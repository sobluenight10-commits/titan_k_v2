"""
🔱 titan_K v2 — Android 24/7 Runner (Termux or any always-on device)
Unified Olympus system: interactive bot (/start, /olympus, /blog) + scheduled briefings + blog alerts.

Why Android: Laptop is off; server must run 24/7 for Telegram alarms and blog new-post alerts.

Usage on Android (Termux):
  1. Install Python, pip, then: pip install -r requirements.txt
  2. Copy .env with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (same as config)
  3. Run: python run_android.py
  4. Keep Termux in background (or use termux-boot). You will get:
     - Reply to /start and all commands
     - 06:45 Olympus update + Telegram
     - 07:00 Blog summary
     - New blog post → immediate Telegram alert (every 15 min check)
"""
import os
import sys

# Ensure we load .env from script directory
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)

from dotenv import load_dotenv
load_dotenv()

# Validate before starting
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.startswith("your"):
    print("ERROR: Set TELEGRAM_BOT_TOKEN in .env (from @BotFather)")
    sys.exit(1)
if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID.startswith("your"):
    print("ERROR: Set TELEGRAM_CHAT_ID in .env (send /start to your bot, then get id from @userinfobot)")
    sys.exit(1)

# Run full system (bot + scheduler + blog monitor). main.start_full_system() sends "Minerva ONLINE" to Telegram.
from main import start_full_system
start_full_system()
