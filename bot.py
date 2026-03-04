import time
from datetime import datetime, timedelta, timezone
import telebot
import os
import requests
import feedparser   # ← NOUVEAU pour les RSS

# ================== CONFIG ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OILPRICE_API_KEY = os.getenv("OILPRICE_API_KEY")
SENTIMENT_BIAS = os.getenv("SENTIMENT_BIAS", "bullish")

COMMODITY_CODE = "WTI_USD"

print("🚀 Bot WTI + RSS (Investing + OilPrice) démarré - Sentiment Grok :", SENTIMENT_BIAS.upper())

bot = telebot.TeleBot(TELEGRAM_TOKEN)

RSS_FEEDS = [
    "https://oilprice.com/rss/main",                    # Meilleur pour géopolitique pétrole
    "https://www.investing.com/rss/news_11.rss"         # Commodities / WTI
]

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
                return data["data"]["price"]
    except:
        pass
    return None

def get_rss_news():
    news_text = "📰 Dernières news WTI / Oil (RSS) :\n\n"
    count = 0
    keywords = ["wti", "crude oil", "oil price", "hormuz", "hormoz", "iran", "installation", "bombard", "attaque", "tankers", "strike"]
    
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:6]:  # 6 articles max par flux
            title = entry.title.lower()
            if any(k in title for k in keywords):
                news_text += f"• {entry.title}\n   {entry.link}\n\n"
                count += 1
                if count >= 5:  # max 5 news au total
                    return news_text
    return news_text if count > 0 else "📰 Aucune news majeure sur WTI/Hormuz pour l’instant"

def get_prediction():
    if SENTIMENT_BIAS.lower() == "bullish":
        return "🔥 GROK PREDICTION : HAUSSE FORTE\n✅ RECOMMANDATION : ACHAT (Buy WTI)"
    elif SENTIMENT_BIAS.lower() == "bearish":
        return "📉 GROK PREDICTION : CHUTE\n❌ RECOMMANDATION : VENTE (Sell WTI)"
    else:
        return "⚖️ GROK PREDICTION : NEUTRE\n🔄 Attendre signal"

while True:
    try:
        # Prix
        price = get_price()
        if price:
            send_message(f"📊 Prix OIL WTI : **{price:.2f} USD / baril**\n🕒 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

        # News RSS (Investing + OilPrice)
        news = get_rss_news()
        send_message(news)

        # Prédiction Grok
        pred = get_prediction()
        send_message(pred)

        print("✅ Cycle terminé (prix + RSS news + prédiction)")

    except Exception as e:
        print(f"Erreur : {e}")

    time.sleep(900)  # Toutes les 15 minutes
