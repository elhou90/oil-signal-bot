import time
from datetime import datetime, timezone
import telebot
import os
import requests
import feedparser

# ================== CONFIG ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OILPRICE_API_KEY = os.getenv("OILPRICE_API_KEY")
SENTIMENT_BIAS = os.getenv("SENTIMENT_BIAS", "bullish")

COMMODITY_CODE = "WTI_USD"

# TES NIVEAUX BUY LIMIT (modifie ici si tu veux)
BUY_LEVELS = {
    76.20: {"sl": 75.60, "tp": 79.50, "lot": 0.02},
    75.50: {"sl": 74.80, "tp": 79.50, "lot": 0.02},
    74.80: {"sl": 74.00, "tp": 79.50, "lot": 0.01},
    73.80: {"sl": 73.00, "tp": 79.50, "lot": 0.01}
}

print("🚀 Bot démarré - Debug prix activé")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

RSS_FEEDS = [
    "https://oilprice.com/rss/main",
    "https://www.investing.com/rss/news_11.rss"
]

def send_message(message):
    try:
        bot.send_message(CHAT_ID, message)
    except Exception as e:
        print(f"Erreur Telegram : {e}")

def get_price():
    """Version avec debug complet"""
    url = "https://api.oilpriceapi.com/v1/prices/latest"
    params = {'by_code': COMMODITY_CODE}
    headers = {'Authorization': f'Token {OILPRICE_API_KEY}'}
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Status code: {r.status_code}")
        print(f"Réponse brute: {r.text[:400]}")   # ← tu verras exactement ce que renvoie l’API
        
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success" and "data" in data:
                price = data["data"]["price"]
                print(f"✅ Prix extrait : {price:.2f}")
                return price
            else:
                print("❌ Format inattendu")
        else:
            print(f"❌ Erreur HTTP {r.status_code}")
    except Exception as e:
        print(f"❌ Exception prix : {e}")
    
    print("⚠️ Prix non récupéré → fallback à 0")
    return None

# (le reste du code est identique : check_buy_alert, get_rss_news, get_prediction, boucle while)

def check_buy_alert(price):
    for level, data in BUY_LEVELS.items():
        if abs(price - level) <= 0.25:
            risk = round((level - data["sl"]) * data["lot"] * 100, 2)
            return (f"🚨 **ALERTE BUY LIMIT** 🚨\n"
                    f"Prix actuel : **{price:.2f} USD**\n"
                    f"✅ Niveau touché : **{level}**\n"
                    f"Lot recommandé : {data['lot']}\n"
                    f"Stop Loss : **{data['sl']}** (-{risk}$ risque)\n"
                    f"Take Profit : **{data['tp']}**\n\n"
                    f"Place ton Buy Limit maintenant !")
    return None

def get_rss_news():
    news_text = "📰 Dernières news WTI / Oil (RSS) :\n\n"
    count = 0
    keywords = ["wti", "crude oil", "oil price", "hormuz", "hormoz", "iran", "installation", "bombard", "attaque", "tankers"]
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:8]:
            if any(k in entry.title.lower() for k in keywords):
                news_text += f"• {entry.title}\n   {entry.link}\n\n"
                count += 1
                if count >= 5: return news_text
    return news_text if count > 0 else "📰 Aucune news majeure pour l’instant"

def get_prediction():
    if SENTIMENT_BIAS.lower() == "bullish":
        return "🔥 GROK PREDICTION : HAUSSE FORTE\n✅ RECOMMANDATION : ACHAT (Buy WTI)"
    elif SENTIMENT_BIAS.lower() == "bearish":
        return "📉 GROK PREDICTION : CHUTE\n❌ RECOMMANDATION : VENTE (Sell WTI)"
    else:
        return "⚖️ GROK PREDICTION : NEUTRE"

while True:
    try:
        price = get_price()
        
        if price:
            send_message(f"📊 Prix OIL WTI : **{price:.2f} USD / baril**\n🕒 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
            alert = check_buy_alert(price)
            if alert:
                send_message(alert)
        
        send_message(get_rss_news())
        send_message(get_prediction())

    except Exception as e:
        print(f"Erreur globale : {e}")

    time.sleep(900)
