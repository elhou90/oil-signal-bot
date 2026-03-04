import time
from datetime import datetime, timedelta   # ← CORRIGÉ ici !
import telebot
import os
import requests

# ================== CONFIG (Railway Variables) ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OILPRICE_API_KEY = os.getenv("OILPRICE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
SENTIMENT_BIAS = os.getenv("SENTIMENT_BIAS", "bullish")

COMMODITY_CODE = "WTI_USD"

print("🚀 Bot WTI + DEUX sources news démarré - Sentiment Grok :", SENTIMENT_BIAS.upper())

bot = telebot.TeleBot(TELEGRAM_TOKEN)

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

def get_news_newsapi():
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": '(WTI OR "crude oil" OR "oil price" OR Hormuz OR "Strait of Hormuz" OR "Iran oil" OR "oil installation")',
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": 5,
        "from": yesterday,
        "apiKey": NEWS_API_KEY
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            if not articles:
                return ""
            text = "📰 NewsAPI.org :\n"
            for art in articles[:2]:
                text += f"• {art['title']}\n   {art['url']}\n\n"
            return text
    except:
        return ""

def get_news_newsdata():
    url = "https://newsdata.io/api/1/market"
    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": "WTI, oil, hormoz, hormuz, iran oil, oil installation",
        "language": "fr,en,ar",
        "timezone": "africa/algiers",
        "removeduplicate": "1",
        "size": 10
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if not results:
                return ""
            text = "📰 NewsData.io :\n"
            count = 0
            for art in results:
                title = art.get("title", "")
                link = art.get("link", "")
                if any(word in title.lower() for word in ["wti", "oil", "hormoz", "hormuz", "iran", "installation", "bombard", "attaque"]):
                    text += f"• {title}\n   {link}\n\n"
                    count += 1
                    if count >= 3:
                        break
            return text
    except:
        return ""

def get_prediction():
    if SENTIMENT_BIAS.lower() == "bullish":
        return "🔥 GROK PREDICTION : HAUSSE FORTE\n✅ RECOMMANDATION : ACHAT (Buy WTI)"
    elif SENTIMENT_BIAS.lower() == "bearish":
        return "📉 GROK PREDICTION : CHUTE\n❌ RECOMMANDATION : VENTE (Sell WTI)"
    else:
        return "⚖️ GROK PREDICTION : NEUTRE\n🔄 Attendre signal"

while True:
    try:
        price = get_price()
        if price:
            send_message(f"📊 Prix OIL WTI : **{price:.2f} USD / baril**\n🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

        news1 = get_news_newsapi()
        news2 = get_news_newsdata()
        combined_news = "📰 Dernières infos WTI / Géopolitique :\n\n" + news1 + news2
        if len(combined_news) > 60:
            send_message(combined_news)
        else:
            send_message("📰 Aucune info majeure sur WTI/Hormuz ces dernières heures")

        pred = get_prediction()
        send_message(pred)

        print("✅ Cycle terminé (prix + 2 sources news + prédiction)")

    except Exception as e:
        print(f"Erreur : {e}")

    time.sleep(900)
