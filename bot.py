import pandas as pd
import time
from datetime import datetime
import telebot
import os
from twelvedata import TDClient

# ================== CONFIG (ajoute sur Railway Variables) ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")          # ← TA CLÉ API ICI !
SENTIMENT_BIAS = os.getenv("SENTIMENT_BIAS", "bullish")

SYMBOL = "WTI"   # Crude Oil WTI Spot / USD sur Twelve Data
INTERVAL = "15min"   # ou "5min", "1h", etc.

print("🚀 Bot OIL WTI (Twelve Data) démarré - Sentiment :", SENTIMENT_BIAS.upper())
print("API Key présent :", "OUI" if TWELVE_API_KEY else "NON ❌")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Client Twelve Data
td = TDClient(apikey=TWELVE_API_KEY)

last_signal = None
last_bar_time = None

def send_signal(message):
    try:
        bot.send_message(CHAT_ID, f"🚨 SIGNAL OIL WTI (Twelve Data)\n{message}\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"✅ Signal envoyé : {message}")
    except Exception as e:
        print(f"❌ Erreur Telegram : {e}")

def get_data():
    """Récupère les données time series avec retry"""
    for attempt in range(3):
        try:
            ts = td.time_series(
                symbol=SYMBOL,
                interval=INTERVAL,
                outputsize=100,          # assez pour SMA 50 + marge
                timezone="UTC"
            )
            df = ts.as_pandas()      # retourne directement un DataFrame pandas
            if not df.empty:
                print(f"✅ Données Twelve Data récupérées ({len(df)} lignes) - Dernier prix : {df['close'].iloc[-1]:.2f}")
                return df
        except Exception as e:
            print(f"Tentative {attempt+1}/3 échouée : {str(e)[:100]}")
            time.sleep(10)
    print("❌ Impossible de récupérer les données après 3 essais")
    return None

def calculate_signals(df):
    global last_signal, last_bar_time
    if df is None or df.empty:
        return
    
    # Colonnes Twelve Data : open, high, low, close, volume
    df['sma_fast'] = df['close'].rolling(20).mean()
    df['sma_slow'] = df['close'].rolling(50).mean()
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = abs(delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    current_time = df.index[-1]
    if last_bar_time is not None and current_time == last_bar_time:
        return
    last_bar_time = current_time
    
    price = df['close'].iloc[-1]
    sma_f = df['sma_fast'].iloc[-1]
    sma_s = df['sma_slow'].iloc[-1]
    rsi = df['rsi'].iloc[-1]
    
    if pd.isna(sma_f) or pd.isna(sma_s) or pd.isna(rsi):
        return
    
    signal = None
    bias = SENTIMENT_BIAS.lower()
    
    if sma_f > sma_s and rsi > 50 and last_signal != "BUY":
        signal = f"🟢 **ACHAT FORT** OIL WTI\nPrix : {price:.2f}\nSMA20 > SMA50 + RSI {rsi:.1f} + {bias.upper()}"
        last_signal = "BUY"
    elif sma_f < sma_s and rsi < 50 and last_signal != "SELL":
        signal = f"🔴 **VENTE** OIL WTI\nPrix : {price:.2f}\nSMA20 < SMA50 + RSI {rsi:.1f}"
        last_signal = "SELL"
    elif bias == "bullish" and sma_f > sma_s and last_signal != "BUY":
        signal = f"🟢 **ACHAT FORCÉ (Géopolitique)** OIL WTI\nPrix : {price:.2f}\nSentiment X très haussier !"
        last_signal = "BUY"
    
    if signal:
        send_signal(signal)

while True:
    try:
        df = get_data()
        calculate_signals(df)
    except Exception as e:
        print("Erreur boucle :", e)
    time.sleep(60)  # Vérifie toutes les minutes
