# 🔱 titan_K v2 — Investment Intelligence System

**Titan's 24/7 automated investment briefing system.**

Two daily Telegram briefings at 07:00 Berlin time:
1. **Blog Briefing** — ranto28 Naver blog analysis via GPT-4o
2. **Macro + Portfolio Digest** — overnight global events mapped to your exact positions

## Quick Setup

### 1. Environment
```bash
cp .env.example .env
# Fill in your keys:
# OPENAI_API_KEY=sk-...
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...
```

### 2. Install Dependencies
```bash
# Windows (Cursor terminal)
pip install -r requirements.txt

# Android (Termux)
pip install -r requirements.txt
```

### 3. Run
```bash
# Test immediately (sends both briefings now)
python main.py --test

# Run as scheduler (7am Berlin daily)
python main.py

# Run only blog briefing
python main.py --blog

# Run only macro briefing
python main.py --macro
```

### 4. Cursor Agent Automation (New!)
Use `.cursor/automation.json` to set up scheduled runs via Cursor's agent feature.

### 5. Android 24/7 (Olympus server — required for alarms)
**If you get no Telegram messages:** the process must run 24/7 (laptop off = no alerts). Use an Android phone with Termux.

```bash
# On Android (Termux): same .env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
python run_android.py
```
See **[ANDROID.md](ANDROID.md)** for full setup. `/start` not replying? Bot wasn’t running or `TELEGRAM_CHAT_ID` is wrong — send `/start` and the bot will tell you your chat ID if the chat isn’t configured.

### 6. Olympus dashboard shows old data
Dashboard is `data/OLYMPUS_LIVE.html`, updated at 06:45 Berlin or manually:

```bash
python refresh_olympus.py        # Refresh HTML
python refresh_olympus.py --send  # Refresh + send summary to Telegram
```
Or double‑click **Refresh Olympus.bat** (Windows).

## Architecture
```
main.py              ← Entry point + scheduler
config.py            ← Portfolio, watchlist, weights, API keys
scraper.py           ← ranto28 Naver blog scraper
analyzer.py          ← GPT-4o blog post analysis
market_data.py       ← yfinance market snapshot + 30 indicators
macro_briefing.py    ← Overnight macro digest generator
portfolio.py         ← Portfolio tracker + scoring
telegram_bot.py      ← Telegram message sender
```
