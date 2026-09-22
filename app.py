import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Environment variables from Render configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    """Posts formatted markdown message directly to Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing Telegram configuration keys.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Telegram API Response: {response.status_code}")
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    # Handle JSON payloads or raw text bodies
    data = request.get_json(silent=True)
    raw_text = request.get_data(as_text=True)

    ticker = "XAUUSD"
    action = "ALERT"
    price = "N/A"
    sl = "N/A"
    tp1 = "N/A"
    tp2 = "N/A"

    # 1. Parse structured JSON payload
    if data and isinstance(data, dict):
        ticker = data.get("ticker", "XAUUSD")
        action = data.get("action", "BUY").upper()
        price  = str(data.get("price", "N/A"))
        sl     = str(data.get("sl", "N/A"))
        tp1    = str(data.get("tp1", "N/A"))
        tp2    = str(data.get("tp2", "N/A"))

    # 2. Parse unstructured text (from email relay or plain pop-up messages)
    elif raw_text:
        text_upper = raw_text.upper()
        if "BUY" in text_upper:
            action = "BUY"
        elif "SELL" in text_upper:
            action = "SELL"
        
        # Extract potential numerical values for entry/price using regex
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", raw_text)
        if numbers:
            price = numbers[0]

    emoji = "🟢" if action == "BUY" else ("🔴" if action == "SELL" else "🔔")

    # Format Telegram Signal Card
    message = (
        f"🚨 *LONDON OPEN LIQUIDITY SIGNAL* 🚨\n\n"
        f"{emoji} *Action:* `{action}`\n"
        f"🔤 *Asset:* `{ticker}`\n"
        f"🎯 *Entry:* `{price}`\n"
        f"🛑 *Stop Loss:* `{sl}`\n"
        f"🥇 *TP1 (1:1 RR):* `{tp1}`\n"
        f"🥈 *TP2 (1:2 RR):* `{tp2}`\n\n"
        f"⚠️ *Management:* Partial close 50% at TP1 and move SL to Breakeven."
    )

    send_telegram(message)
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
