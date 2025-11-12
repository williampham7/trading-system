import asyncio
import websockets
import json
import datetime

class BinanceUSWebsocketClient:
    def __init__(self, trading_bot=None, symbol="btcusdc", interval="1m"):
        self.url = f"wss://stream.binance.us:9443/ws/{symbol.lower()}@kline_{interval}"
        self.trading_bot = trading_bot
        self.symbol = symbol.upper()

    async def handle_message(self, message):
        kline = message['k']
        timestamp = datetime.datetime.fromtimestamp(kline['t'] / 1000)
        kline_data = {
            "symbol": self.symbol,
            "timestamp": timestamp,
            "open": float(kline['o']),
            "high": float(kline['h']),
            "low": float(kline['l']),
            "close": float(kline['c']),
            "volume": float(kline['v']),
        }

        if self.trading_bot:
            self.trading_bot.on_new_data(kline_data)
        else:
            print(f"[{kline_data['timestamp']}] Open: {kline_data['open']} | High: {kline_data['high']} | Low: {kline_data['low']} | Close: {kline_data['close']} | Volume: {kline_data['volume']}")

    async def connect(self):
        print(f"🔌 Connecting to Binance.US WebSocket for {self.symbol} ({self.url})")
        while True:
            try:
                async with websockets.connect(self.url) as ws:
                    print("✅ Connected")
                    async for message in ws:
                        data = json.loads(message)
                        await self.handle_message(data)

            except Exception as e:
                print(f"❌ Connection error: {e}")
                print("🔄 Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def start(self):
        await self.connect()