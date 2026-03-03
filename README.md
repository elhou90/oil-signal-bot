# oil-signal-bot
خاصة
# 🛢️ OIL WTI Signal Bot (Telegram + Railway)

Bot de trading qui détecte les croisements SMA20/SMA50 sur le WTI Oil (M15) et envoie des alertes Telegram.

## 📦 Stack
- **Données** : Yahoo Finance (`yfinance`) — remplace MetaTrader5 (incompatible Linux)
- **Alertes** : Telegram Bot
- **Hébergement** : Railway.app

---

## 🚀 Déploiement sur Railway

### 1. Prépare ton repo GitHub
```
bot.py
requirements.txt
Procfile
README.md
```

### 2. Variables d'environnement (Railway > Variables)

| Variable | Valeur |
|---|---|
| `TELEGRAM_TOKEN` | Token de ton bot Telegram (via @BotFather) |
| `CHAT_ID` | Ton Chat ID Telegram (via @userinfobot) |

⚠️ **Ne jamais mettre ces valeurs dans le code ou sur GitHub.**

### 3. Déploiement
1. Va sur [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub repo"
3. Sélectionne ton repo
4. Ajoute les variables d'environnement
5. Railway détecte le `Procfile` et lance `python bot.py`

---

## ⚙️ Configuration

Dans `bot.py`, tu peux modifier :

```python
SYMBOL_YF = "CL=F"    # Symbole Yahoo Finance (WTI Oil)
INTERVAL  = "15m"     # Timeframe
SMA_FAST  = 20        # Période SMA rapide
SMA_SLOW  = 50        # Période SMA lente
```

---

## 📡 Logique des signaux

| Condition | Signal |
|---|---|
| SMA20 croise au-dessus de SMA50 | 🟢 ACHAT |
| SMA20 croise en-dessous de SMA50 | 🔴 VENTE |

Un seul signal par croisement (pas de répétition).

---

## 🔒 Sécurité GitHub

Ajoute un fichier `.gitignore` :
```
__pycache__/
*.pyc
.env
```

Et ne commite jamais de fichier `.env` contenant tes secrets.
