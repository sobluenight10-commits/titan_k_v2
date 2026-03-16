"""
🔱 titan_K v2 — Telegram Bot Sender
Sends formatted briefings to Titan via Telegram.
"""
import asyncio
import logging
from telegram import Bot
from telegram.constants import ParseMode
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger("titan_k.telegram")

MAX_MESSAGE_LENGTH = 4096  # Telegram limit


async def _send_message_async(text: str, parse_mode: str = ParseMode.HTML):
    """Send a single message via Telegram Bot API."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Split long messages
    chunks = []
    if len(text) <= MAX_MESSAGE_LENGTH:
        chunks = [text]
    else:
        lines = text.split("\n")
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > MAX_MESSAGE_LENGTH:
                if current:
                    chunks.append(current)
                current = line
            else:
                current = current + "\n" + line if current else line
        if current:
            chunks.append(current)
    
    for i, chunk in enumerate(chunks):
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=chunk,
                parse_mode=parse_mode,
                disable_web_page_preview=True,
            )
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)  # rate limit
        except Exception as e:
            logger.error(f"Telegram send error (chunk {i+1}): {e}")
            # Fallback: try without parse mode
            try:
                await bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=chunk,
                    disable_web_page_preview=True,
                )
            except Exception as e2:
                logger.error(f"Telegram fallback send also failed: {e2}")


def send_telegram(text: str, parse_mode: str = ParseMode.HTML):
    """Synchronous wrapper for sending Telegram messages."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an existing event loop (e.g., Jupyter, Termux edge case)
            import nest_asyncio
            nest_asyncio.apply()
            loop.run_until_complete(_send_message_async(text, parse_mode))
        else:
            loop.run_until_complete(_send_message_async(text, parse_mode))
    except RuntimeError:
        # No event loop exists
        asyncio.run(_send_message_async(text, parse_mode))


def send_blog_briefing(briefing: dict):
    """Format and send the blog analysis briefing."""
    from config import TITAN_SYSTEM_URL
    
    posts = briefing.get("posts", [])
    summary = briefing.get("summary", "No summary available.")
    timestamp = briefing.get("timestamp", "")
    
    header = (
        f"🔱 <b>titan_K BLOG BRIEFING</b>\n"
        f"📅 {timestamp} Berlin\n"
        f"📡 ranto28 Naver Blog\n"
        f"{'━' * 28}\n\n"
    )
    
    body = f"<b>📋 SUMMARY</b>\n{summary}\n\n"
    
    if posts:
        body += f"<b>📰 {len(posts)} ARTICLES</b>\n\n"
        for i, post in enumerate(posts, 1):
            signal = post.get("watch_signal", "—")
            signal_emoji = "🟢" if "BUY" in signal else "🟡" if "WATCH" in signal else "🔴"
            paradigm = " 🌍" if post.get("paradigm_shift") else ""
            
            body += (
                f"<b>{i}. {post.get('title', 'Untitled')}</b>{paradigm}\n"
                f"  {signal_emoji} {signal}\n"
                f"  💡 {post.get('investment_insight', '—')}\n"
            )
            
            companies = post.get("companies", [])
            if companies:
                for c in companies[:3]:
                    gem = "💎" if c.get("hidden_gem") else "•"
                    body += (
                        f"  {gem} {c.get('name', '')} ({c.get('ticker', '?')}) "
                        f"{c.get('titan_k_score', '?')}/10\n"
                    )
            body += "\n"
    
    footer = (
        f"{'━' * 28}\n"
        f"🔱 <a href=\"{TITAN_SYSTEM_URL}\">Open TITAN SYSTEM</a>\n"
        f"<i>The market comes to your prices.</i>"
    )
    
    send_telegram(header + body + footer)


def send_macro_briefing(briefing: dict):
    """Format and send the macro + portfolio digest — optimized for phone reading."""
    from config import TITAN_SYSTEM_URL
    
    timestamp = briefing.get("timestamp", "")
    vix = briefing.get("vix", {})
    regime = briefing.get("regime", "UNKNOWN")
    deploy_pct = briefing.get("deploy_pct", 0)
    composite = briefing.get("composite_score", 0)
    
    # Regime emoji
    regime_emoji = {
        "CALM": "🟢", "NORMAL": "🔵", "FEAR": "🟡", "CRISIS": "🔴"
    }.get(regime, "⚪")
    
    # ── HEADER (compact) ──
    vix_val = vix.get('value', '?')
    vix_chg = vix.get('change_pct', 0)
    vix_dir = "📉" if vix_chg < 0 else "📈"
    
    header = (
        f"🔱 <b>titan_K MACRO DIGEST</b>\n"
        f"📅 {timestamp} Berlin\n"
        f"{'━' * 28}\n\n"
        f"{regime_emoji} <b>{regime}</b> · VIX {vix_val} ({vix_chg:+.1f}%)\n"
        f"📊 Composite {composite}/100 → Deploy {deploy_pct}%\n\n"
    )
    
    # ── OVERNIGHT (already bullet-formatted by GPT) ──
    overnight = briefing.get("overnight_summary", "")
    body = f"<b>🌙 OVERNIGHT</b>\n{overnight}\n\n"
    
    # ── KEY MOVES (compact table) ──
    key_moves = briefing.get("key_moves", [])
    if key_moves:
        body += "<b>📊 KEY MOVES</b>\n"
        for move in key_moves:
            direction = "▲" if move.get("change_pct", 0) >= 0 else "▼"
            chg = move.get("change_pct", 0)
            # Color-code with bold for big moves
            if abs(chg) >= 3:
                body += f"  <b>{direction} {move['name']} {move.get('value', '?')} ({chg:+.1f}%)</b>\n"
            else:
                body += f"  {direction} {move['name']} {move.get('value', '?')} ({chg:+.1f}%)\n"
        body += "\n"
    
    # ── PORTFOLIO IMPACT (already bullet-formatted by GPT) ──
    portfolio_impact = briefing.get("portfolio_impact", "")
    if portfolio_impact:
        body += f"<b>💼 PORTFOLIO</b>\n{portfolio_impact}\n\n"
    
    # ── TODAY'S ACTIONS ──
    actions = briefing.get("todays_actions", "")
    if actions:
        body += f"<b>⚡ TODAY</b>\n{actions}\n\n"
    
    # ── EARNINGS ──
    earnings = briefing.get("earnings_today", [])
    if earnings:
        body += "<b>📅 EARNINGS TODAY</b>\n"
        for e in earnings:
            body += f"  🔴 {e['ticker']} {e.get('timing', '')} — {e.get('importance', '')}\n"
        body += "\n"
    
    # ── FOOTER with system URL ──
    footer = (
        f"{'━' * 28}\n"
        f"🔱 <a href=\"{TITAN_SYSTEM_URL}\">Open TITAN SYSTEM</a>\n"
        f"<i>Limits armed. Go to work.</i>"
    )
    
    send_telegram(header + body + footer)


def send_olympus_briefing(data: dict):
    """Format and send the Olympus forecast update."""
    from olympus_engine import get_olympus_telegram_summary
    msg = get_olympus_telegram_summary(data)
    send_telegram(msg)


def send_test_ping():
    """Send a test message to verify bot connection."""
    send_telegram(
        "🔱 <b>titan_K v2 — CONNECTION TEST</b>\n\n"
        "✅ Bot is online and connected.\n"
        "📡 Briefings will arrive at 07:00 Berlin time.\n\n"
        "<i>Minerva standing by.</i>"
    )
