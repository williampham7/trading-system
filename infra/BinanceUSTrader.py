import ccxt
import yaml, pytz
import comms
from datetime import datetime, timezone

class BinanceUSTrader:
    def __init__(self, config_path="infra/config.yaml"):
        """Initialize Binance.US API with credentials from a config file."""
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        self.api_key = config["binance_us"]["key"]
        self.api_secret = config["binance_us"]["secret"]

        # Initialize Binance.US API
        self.exchange = ccxt.binanceus({
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True
        })

    def get_balance(self):
        """Fetch account balance for USDC."""
        balance = self.exchange.fetch_balance()
        usdc_balance = balance['total'].get('USDC', 0)
        print(f"Available USDC balance: {usdc_balance}")
        return usdc_balance

    def place_buy_order(self, symbol, usdc_amt = 10, order_type="market"):
        """Places a market buy order for the given symbol using a specified USDC amount."""

        ticker = self.exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        qty = round(usdc_amt / current_price, 8)  # precision depends on the exchange

        try:
            # Place the buy order
            order = self.exchange.create_market_order(symbol=symbol, side="buy", amount=qty)

            order_id = order['id']
            trade_price = order['price']
            timestamp_str = datetime.fromtimestamp(int(order['info']['transactTime']) / 1000, tz=timezone.utc) \
                    .astimezone(pytz.timezone('America/Los_Angeles')) \
                    .strftime('%Y-%m-%d %I:%M:%S %p PDT')
            comms.buy_order_success(symbol, qty, trade_price, timestamp_str)
            print(f"✅ Buy order {order_id} placed successfully at {trade_price} @ {timestamp_str}")
        except Exception as e:
            reason = f"Error placing buy order: {e}"
            print(reason)
            comms.buy_order_fail(symbol, reason)

    def place_sell_order(self, symbol):
        """Places a market sell order for the full position of the given symbol."""
        try:
            balance = self.exchange.fetch_balance()
            asset = symbol.split("/")[0]  # Extracts base asset (e.g., BTC from BTC/USDC)
            qty = balance['total'].get(asset, 0)

            if qty > 0:
                order = self.exchange.create_market_order(symbol=symbol, side="sell", amount=qty)

                order_id = order['id']
                trade_price = order['price']
                timestamp_str = datetime.fromtimestamp(int(order['info']['transactTime']) / 1000, tz=timezone.utc) \
                    .astimezone(pytz.timezone('America/Los_Angeles')) \
                    .strftime('%Y-%m-%d %I:%M:%S %p PDT')
                comms.sell_order_success(symbol, qty, trade_price, timestamp_str)
                print(f"✅ Sell order {order_id} placed successfully at {trade_price} @ {timestamp_str}")
            else:
                reason = f"No {symbol} position found. Holding 0 {asset}."
                print(reason)
                comms.sell_order_fail(symbol, reason)

        except Exception as e:
            reason = f"Error placing sell order: {e}"
            print(reason)
            comms.sell_order_fail(symbol, reason)

# if __name__ == "__main__":
#     trader = BinanceUSTrader()
#     trader.place_sell_order('BTC/USDC')