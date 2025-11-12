import alpaca_trade_api as tradeapi
import yaml
import comms
from datetime import datetime
import pytz

class AlpacaTrader:
    def __init__(self, config_path="infra/config.yaml"):
        """Initialize Alpaca API with credentials from a config file."""
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        self.api_key = config["alpaca"]["key"]
        self.api_secret = config["alpaca"]["secret"]
        self.base_url = "https://paper-api.alpaca.markets"  # Paper trading endpoint

        # Initialize Alpaca API
        self.api = tradeapi.REST(self.api_key, self.api_secret, self.base_url, api_version="v2")

    def get_cash_balance(self):
        """Fetch account balance in USD."""
        account = self.api.get_account()
        cash_balance = float(account.cash)
        print(f"Available USD balance: {cash_balance}")
        return cash_balance

    def place_buy_order(self, symbol, cash_qty, order_type="market", time_in_force="gtc"):
        """Places a market buy order for the given symbol using a dollar amount."""
        try:
            # Get the latest market price
            barset = self.api.get_latest_trade(symbol)
            current_price = float(barset.price)

            qty = round(cash_qty / current_price, 6)  # Adjust precision for stock/crypto

            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                type=order_type,
                time_in_force=time_in_force
            )

            timestamp_str = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %I:%M:%S %p PDT')
            print(f"✅ Buy order placed successfully at ~{current_price} for {qty} {symbol} @ {timestamp_str}")
            comms.buy_order_success(symbol, qty, current_price, timestamp_str)

        except Exception as e:
            reason = f"Error placing buy order: {e}"
            print(reason)
            comms.buy_order_fail(symbol, reason)

    def place_sell_order(self, symbol):
        """Places a market sell order for the full position of the given symbol."""
        try:
            position = self.api.get_position(symbol)
            qty = float(position.qty)

            if qty > 0:
                order = self.api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side="sell",
                    type="market",
                    time_in_force="gtc"
                )

                current_price = float(position.current_price)
                timestamp_str = datetime.now(pytz.timezone('America/Los_Angeles')).strftime('%Y-%m-%d %I:%M:%S %p PDT')
                print(f"✅ Sell order placed successfully at ~{current_price} for {qty} {symbol} @ {timestamp_str}")
                comms.sell_order_success(symbol, qty, current_price, timestamp_str)
            else:
                reason = f"No {symbol} position found. Holding 0 {symbol}."
                print(reason)
                comms.sell_order_fail(symbol, reason)

        except Exception as e:
            if "position does not exist" in str(e):
                reason = f"No {symbol} position found. Holding 0 {symbol}."
            else:
                reason = f"Error placing sell order: {e}"
            print(reason)
            comms.sell_order_fail(symbol, reason)

if __name__ == "__main__":
    trader = AlpacaTrader()
    trader.place_sell_order('BTCUSDC')