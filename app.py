import os
import re
import requests
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Environment Variables from Render
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY")

# Initialize Gemini Client
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def analyze_trade_with_gemini(ticker, action, price, sl, tp1, tp2):
    """Uses Gemini to generate a concise technical analysis breakdown for the signal."""
    if not ai_client:
        return "⚠️ *Gemini Analysis:* API Key missing. Skipping AI commentary."

    prompt = f"""
    You are an expert institutional trader specializing in London Open Liquidity Sweeps and Opening Range Breakouts.
    A automated trading signal just fired with the following parameters:
    - Asset: {ticker}
    - Action: {action}
    - Entry Price: {price}
    - Stop Loss: {sl}
    - Take Profit 1: {tp1}
    - Take Profit 2: {tp2}

    Provide a concise 3-bullet-point technical commentary for this trade setup:
    1. Key liquidity pool targeted or swept.
    2. Expected price delivery behavior during the London session.
    3. Essential execution or trade-management warning.

    Keep your response under 120 words total, formatted nicely in Telegram Markdown.
    """

    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return "⚠️ *Gemini Analysis:* Unable to generate AI commentary."

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
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram API Response: {response.status_code}")
    except Exception as e:
        print(f"Error sending message to Telegram: {e}")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(silent=True)
    raw_text = request.get_data(as_text=True)

    ticker = "XAUUSD"
    action = "ALERT"
    price = "N/A"
    sl = "N/A"
    tp1 = "N/A"
    tp2 = "N/A"

    # 1. Parse Structured JSON
    if data and isinstance(data, dict):
        ticker = data.get("ticker", "XAUUSD")
        action = data.get("action", "BUY").upper()
        price  = str(data.get("price", "N/A"))
        sl     = str(data.get("sl", "N/A"))
        tp1    = str(data.get("tp1", "N/A"))
        tp2    = str(data.get("tp2", "N/A"))

    # 2. Parse Raw Email / Text
    elif raw_text:
        text_upper = raw_text.upper()
        if "BUY" in text_upper:
            action = "BUY"
        elif "SELL" in text_upper:
            action = "SELL"
        
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", raw_text)
        if numbers:
            price = numbers[0]

    emoji = "🟢" if action == "BUY" else ("🔴" if action == "SELL" else "🔔")

    # Call Gemini for AI Market Analysis
    gemini_analysis = analyze_trade_with_gemini(ticker, action, price, sl, tp1, tp2)

    # Format Telegram Message Card
    message = (
        f"🚨 *LONDON OPEN LIQUIDITY SIGNAL* 🚨\n\n"
        f"{emoji} *Action:* `{action}`\n"
        f"🔤 *Asset:* `{ticker}`\n"
        f"🎯 *Entry:* `{price}`\n"
        f"🛑 *Stop Loss:* `{sl}`\n"
        f"🥇 *TP1 (1:1 RR):* `{tp1}`\n"
        f"🥈 *TP2 (1:2 RR):* `{tp2}`\n\n"
        f"----------------------------------\n"
        f"🧠 *GEMINI AI TRADE ANALYSIS*\n"
        f"{gemini_analysis}\n"
        f"----------------------------------\n"
        f"⚠️ *Management:* Partial close 50% at TP1 and move SL to Breakeven."
    )

    send_telegram(message)
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
