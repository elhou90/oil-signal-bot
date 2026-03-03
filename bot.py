import pandas as pd
import time
from datetime import datetime
import telebot
import os
import requests

# ================== CONFIG ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OILPRICE_API_KEY = os.getenv("OILPRICE_API_KEY")
SENTIMENT_BIAS = os.getenv("SENTIMENT_BIAS", "bullish")

BASE_URL = "https://api.oilpriceapi.com/v1"
COMMODITY_CODE = "WTI_USD"

print("🚀 Bot démarré - Sentiment :", SENTIMENT_BIAS.upper())
print("Clé API :", "présente" if OILPRICE_API_KEY else "MANQUANTE ❌")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

last_price_alert = None

def send_message(message):
    try:
        bot.send_message(CHAT_ID, message)
        print(f"Message envoyé : {message[:80]}...")
    except Exception as e:
        print(f"Erreur Telegram : {e}")

def send_price_alert(price, timestamp):
    global last_price_alert
    if last_price_alert == price:
        return
    last_price_alert = price
    
    msg = f"📊 Prix OIL WTI : **{price:.2f} USD / baril**\n🕒 {timestamp.strftime('%Y-%m-%d %H:%M UTC')}\nSentiment : {SENTIMENT_BIAS.upper()}"
    send_message(msg)

def get_latest_price():
    url = f"{BASE_URL}/prices/latest"
    params = {'by_code': COMMODITY_CODE}
    headers = {
        'Authorization': f'Token {OILPRICE_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    for attempt in range(4):
        try:
            print(f"Tentative {attempt+1}/4 - Appel à {url} avec by_code={COMMODITY_CODE}")
            response = requests.get(url, headers=headers, params=params, timeout=15)
            print(f"Status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Erreur HTTP {response.status_code}: {response.text[:200]}")
                continue
            
            data = response.json()
            print(f"Réponse brute: {data}")
            
            if data.get("status") == "success" and "data" in data:
                price_data = data["data"]
                # Structure directe : data = {price, formatted, ...} (pas de sous-clé WTI_USD)
                price = price_data.get("price")
                if price is not None:
                    ts_str = price_data.get("created_at") or price_data.get("timestamp") or price_data.get("updated_at")
                    timestamp = datetime.fromisoformat(ts_str.replace('Z', '+00:00')) if ts_str else datetime.utcnow()
                    print(f"✅ Prix extrait : {price:.2f} USD")
                    return price, timestamp
                else:
                    print("Pas de 'price' dans data")
            else:
                print("Pas de 'status: success' ou pas de 'data'")
                
        except Exception as e:
            print(f"Exception tentative {attempt+1}: {e}")
        
        time.sleep(2 ** attempt)
    
    print("❌ Échec total après 4 tentatives")
    return None, None

while True:
    try:
        price, timestamp = get_latest_price()
        if price is not None:
            send_price_alert(price, timestamp)
    except Exception as e:
        print(f"Erreur boucle: {e}")
    
    time.sleep(900)  # 15 minutes
