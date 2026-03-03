import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import telebot
import os

# ================== CONFIG (remplis sur Railway) ==================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SENTIMENT_BIAS = os.getenv("SENTIMENT_BIAS", "neutral")  # ← JE TE DIS QUOI METTRE CHAQUE JOUR

SYMBOL = "CL=F"  # WTI Crude Oil

print("🚀 Bot OIL WTI amélioré démarré - Sentiment actuel :", SENTIMENT_BIAS.upper())

bot = telebot.TeleBot(TELEGRAM_TOKEN)

last_signal = None
last_bar_time = None

def send_signal(message):
    try:
        bot.send_message(CHAT_ID, f"🚨 SIGNAL OIL WTI\n{message}\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"✅ Signal envoyé : {message}")
    except Exception as e:
        print(f"❌ Erreur Telegram : {e}")

def get_data():
    df = yf.download(SYMBOL, period="10d", interval="15m", progress=False)
    return df

def calculate_signals(df):
    global last_signal, last_bar_time
    
    df['sma_fast'] = df['Close'].rolling(20).mean()
    df['sma_slow'] = df['Close'].rolling(50).mean()
    df['rsi'] = 100 - (100 / (1 + (df['Close'].diff(1).where(df['Close'].diff(1) > 0, 0).rolling(14).mean() / 
                                   abs(df['Close'].diff(1).where(df['Close'].diff(1) < 0, 0)).rolling(14).mean())))
    
    current_time = df.index[-1]
    if last_bar_time is not None and current_time == last_bar_time:
        return
    last_bar_time = current_time
    
    price = df['Close'].iloc[-1]
    sma_f = df['sma_fast'].iloc[-1]
    sma_s = df['sma_slow'].iloc[-1]
    rsi = df['rsi'].iloc[-1]
    
    if pd.isna(sma_f) or pd.isna(sma_s) or pd.isna(rsi):
        return
    
    signal = None
    bias = SENTIMENT_BIAS.lower()
    
    # Stratégie améliorée
    if sma_f > sma_s and rsi > 50 and last_signal != "BUY":
        signal = f"🟢 **ACHAT FORT** OIL WTI\nPrix : {price:.2f}\nSMA20 > SMA50 + RSI {rsi:.1f} + Sentiment {bias.upper()}"
        last_signal = "BUY"
    elif sma_f < sma_s and rsi < 50 and last_signal != "SELL":
        signal = f"🔴 **VENTE** OIL WTI\nPrix : {price:.2f}\nSMA20 < SMA50 + RSI {rsi:.1f}"
        last_signal = "SELL"
    
    # Bonus sentiment : force ACHAT si géopolitique très haussier
    elif bias == "bullish" and sma_f > sma_s and last_signal != "BUY":
        signal = f"🟢 **ACHAT FORCÉ (Géopolitique)** OIL WTI\nPrix : {price:.2f}\nSentiment X très haussier !"
        last_signal = "BUY"
    
    if signal:
        send_signal(signal)

while True:
    try:
        df = get_data()
        if df is not None and not df.empty:
            calculate_signals(df)
    except Exception as e:
        print("Erreur :", e)
    time.sleep(60)
