"""
🔱 titan_K v2 — Main Entry Point
Orchestrates both daily missions and runs the scheduler.

Usage:
    python main.py              # Start scheduler (7am Berlin daily)
    python main.py --test       # Run both briefings now
    python main.py --blog       # Run blog briefing only
    python main.py --macro      # Run macro briefing only
    python main.py --ping       # Test Telegram connection
"""
import sys
import json
import os
import logging
import argparse
from datetime import datetime

import schedule
import time
import pytz

from config import (
    BRIEFING_HOUR, BRIEFING_MINUTE, TIMEZONE,
    OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DATA_FILE,
)

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("titan_k.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("titan_k.main")


def validate_config():
    """Check that all required config values are set."""
    missing = []
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("sk-your"):
        missing.append("OPENAI_API_KEY")
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.startswith("your"):
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID.startswith("your"):
        missing.append("TELEGRAM_CHAT_ID")
    
    if missing:
        logger.error(f"Missing config: {', '.join(missing)}")
        logger.error("Copy .env.example to .env and fill in your keys.")
        sys.exit(1)
    
    logger.info("✅ Configuration validated")


# ══════════════════════════════════════════════════════════════════════════════
# MISSION 1: Blog Briefing
# ══════════════════════════════════════════════════════════════════════════════

def run_blog_briefing():
    """
    Mission 1: Scrape ranto28 blog → GPT-4o analysis → Telegram briefing.
    """
    logger.info("=" * 60)
    logger.info("🔱 MISSION 1: Blog Intelligence Briefing")
    logger.info("=" * 60)
    
    from scraper import fetch_posts
    from analyzer import analyze_post, generate_blog_summary
    from telegram_bot import send_blog_briefing
    
    try:
        # Step 1: Fetch recent posts
        logger.info("Fetching ranto28 blog posts (last 24h)...")
        posts = fetch_posts(days_back=1, max_posts=5)
        
        if not posts:
            logger.warning("No new posts found. Trying 3-day window...")
            posts = fetch_posts(days_back=3, max_posts=5)
        
        if not posts:
            logger.warning("No posts found even in 3-day window. Sending notification.")
            from telegram_bot import send_telegram
            send_telegram(
                "🔱 <b>titan_K Blog Briefing</b>\n\n"
                "📭 No new posts from ranto28 in the past 3 days.\n"
                "Blog may be on hiatus. Manual check recommended."
            )
            return
        
        logger.info(f"Found {len(posts)} posts. Analyzing...")
        
        # Step 2: Analyze each post
        analyses = []
        for post in posts:
            result = analyze_post(post)
            if not result.get("error"):
                analyses.append(result)
            else:
                logger.warning(f"Analysis failed for: {post.get('title', '?')}")
        
        # Step 3: Generate executive summary
        summary = generate_blog_summary(analyses)
        
        # Step 4: Save to data file
        _save_analyses(analyses)
        
        # Step 5: Send Telegram
        briefing = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "posts": analyses,
            "summary": summary,
        }
        send_blog_briefing(briefing)
        
        logger.info(f"✅ Blog briefing sent: {len(analyses)} posts analyzed")
        
    except Exception as e:
        logger.error(f"Blog briefing failed: {e}", exc_info=True)
        try:
            from telegram_bot import send_telegram
            send_telegram(f"🔱 ⚠️ Blog briefing error: {str(e)[:200]}")
        except:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# MISSION 2: Macro + Portfolio Briefing
# ══════════════════════════════════════════════════════════════════════════════

def run_macro_briefing():
    """
    Mission 2: Global macro digest + portfolio impact → Telegram briefing.
    """
    logger.info("=" * 60)
    logger.info("🔱 MISSION 2: Macro + Portfolio Digest")
    logger.info("=" * 60)
    
    from macro_briefing import generate_full_macro_briefing
    from telegram_bot import send_macro_briefing
    
    try:
        briefing = generate_full_macro_briefing()
        send_macro_briefing(briefing)
        logger.info("✅ Macro briefing sent")
        
    except Exception as e:
        logger.error(f"Macro briefing failed: {e}", exc_info=True)
        try:
            from telegram_bot import send_telegram
            send_telegram(f"🔱 ⚠️ Macro briefing error: {str(e)[:200]}")
        except:
            pass


# ══════════════════════════════════════════════════════════════════════════════
# COMBINED DAILY JOB
# ══════════════════════════════════════════════════════════════════════════════

def run_daily_briefing():
    """Execute both missions in sequence."""
    berlin = pytz.timezone(TIMEZONE)
    now = datetime.now(berlin)
    logger.info(f"🔱 Daily briefing triggered at {now.strftime('%Y-%m-%d %H:%M %Z')}")
    
    # Mission 1: Blog
    run_blog_briefing()
    
    # Small pause between missions
    time.sleep(5)
    
    # Mission 2: Macro + Portfolio
    run_macro_briefing()
    
    logger.info("🔱 Both missions complete. Minerva standing by.")


# ══════════════════════════════════════════════════════════════════════════════
# SCHEDULER
# ══════════════════════════════════════════════════════════════════════════════

def start_scheduler():
    """Start the daily scheduler. Runs at BRIEFING_HOUR:BRIEFING_MINUTE Berlin time."""
    berlin = pytz.timezone(TIMEZONE)
    now = datetime.now(berlin)
    
    briefing_time = f"{BRIEFING_HOUR:02d}:{BRIEFING_MINUTE:02d}"
    
    logger.info("═" * 60)
    logger.info("🔱 titan_K v2 — SCHEDULER ACTIVE")
    logger.info(f"   Time now: {now.strftime('%Y-%m-%d %H:%M %Z')}")
    logger.info(f"   Daily briefing at: {briefing_time} Berlin")
    logger.info(f"   Missions: Blog + Macro/Portfolio → Telegram")
    logger.info("═" * 60)
    
    # Schedule uses local time — we need to convert Berlin time to system time
    # On Termux/Android, system time might differ from Berlin
    schedule.every().day.at(briefing_time).do(_scheduled_job)
    
    logger.info(f"Scheduler running. Next briefing at {briefing_time}. Ctrl+C to stop.")
    
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds


def _scheduled_job():
    """Wrapper for scheduled execution with timezone check."""
    berlin = pytz.timezone(TIMEZONE)
    now = datetime.now(berlin)
    
    # Only run on weekdays (markets closed on weekends, but macro still matters)
    # We run every day — weekend briefings are still valuable for preparation
    logger.info(f"Scheduled job triggered: {now.strftime('%A %Y-%m-%d %H:%M %Z')}")
    run_daily_briefing()


# ══════════════════════════════════════════════════════════════════════════════
# DATA PERSISTENCE
# ══════════════════════════════════════════════════════════════════════════════

def _save_analyses(new_analyses: list):
    """Save new analyses to the data file."""
    os.makedirs("data", exist_ok=True)
    
    data = {"analyses": [], "stocks": [], "last_run": None}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass
    
    # Deduplicate by URL
    existing_urls = {a.get("url") for a in data.get("analyses", [])}
    new_unique = [a for a in new_analyses if a.get("url") not in existing_urls]
    
    data["analyses"] = data.get("analyses", []) + new_unique
    
    # Extract stocks
    new_stocks = []
    for a in new_unique:
        new_stocks.extend(a.get("companies", []))
    
    existing_keys = {(s.get("name"), s.get("date_mentioned")) for s in data.get("stocks", [])}
    data["stocks"] = data.get("stocks", []) + [
        s for s in new_stocks
        if (s.get("name"), s.get("date_mentioned")) not in existing_keys
    ]
    
    data["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Saved {len(new_unique)} new analyses, {len(new_stocks)} new stocks")


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="🔱 titan_K v2 — Investment Intelligence System")
    parser.add_argument("--test", action="store_true", help="Run both briefings immediately")
    parser.add_argument("--blog", action="store_true", help="Run blog briefing only")
    parser.add_argument("--macro", action="store_true", help="Run macro briefing only")
    parser.add_argument("--ping", action="store_true", help="Test Telegram connection")
    
    args = parser.parse_args()
    
    # Always validate
    validate_config()
    
    if args.ping:
        from telegram_bot import send_test_ping
        send_test_ping()
        logger.info("✅ Ping sent. Check Telegram.")
    elif args.test:
        run_daily_briefing()
    elif args.blog:
        run_blog_briefing()
    elif args.macro:
        run_macro_briefing()
    else:
        # Default: start scheduler
        start_scheduler()


if __name__ == "__main__":
    main()
