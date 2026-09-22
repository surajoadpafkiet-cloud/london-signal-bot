import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Reads your keys safely from Render's settings
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON payload"}), 400

    ticker = data.get("ticker", "XAUUSD")
    action = data.get("action", "BUY")
    price  = float(data.get("price", 0.0))
    sl     = float(data.get("sl", 0.0))
    tp1    = float(data.get("tp1", 0.0))
    tp2    = float(data.get("tp2", 0.0))

    emoji = "🟢" if action == "BUY" else "🔴"

    message = (
        f"🚨 *LONDON OPEN LIQUIDITY SIGNAL* 🚨\n\n"
        f"{emoji} *Action:* `{action}`\n"
        f"🔤 *Asset:* {ticker}\n"
        f"🎯 *Entry:* `{price:.2f}`\n"
        f"🛑 *Stop Loss:* `{sl:.2f}`\n"
        f"🥇 *TP1 (1:1 RR):* `{tp1:.2f}`\n"
        f"🥈 *TP2 (1:2 RR):* `{tp2:.2f}`\n\n"
        f"⚠️ *Management:* Partial close 50% at TP1 and move SL to Breakeven."
    )

    send_telegram(message)
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)