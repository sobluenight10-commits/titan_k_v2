import schedule
import time
import asyncio
import json
from datetime import datetime
import pytz
from telegram import Bot
from scraper import fetch_posts
from analyzer import analyze_post
from market_data import fetch_market_snapshot, calculate_titan_k_index
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, DAILY_TIME, TIMEZONE, WEIGHTS, DATA_FILE
import os


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"analyses": [], "stocks": [], "last_run": None}


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_message(analyses, snapshot, titan_score):
    lines = [
        f"🔱 *titan\\_K Daily Briefing*",
        f"📅 {datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M')} Berlin",
        f"",
        f"🔱 *titan\\_K Index: {titan_score}/100*",
        f"{'🟢 DEPLOY CAPITAL' if titan_score>=60 else '🟡 WAIT FOR SIGNAL' if titan_score>=45 else '🔴 HOLD CASH'}",
        f"",
        f"📡 *Key Indicators:*",
        f"  VIX: {snapshot.get('VIX',{}).get('value','N/A')} — {snapshot.get('VIX',{}).get('signal','')}",
        f"  SOX: {snapshot.get('SOX',{}).get('value','N/A')} — {snapshot.get('SOX',{}).get('signal','')}",
        f"  Gold: {snapshot.get('Gold',{}).get('value','N/A')} — {snapshot.get('Gold',{}).get('signal','')}",
        f"",
        "=" * 35,
        f"📰 *TODAY'S BLOG INTELLIGENCE:*",
        ""
    ]

    all_gems = []
    all_strong = []

    for a in analyses:
        if a.get("error"):
            continue
        lines.append(f"📌 *{a.get('title','')[:60]}*")
        lines.append(f"💡 {a.get('investment_insight','')}")
        lines.append(f"Signal: {a.get('watch_signal','')}")
        lines.append("")

        for c in a.get("companies", []):
            if c.get("hidden_gem"):
                all_gems.append(c)
            if a.get("watch_signal") == "STRONG BUY":
                all_strong.append(c)

    if all_gems:
        lines.append("=" * 35)
        lines.append("💎 *HIDDEN GEMS TODAY:*")
        for g in all_gems:
            lines.append(f"  💎 {g.get('name','')} ({g.get('ticker','N/A')}) Score: {g.get('titan_k_score','')}/10")
            lines.append(f"     Buy when: {g.get('when_to_buy','')}")

    if all_strong:
        lines.append("")
        lines.append("🔥 *STRONG BUY SIGNALS:*")
        for s in all_strong:
            lines.append(f"  ✅ {s.get('name','')} ({s.get('ticker','N/A')})")

    return "\n".join(lines)


async def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] No credentials set. Skipping.")
        return
    bot = Bot(token=TELEGRAM_TOKEN)
    max_len = 4000
    chunks = [message[i:i+max_len] for i in range(0, len(message), max_len)]
    for chunk in chunks:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=chunk, parse_mode="Markdown")
    print("[TELEGRAM] Sent successfully")


def daily_job():
    print(f"\n⏰ titan_K daily run at {datetime.now().strftime('%H:%M')}")
    data = load_data()

    posts = fetch_posts(days_back=1)
    new_analyses = []
    new_stocks = []

    for post in posts:
        result = analyze_post(post)
        if not result.get("error"):
            new_analyses.append(result)
            new_stocks.extend(result.get("companies", []))

    existing_urls = {a.get("url") for a in data["analyses"]}
    data["analyses"] += [a for a in new_analyses if a.get("url") not in existing_urls]
    data["stocks"] += new_stocks
    data["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_data(data)

    snapshot = fetch_market_snapshot()
    titan_score = calculate_titan_k_index(snapshot, WEIGHTS)
    message = build_message(new_analyses, snapshot, titan_score)
    asyncio.run(send_telegram(message))
    print("[DONE] Daily job complete")


print(f"🔱 titan_K Scheduler running. Daily at {DAILY_TIME} Berlin time.")
schedule.every().day.at(DAILY_TIME).do(daily_job)

while True:
    schedule.run_pending()
    time.sleep(60)
