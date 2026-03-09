"""
titan_K PHONE SCHEDULER
========================
Lightweight version for Flip 3 / Termux
- NO pandas, NO numpy, NO yfinance
- Uses only: requests, feedparser, python-telegram-bot, schedule, openai
- Tasks: blog monitor, stock alerts, global news alerts
"""

import os
import time
import schedule
import requests
import feedparser
from datetime import datetime
from dotenv import load_dotenv
import pytz
import asyncio
from telegram import Bot

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BERLIN = pytz.timezone("Europe/Berlin")

# ── Stock watchlist (Yahoo Finance query API, no yfinance library needed) ──────
WATCHLIST = {
    "PLTR":  {"name": "Palantir",        "alert_below": 120, "alert_above": 160},
    "COHR":  {"name": "Coherent",        "alert_below": 220, "alert_above": 300},
    "RKLB":  {"name": "Rocket Lab",      "alert_below": 55,  "alert_above": 85},
    "UEC":   {"name": "Uranium Energy",  "alert_below": 12,  "alert_above": 20},
    "FCX":   {"name": "Freeport-McMoRan","alert_below": 35,  "alert_above": 55},
}

KR_WATCHLIST = {
    "000660.KS": {"name": "SK Hynix",      "alert_below": 140000, "alert_above": 200000},
    "272210.KS": {"name": "Hanwha Systems", "alert_below": 100000, "alert_above": 150000},
}

BLOG_RSS = "https://rss.blog.naver.com/ranto28.xml"
last_seen_blog_id = None


# ── Telegram sender ────────────────────────────────────────────────────────────
async def send_telegram(message: str):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="HTML")

def notify(message: str):
    asyncio.run(send_telegram(message))


# ── Stock price fetch (no yfinance - uses Yahoo Finance v8 API directly) ──────
def get_price(ticker: str) -> float | None:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return round(price, 2)
    except Exception as e:
        print(f"[price error] {ticker}: {e}")
        return None


# ── Blog monitor ───────────────────────────────────────────────────────────────
def check_blog():
    global last_seen_blog_id
    try:
        feed = feedparser.parse(BLOG_RSS)
        if not feed.entries:
            return
        latest = feed.entries[0]
        entry_id = latest.get("id") or latest.get("link")
        if entry_id != last_seen_blog_id:
            last_seen_blog_id = entry_id
            title = latest.get("title", "No title")
            link = latest.get("link", "")
            now = datetime.now(BERLIN).strftime("%Y-%m-%d %H:%M")
            msg = (
                f"📰 <b>ranto28 NEW POST</b>\n"
                f"🕐 {now} Berlin\n\n"
                f"<b>{title}</b>\n"
                f"{link}"
            )
            notify(msg)
            print(f"[blog] New post: {title}")
        else:
            print(f"[blog] No new post")
    except Exception as e:
        print(f"[blog error] {e}")


# ── Stock alerts ───────────────────────────────────────────────────────────────
def check_stocks():
    alerts = []
    now = datetime.now(BERLIN).strftime("%Y-%m-%d %H:%M")

    for ticker, info in WATCHLIST.items():
        price = get_price(ticker)
        if price is None:
            continue
        name = info["name"]
        lo = info["alert_below"]
        hi = info["alert_above"]
        if price <= lo:
            alerts.append(f"🔴 <b>{name} ({ticker})</b> ${price} — BELOW alert ${lo}")
        elif price >= hi:
            alerts.append(f"🟢 <b>{name} ({ticker})</b> ${price} — ABOVE alert ${hi}")
        else:
            print(f"[stocks] {ticker}: ${price} (no alert)")

    for ticker, info in KR_WATCHLIST.items():
        price = get_price(ticker)
        if price is None:
            continue
        name = info["name"]
        lo = info["alert_below"]
        hi = info["alert_above"]
        if price <= lo:
            alerts.append(f"🔴 <b>{name} ({ticker})</b> ₩{price:,.0f} — BELOW ₩{lo:,}")
        elif price >= hi:
            alerts.append(f"🟢 <b>{name} ({ticker})</b> ₩{price:,.0f} — ABOVE ₩{hi:,}")

    if alerts:
        msg = f"⚡ <b>TITAN STOCK ALERT</b> | {now}\n\n" + "\n".join(alerts)
        notify(msg)
        print(f"[stocks] {len(alerts)} alert(s) sent")


# ── Morning briefing ───────────────────────────────────────────────────────────
def morning_briefing():
    now = datetime.now(BERLIN).strftime("%Y-%m-%d %H:%M")
    lines = [f"🔱 <b>TITAN MORNING BRIEFING</b> | {now}\n"]

    for ticker, info in {**WATCHLIST, **KR_WATCHLIST}.items():
        price = get_price(ticker)
        name = info["name"]
        currency = "₩" if ".KS" in ticker else "$"
        if price:
            fmt = f"{price:,.0f}" if ".KS" in ticker else f"{price:.2f}"
            lines.append(f"• <b>{name}</b> ({ticker}): {currency}{fmt}")
        else:
            lines.append(f"• <b>{name}</b> ({ticker}): N/A")

    lines.append("\n📰 Checking ranto28 blog...")
    notify("\n".join(lines))
    check_blog()


# ── Schedule ───────────────────────────────────────────────────────────────────
schedule.every().day.at("07:00").do(morning_briefing)   # 7am Berlin briefing
schedule.every(30).minutes.do(check_blog)                # blog check every 30min
schedule.every(60).minutes.do(check_stocks)              # stock alerts every 1hr

print("🔱 titan_K Phone Scheduler running...")
print(f"   Time: {datetime.now(BERLIN).strftime('%Y-%m-%d %H:%M')} Berlin")
print("   Sending startup notification...")
notify("🔱 <b>titan_K Phone Scheduler ONLINE</b>\nFlip 3 is watching the market.")

# Run immediately on start
check_blog()
check_stocks()

while True:
    schedule.run_pending()
    time.sleep(60)
