import yaml
import smtplib
from datetime import datetime

# Load YAML file
with open("infra/config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Extract credentials
sender_email = config["email"]["address"]
password = config["email"]["password"]
recipient_sms = config["email"]["recipient_sms"]

def connected_message():
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"Live price stream connected at {time}"
    send_message(message)

def disconnected_message():
    message = f"Live price stream has been disconnected."
    send_message(message)

def buy_order_success(asset, qty, trade_price, timestamp):
    message = f"BUY {qty} {asset} @ {trade_price} | {timestamp}"
    send_message(message)

def buy_order_fail(asset, reason):
    message = f"FAILED BUY {asset}. {reason}"
    send_message(message)

def sell_order_success(asset, qty, trade_price, timestamp):
    message = f"SELL {qty} {asset} @ {trade_price} | {timestamp}"
    send_message(message)

def sell_order_fail(asset, reason):
    message = f"FAILED SELL {asset}. {reason}"
    send_message(message)



def send_message(message):
    subject = "Trading Bot"
    email_body = f"Subject: {subject}\n\n{message}"  # Proper email format

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, sender_email, email_body)