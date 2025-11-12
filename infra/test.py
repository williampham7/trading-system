import asyncio
import websockets
import json
import yaml
import time
from datetime import datetime

class AlpacaWebsocketClient:
    def __init__(self):
        self.api_key, self.api_secret = self.get_keys()

        self.stream_url = 'wss://stream.data.alpaca.markets/v1beta3/crypto/us'

        self.tickers = ['BTC/USD']
        self.ws = None

    def get_keys(self):
        config_path = "infra/config.yaml"
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        return config["alpaca"]["key"], config["alpaca"]["secret"]

    async def on_message(self, message):
        """Handles incoming WebSocket messages."""
        print(message)
        data = json.loads(message)
        if isinstance(data, list) and len(data) > 0:
            for trade in data:
                print(trade)

    async def on_error(self, error):
        print(f"WebSocket Error: {error}")

    async def on_close(self, close_status_code, close_msg):
        print("WebSocket closed. Reconnecting in 5 seconds...")

    async def on_open(self):
        """Authenticates and subscribes to trade data."""
        auth_message = {
            "action": "auth",
            "key": self.api_key,
            "secret": self.api_secret
        }
        await self.ws.send(json.dumps(auth_message))
        response = await self.ws.recv()
        print(f"Auth Response: {response}")

        subscribe_message = {
            "action": "subscribe",
            "trades": self.tickers
        }
        await self.ws.send(json.dumps(subscribe_message))
        response = await self.ws.recv()
        print(f"Subscription Response: {response}")

    async def start(self):
        """Starts the WebSocket connection with auto-reconnect."""
        while True:
            try:
                print("Connecting to Alpaca WebSocket...")
                async with websockets.connect(self.stream_url) as websocket:
                    self.ws = websocket
                    await self.on_open()

                    async for message in websocket:
                        await self.on_message(message)

            except websockets.exceptions.ConnectionClosed as e:
                await self.on_error(f"Connection closed: {e}")

            except Exception as e:
                await self.on_error(f"Unexpected error: {e}")

            print("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    bot = AlpacaWebsocketClient()
    async def run_bot():
        await bot.start()

    # Run the async function using asyncio
    asyncio.run(run_bot())
