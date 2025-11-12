import requests
import datetime

class BinanceUSPrimer:
    def __init__(self, trading_bot=None, symbol="BTCUSDC", interval="1m", limit=60):
        self.trading_bot = trading_bot
        self.symbol = symbol.upper()
        self.interval = interval
        self.limit = limit
        self.url = "https://api.binance.us/api/v3/klines"

    def fetch_and_send(self):
        params = {
            "symbol": self.symbol,
            "interval": self.interval,
            "limit": self.limit
        }

        print(f"📥 Fetching {self.limit} {self.interval} candles for {self.symbol} from Binance.US")
        response = requests.get(self.url, params=params)

        if response.status_code == 200:
            candles = response.json()
            for candle in candles:
                timestamp = datetime.datetime.fromtimestamp(candle[0] / 1000)
                kline_data = {
                    "symbol": self.symbol,
                    "timestamp": timestamp,
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5]),
                }

                if self.trading_bot:
                    self.trading_bot.data_prime(kline_data)
                else:
                    print(f"[{kline_data['timestamp']}] O: {kline_data['open']} H: {kline_data['high']} L: {kline_data['low']} C: {kline_data['close']} V: {kline_data['volume']}")

        else:
            print(f"❌ Failed to fetch data: {response.status_code} - {response.text}")

    def start(self):
        self.fetch_and_send()
