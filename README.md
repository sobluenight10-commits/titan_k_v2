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

### 5. Android Termux 24/7 Server
```bash
# In Termux:
cd ~/titan_k_v2
nohup python main.py &

# Or use termux-job-scheduler for reliability
```

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
