import pandas as pd
import time
from datetime import datetime
import telebot
import os
import requests

# ================== CONFIG (sur Railway Variables) ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OILPRICE_API_KEY = os.getenv("OILPRICE_API_KEY")          # ← TA CLÉ OILPRICEAPI ICI !
SENTIMENT_BIAS = os.getenv("SENTIMENT_BIAS", "bullish")

BASE_URL = "https://api.oilpriceapi.com/v1"
COMMODITY_CODE = "WTI_USD"   # WTI Crude Oil en USD (change en BRENT_CRUDE_USD si tu veux Brent)

print("🚀 Bot OIL WTI (OilPriceAPI) démarré - Sentiment :", SENTIMENT_BIAS.upper())
print("API Key présent :", "OUI" if OILPRICE_API_KEY else "NON ❌")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

last_signal = None
last_bar_time = None
last_price_alert = None

def send_message(message):
    try:
        bot.send_message(CHAT_ID, message)
        print(f"✅ Message envoyé : {message[:80]}...")
    except Exception as e:
        print(f"❌ Erreur Telegram : {e}")

def send_price_alert(price, timestamp):
    global last_price_alert
    if last_price_alert == price:
        return
    last_price_alert = price
    
    msg = (
        f"📊 Prix actuel OIL WTI : **{price:.2f} USD / baril**\n"
        f"🕒 {timestamp.strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"Sentiment actuel : {SENTIMENT_BIAS.upper()}"
    )
    send_message(msg)

def get_latest_price():
    """Récupère le prix actuel via OilPriceAPI avec retry"""
    url = f"{BASE_URL}/prices/latest?by_code={COMMODITY_CODE}"
    headers = {
        "Authorization": f"Token {OILPRICE_API_KEY}"
    }
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "success" and "data" in data and COMMODITY_CODE in data["data"]:
                price_data = data["data"][COMMODITY_CODE]
                price = price_data.get("price")
                timestamp_str = price_data.get("timestamp")
                if price is not None:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')) if timestamp_str else datetime.utcnow()
                    print(f"✅ Prix récupéré : {price:.2f} USD à {timestamp}")
                    return price, timestamp
            else:
                print(f"Réponse inattendue : {data}")
        except Exception as e:
            print(f"Tentative {attempt+1}/3 échouée : {str(e)[:100]}")
            time.sleep(10)
    
    print("❌ Échec récupération prix après 3 essais")
    return None, None

# Boucle principale (toutes les 15 min)
while True:
    try:
        price, timestamp = get_latest_price()
        if price is not None:
            send_price_alert(price, timestamp)
            
            # Ici tu peux ajouter la logique SMA/RSI si tu veux (mais il faut des données historiques)
            # OilPriceAPI a /v1/prices/historical pour ça, mais pour l'instant on garde simple
            # Si tu veux full stratégie, dis-moi et on ajoute historical + pandas rolling
    except Exception as e:
        print("Erreur boucle :", e)
    
    time.sleep(900)  # 15 minutes
