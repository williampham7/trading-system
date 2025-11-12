import websocket
import json
import datetime
import sqlite3
import time

# Initialize SQLite database
conn = sqlite3.connect('xrp_trades.db')
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        timestamp TEXT,
        price REAL,
        volume REAL
    )
''')
conn.commit()

# WebSocket URL
socket = "wss://ws.kraken.com/"

def on_message(ws, message):
    data = json.loads(message)
    if isinstance(data, list) and len(data) > 1:
        price = 0
        volume = 0.0
        timestamp = datetime.datetime.fromtimestamp(float(data[1][0][2])).strftime('%Y-%m-%d %H:%M:%S')

        for trade in data[1]:
            price = float(trade[0])
            volume += float(trade[1])

        print(f"Price: {price}, Volume: {volume}, Timestamp: {timestamp}\n{trade}")
        cursor.execute("INSERT INTO trades (timestamp, price, volume) VALUES (?, ?, ?)", (timestamp, price, volume))
        conn.commit()

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed. Reconnecting in 5 seconds...")

def on_open(ws):
    payload = {
        "event": "subscribe",
        "pair": ["XRP/USD"],
        "subscription": {"name": "trade"}
    }
    ws.send(json.dumps(payload))

def start_websocket():
    """Keeps trying to reconnect to WebSocket on failure."""
    while True:
        try:
            print("Connecting to WebSocket...")
            ws = websocket.WebSocketApp(socket, 
                                        on_message=on_message, 
                                        on_error=on_error, 
                                        on_close=on_close)
            ws.on_open = on_open
            ws.run_forever()
        except Exception as e:
            print(f"WebSocket error: {e}")
        
        print("Reconnecting in 5 seconds...")
        time.sleep(5)  # Delay before attempting to reconnect

# Start the WebSocket connection with auto-reconnect
start_websocket()
