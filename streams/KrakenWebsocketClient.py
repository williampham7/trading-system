import websocket
import json
import datetime
import time

class KrakenWebsocketClient:
    def __init__(self, trading_bot):
        self.socket_url = "wss://ws.kraken.com/"
        self.ws = None
        self.trading_bot = trading_bot  # Reference to TradingBot instance
        self.asset_list = trading_bot.asset_list

    def on_message(self, ws, message):
        """Handles incoming WebSocket messages."""
        data = json.loads(message)
        if isinstance(data, list) and len(data) > 1:
            price = 0
            volume = 0.0
            timestamp = datetime.datetime.fromtimestamp(float(data[1][0][2]))

            for trade in data[1]:
                price = float(trade[0])
                volume += float(trade[1])

            self.trading_bot.on_new_data((timestamp, price, volume))  # Send data to bot

    def on_error(self, ws, error):
        print(f"WebSocket Error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket closed. Reconnecting in 5 seconds...")

    def on_open(self, ws):
        payload = {
            "event": "subscribe",
            "pair": self.asset_list,
            "subscription": {"name": "trade"}
        }
        ws.send(json.dumps(payload))

    def start(self):
        while True:
            try:
                print("Connecting to WebSocket...")
                self.ws = websocket.WebSocketApp(
                    self.socket_url, 
                    on_message=self.on_message, 
                    on_error=self.on_error, 
                    on_close=self.on_close
                )
                self.ws.on_open = self.on_open
                #connected_message()
                self.ws.run_forever()

            except Exception as e:
                error = e

            #disconnected_message()
            print("Reconnecting in 5 seconds...")
            time.sleep(1)  # Delay before reconnecting
