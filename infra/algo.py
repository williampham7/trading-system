import comms, indicators, BinanceUSWebsocketClient, BinanceUSPrimer, BinanceUSTrader
import collections, yaml, sqlite3, asyncio, ctypes, traceback
from datetime import datetime, timedelta
import numpy as np

# Signal condition:
# DI+ over 50 and RSI over 50


#KEPT BUYING


class TradingBot:
    def __init__(self):
        #main deque
        self.price_deque = collections.deque()  # Store (timestamp, price, volume) tuples

        #alpacatrader
        self.trader = BinanceUSTrader.BinanceUSTrader()
        self.data_primer = BinanceUSPrimer.BinanceUSPrimer(self)
        self.data_stream = BinanceUSWebsocketClient.BinanceUSWebsocketClient(self)

        with open("infra/config.yaml", "r") as file:
            config = yaml.safe_load(file)

        # Extract config
        self.asset = config["trading_config"]["asset"]
        self.usdc_amt = config["trading_config"]["usdc_amt"]
        self.bollinger_std_width = config["trading_config"]["bollinger_std_width"]
        self.sell_std = config["trading_config"]["sell_std"]
        self.loss_threshold = config["trading_config"]["loss_threshold"]

        self.active_position = False  # Whether a position is currently open
        self.trading_enabled = False
        self.buy_price = 0.0
        self.cache_timestamp = ''
        self.cache_price = 0.0
        self.cache_volume = 0.0
        self.cache_mean = 0.0
        self.cache_std = 0.0
        self.cache_buy_line = 0.0
        self.cache_sell_line = 0.0
        self.cache_rsi = 0.0
        self.cache_di_plus = 0.0
        self.cache_di_minus = 0.0
        self.cache_macd = 0.0
        self.start_time = datetime.now()

    async def start(self):
        self.start_database()
        self.prevent_sleep()
        self.data_primer.start()
        await self.data_stream.start()  # probably runs sync code that feeds into on_new_data()

    def data_prime(self, data_point):
        self.update_deque(data_point)

    def on_new_data(self, data_point):
        ''' Handles incoming new data. If in a trade, check exit conditions. If not in a trade, update the deque and check entry conditions. '''
        self.update_deque(data_point)

        if not self.active_position:
            self.check_entry_conditions()
        else:
            self.check_exit_conditions()

    def update_deque(self, data_point):
        try:
            """Removes old data points (older than 60 minutes) and adds the new one."""
            cutoff_time = datetime.now() - timedelta(minutes=60)
            while self.price_deque and self.price_deque[0]["timestamp"] < cutoff_time:
                self.price_deque.popleft()  # Remove outdated entries

            # Replace the last entry if it's from the same minute
            if self.price_deque and self.price_deque[-1]["timestamp"] == data_point["timestamp"]:
                self.price_deque[-1] = data_point
            else:
                self.price_deque.append(data_point)

            self.cache_timestamp = self.price_deque[-1]["timestamp"].isoformat()
            self.cache_price = self.price_deque[-1]["close"]
            self.cache_volume = self.price_deque[-1]["volume"]
            self.cache_mean, self.std, self.cache_buy_line, self.cache_sell_line, self.cache_rsi, self.cache_di_plus, self.cache_di_minus, self.cache_macd = self.get_indicators()
            self.price_deque[-1]["buy_line"] = self.cache_buy_line
            self.price_deque[-1]["sell_line"] = self.cache_sell_line

            self.save_trade_data(0, 0, 0.0)

            print(f"Time: {self.price_deque[-1]['timestamp']}, Position: {self.active_position}, Price: {self.price_deque[-1]['close']}, Buy Line: {self.price_deque[-1]['buy_line']}, Sell Line: {self.price_deque[-1]['sell_line']}")

        except Exception as e:
            print(traceback.format_exc())


    #check conditions

    def check_entry_conditions(self):
        '''checks buy conditions and if all met, calls trade execute function'''
        mean, std, buy_line, sell_line, rsi, di_plus, di_minus, macd = self.get_indicators()

        if (self.cache_price < self.cache_buy_line):
            self.execute_buy_order()
            self.active_position = True
            self.cache_price = self.cache_price


    def check_exit_conditions(self):
        '''when active_position is true, checks if sell conditions are met. if so, calls sell_order function'''
        mean, std, buy_line, sell_line, rsi, di_plus, di_minus, macd = self.get_indicators()

        if (self.cache_price > self.cache_sell_line): #hold condition no longer met
            self.execute_sell_order()
            self.active_position = False
        elif self.cache_price < self.loss_threshold * self.buy_price: # drops more than x%
            self.execute_sell_order()
            self.active_position = False

    #alpaca connectivity

    def execute_buy_order(self):
        '''connects to alpaca api to execute buy order'''
        self.trader.place_buy_order(self.asset)
        self.save_trade_data(1, 0, -1)

    def execute_sell_order(self):
        '''connects to alpaca api to execute sell order'''
        self.trader.place_sell_order(self.asset)
        self.save_trade_data(0, 1, -1)

    # retrieve indicators

    def get_indicators(self):
        prices = np.array([entry["close"] for entry in self.price_deque])  # Extract price values
        mean = np.mean(prices)
        std = np.std(prices, ddof=1)

        buy_line = mean - std * self.bollinger_std_width
        sell_line = mean + std * self.sell_std

        period = 14

        rsi = indicators.rsi(prices, period)
        di_plus = indicators.di_plus(prices)
        di_minus = indicators.di_minus(prices)
        macd = indicators.macd(prices, period)

        return mean, std, buy_line, sell_line, rsi, di_plus, di_minus, macd
    
    #data storage
    def start_database(self):
        self.conn = sqlite3.connect("btc_MR_trades.db")  # Connect to the database
        self.cursor = self.conn.cursor()

        # Create table if it doesn't exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                asset TEXT,
                buy INTEGER,
                sell INTEGER,
                position INTEGER,
                quantity REAL,
                price REAL,
                volume REAL,
                mean REAL,
                std REAL,
                buy_line REAL,
                sell_line REAL,
                rsi REAL,
                di_plus REAL,
                di_minus REAL,
                macd REAL
            )
        """)

        self.conn.commit()

    def save_trade_data(self, buy, sell, quantity):
        """Saves the latest trade data into the SQLite database."""
        if not self.price_deque:
            print("No trade data available to save.")
            return

        try:
            self.cursor.execute("""
                INSERT INTO trades (timestamp, asset, buy, sell, position, quantity, price, volume, mean, std, buy_line, sell_line, rsi, di_plus, di_minus, macd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.cache_timestamp, self.asset, buy, sell, self.active_position, quantity, self.cache_price, self.cache_volume, self.cache_mean, self.std, self.cache_buy_line, self.cache_sell_line, self.cache_rsi, self.cache_di_plus, self.cache_di_minus, self.cache_macd))

            self.conn.commit()

        except Exception as e:
            print(f"Error saving trade data: {e}")

    def prevent_sleep(self):
        """Prevent the system from sleeping while the bot is running (Windows)."""
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

async def main():
    bot = TradingBot()
    await bot.start()

asyncio.run(main())
