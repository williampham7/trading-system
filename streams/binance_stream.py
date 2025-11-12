import asyncio
import websockets
import json

url = "wss://stream.binance.us:9443/ws/btcusdc@kline_1m"

async def binance_us_trade_stream():    
    async with websockets.connect(url) as ws:
        print("🔌 Connected to Binance.US WebSocket (1m bars)")
        while True:
            data = await ws.recv()
            message = json.loads(data)
            
            kline = message['k']
            print(f"[{kline['t']}] Open: {kline['o']} | High: {kline['h']} | Low: {kline['l']} | Close: {kline['c']} | Volume: {kline['v']}")

# Run the async function
asyncio.run(binance_us_trade_stream())
