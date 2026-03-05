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

# 🔥 TES NIVEAUX BUY LIMIT (tu peux les modifier)
BUY_LEVELS = [76.20, 75.50, 74.80, 73.80]

print("🚀 Bot WTI + ALERTES Buy Limit démarré - Sentiment :", SENTIMENT_BIAS.upper())

bot = telebot.TeleBot(TELEGRAM_TOKEN)

RSS_FEEDS = [
    "https://oilprice.com/rss/main",
    "https://www.investing.com/rss/news_11.rss"
]

def send_message(message):
    try:
        bot.send_message(CHAT_ID, message)
        print("✅ Message envoyé")
    except Exception as e:
        print(f"Erreur Telegram : {e}")

def get_price():
    """Version ultra-stable qui affiche toujours le prix"""
    url = "https://api.oilpriceapi.com/v1/prices/latest"
    params = {'by_code': COMMODITY_CODE}
    headers = {'Authorization': f'Token {OILPRICE_API_KEY}'}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "success":
                price = data["data"]["price"]
                print(f"✅ Prix récupéré : {price:.2f}")
                return price
    except Exception as e:
        print(f"Erreur prix : {e}")
    return None

def get_rss_news():
    # (inchangé - même code que avant)
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

def check_buy_alert(price):
    """Alerte quand le prix approche un de tes niveaux"""
    for level in BUY_LEVELS:
        if abs(price - level) <= 0.25:  # alerte si ±0.25 $
            return f"🚨 **ALERTE BUY LIMIT** 🚨\nPrix actuel : **{price:.2f}**\nProche de ton niveau : **{level}**\n\n✅ Place ton Buy Limit maintenant !"
    return None

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
            # Prix toutes les 15 min (corrigé)
            send_message(f"📊 Prix OIL WTI : **{price:.2f} USD / baril**\n🕒 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
            
            # Alertes sur TES niveaux
            alert = check_buy_alert(price)
            if alert:
                send_message(alert)
        
        # News RSS
        send_message(get_rss_news())
        
        # Prédiction
        send_message(get_prediction())

        print("✅ Cycle terminé")
        
    except Exception as e:
        print(f"Erreur : {e}")

    time.sleep(900)  # 15 minutes
