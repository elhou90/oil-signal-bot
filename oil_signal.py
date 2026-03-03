import pandas as pd
import time
from datetime import datetime
import telebot
import yfinance as yf
import os

# ================== CONFIGURATION ==================
# Utilise les variables d'environnement (Railway / GitHub Secrets)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = int(os.environ.get("CHAT_ID", "0"))

SYMBOL_YF = "CL=F"            # Symbole Yahoo Finance pour Oil WTI
SYMBOL_DISPLAY = "OILCash#"   # Nom affiché dans les messages
INTERVAL = "15m"              # Intervalle M15
PERIOD = "5d"                 # Historique suffisant pour SMA50

SMA_FAST = 20
SMA_SLOW = 50

# ================== INIT ==================
if not TELEGRAM_TOKEN or CHAT_ID == 0:
    raise ValueError("❌ TELEGRAM_TOKEN et CHAT_ID doivent être définis en variables d'environnement.")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

last_signal = None
last_bar_time = None

# ================== FONCTIONS ==================
def send_signal(message):
    try:
        full_msg = f"🚨 SIGNAL OIL WTI\n{message}\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        bot.send_message(CHAT_ID, full_msg)
        print(f"Signal envoyé : {message}")
    except Exception as e:
        print("Erreur Telegram :", e)

def get_data():
    try:
        ticker = yf.Ticker(SYMBOL_YF)
        df = ticker.history(period=PERIOD, interval=INTERVAL)
        if df is None or df.empty:
            print("⚠️ Aucune donnée reçue de Yahoo Finance.")
            return None
        df.rename(columns={"Close": "close"}, inplace=True)
        df.index = pd.to_datetime(df.index)
        # Garder uniquement les dernières lignes nécessaires
        df = df.tail(SMA_SLOW + 10)
        return df
    except Exception as e:
        print(f"Erreur get_data : {e}")
        return None

def calculate_signals(df):
    global last_signal, last_bar_time

    df = df.copy()
    df['sma_fast'] = df['close'].rolling(SMA_FAST).mean()
    df['sma_slow'] = df['close'].rolling(SMA_SLOW).mean()

    # Ignorer si c'est la même bougie
    current_time = df.index[-1]
    if last_bar_time is not None and current_time == last_bar_time:
        return
    last_bar_time = current_time

    price = df['close'].iloc[-1]
    sma_f = df['sma_fast'].iloc[-1]
    sma_s = df['sma_slow'].iloc[-1]

    if pd.isna(sma_f) or pd.isna(sma_s):
        print("⚠️ SMA pas encore calculée (pas assez de données).")
        return

    signal = None
    if sma_f > sma_s and last_signal != "BUY":
        signal = f"🟢 *ACHAT* {SYMBOL_DISPLAY}\nPrix : {price:.2f}\nSMA{SMA_FAST} > SMA{SMA_SLOW}"
        last_signal = "BUY"
    elif sma_f < sma_s and last_signal != "SELL":
        signal = f"🔴 *VENTE* {SYMBOL_DISPLAY}\nPrix : {price:.2f}\nSMA{SMA_FAST} < SMA{SMA_SLOW}"
        last_signal = "SELL"

    if signal:
        send_signal(signal)
    else:
        print(f"[{datetime.now().strftime('%H:%M')}] Pas de nouveau signal. Prix: {price:.2f} | SMA{SMA_FAST}: {sma_f:.2f} | SMA{SMA_SLOW}: {sma_s:.2f}")

# ================== LANCEMENT ==================
print(f"✅ Bot démarré - {SYMBOL_DISPLAY} ({SYMBOL_YF}) - {datetime.now()}")
send_signal(f"🤖 Bot démarré\nSuivi de {SYMBOL_DISPLAY} sur M15\nSMA{SMA_FAST} / SMA{SMA_SLOW}")

while True:
    try:
        df = get_data()
        if df is not None:
            calculate_signals(df)
    except Exception as e:
        print(f"Erreur boucle principale : {e}")
    time.sleep(60)
