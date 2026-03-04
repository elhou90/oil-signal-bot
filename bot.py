import time
from datetime import datetime
import telebot
import os
import requests

# ================== CONFIG (Railway Variables) ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OILPRICE_API_KEY = os.getenv("OILPRICE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")                    # ← NOUVELLE CLÉ !
SENTIMENT_BIAS = os.getenv("SENTIMENT_BIAS", "bullish")    # Je te dis chaque jour quoi mettre

COMMODITY_CODE = "WTI_USD"

print("🚀 Bot WTI complet démarré - Sentiment Grok :", SENTIMENT_BIAS.upper())

bot = telebot.TeleBot(TELEGRAM_TOKEN)

last_price = None

def send_message(message):
    try:
        bot.send_message(CHAT_ID, message)
        print("✅ Message envoyé")
    except Exception as e:
        print(f"Erreur Telegram : {e}")

def get_price():
    url = "https://api.oilpriceapi.com/v1/prices/latest"
    params = {'by_code': COMMODITY_CODE}
    headers = {'Authorization': f'Token {OILPRICE_API_KEY}'}
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success":
                price = data["data"]["price"]
                return price
    except:
        pass
    return None

def get_news():
    url = f"https://newsapi.org/v2/everything"
    params = {
        "q": "WTI OR 'crude oil' OR 'oil price' OR 'Strait of Hormuz' OR Hormuz OR 'Iran oil' OR 'oil installation' OR bombing OR attack",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 3,
        "apiKey": NEWS_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            articles = r.json()["articles"]
            news_text = "📰 Dernières infos WTI / Géopolitique :\n\n"
            for art in articles[:2]:
                news_text += f"• {art['title']}\n   {art['url']}\n\n"
            return news_text
    except:
        return "📰 Impossible de récupérer les news pour l'instant"

def get_prediction():
    bias = SENTIMENT_BIAS.lower()
    if bias == "bullish":
        return "🔥 GROK PREDICTION : HAUSSE FORTE\n✅ RECOMMANDATION : ACHAT (Buy WTI)"
    elif bias == "bearish":
        return "📉 GROK PREDICTION : CHUTE\n❌ RECOMMANDATION : VENTE (Sell WTI)"
    else:
        return "⚖️ GROK PREDICTION : NEUTRE\n🔄 Attendre confirmation"

while True:
    try:
        price = get_price()
        if price:
            price_msg = f"📊 Prix OIL WTI : **{price:.2f} USD / baril**\n🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
            send_message(price_msg)
        
        news = get_news()
        send_message(news)
        
        pred = get_prediction()
        send_message(pred)
        
        print(f"Cycle terminé - Prix : {price} - Sentiment : {SENTIMENT_BIAS}")
        
    except Exception as e:
        print(f"Erreur : {e}")
    
    time.sleep(900)  # 15 minutes
