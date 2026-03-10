"""
🔱 titan_K v2 — Battle Rhythm Briefing Engine
Generates all 9 daily briefing types, each tailored to its time slot.
Every briefing pulls LIVE data and uses GPT-4o for surgical analysis.

Schedule (Berlin time):
  07:00  blog         — ranto28 blog summary
  08:30  morning_macro — overnight global issues → portfolio insights → today's plan
  12:30  kr_close     — Korean market close → KR portfolio impact
  15:00  us_premarket — final preparation before US open
  15:40  us_open_40   — 40min after US open → quick status
  17:30  us_midday_1  — mid-session check
  19:30  us_midday_2  — mid-session check
  22:00  us_late      — late session check
  23:00  us_close     — US close summary + daily review
"""
import logging
from datetime import datetime
from typing import Dict

from openai import OpenAI
from config import (
    OPENAI_API_KEY, PORTFOLIO, WATCHLIST, EARNINGS_CALENDAR,
    TITAN_SYSTEM_URL, TIMEZONE,
)
from market_data import (
    fetch_stock_prices, fetch_market_snapshot, calculate_titan_k_index,
    get_vix_regime, fetch_fx_rate,
)
from config import WEIGHTS

logger = logging.getLogger("titan_k.battle_rhythm")

client = OpenAI(api_key=OPENAI_API_KEY)


# ══════════════════════════════════════════════════════════════════════════════
# SHARED DATA FETCHER
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_live_context() -> Dict:
    """Fetch all live data needed for any briefing type."""
    logger.info("Fetching live market context...")

    # All portfolio + watchlist tickers
    all_tickers = set()
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            all_tickers.add(pos["ticker"])
    for w in WATCHLIST:
        all_tickers.add(w["ticker"])

    prices = fetch_stock_prices(list(all_tickers))
    fx_rate = fetch_fx_rate()
    snapshot = fetch_market_snapshot()
    composite = calculate_titan_k_index(snapshot, WEIGHTS)

    vix_data = snapshot.get("VIX", {})
    vix_val = vix_data.get("value", 25)
    if isinstance(vix_val, (int, float)):
        regime, deploy_pct, label = get_vix_regime(vix_val)
    else:
        regime, deploy_pct, label = "UNKNOWN", 0, "?"

    # Build portfolio text
    portfolio_lines = []
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            t = pos["ticker"]
            p = prices.get(t, {})
            portfolio_lines.append(
                f"{t} ({pos['name']}) | ${p.get('price','?')} ({p.get('change_pct',0):+.1f}%) | "
                f"Score: {pos.get('score','?')}/10 | {pos.get('action','HOLD')}"
            )

    watchlist_lines = []
    for w in WATCHLIST:
        p = prices.get(w["ticker"], {})
        watchlist_lines.append(
            f"{w['ticker']} ({w['name']}) | ${p.get('price','?')} | Entry: {w['entry']} | Score: {w.get('score','?')}/10"
        )

    # Key moves
    key_indicators = ["VIX", "SPX", "NDX", "SOX", "Gold", "Oil", "DXY", "US10Y", "BTC", "Copper", "Uranium"]
    key_moves = []
    for ind in key_indicators:
        d = snapshot.get(ind, {})
        if isinstance(d.get("value"), (int, float)):
            key_moves.append(f"{ind}: {d['value']} ({d.get('change_pct',0):+.1f}%)")

    # Earnings check
    today = _berlin_now().strftime("%Y-%m-%d")
    earnings_today = [e for e in EARNINGS_CALENDAR if e["date"] == today]

    return {
        "prices": prices,
        "fx_rate": fx_rate,
        "vix": vix_val,
        "regime": regime,
        "deploy_pct": deploy_pct,
        "composite": composite,
        "portfolio_text": "\n".join(portfolio_lines),
        "watchlist_text": "\n".join(watchlist_lines),
        "key_moves": "\n".join(key_moves),
        "earnings_today": earnings_today,
        "snapshot": snapshot,
    }


def _format_key_moves(ctx: Dict) -> str:
    """Format key moves as compact lines."""
    snapshot = ctx["snapshot"]
    indicators = ["VIX", "SPX", "NDX", "SOX", "Gold", "Oil", "DXY", "BTC", "Copper", "Uranium"]
    lines = []
    for ind in indicators:
        d = snapshot.get(ind, {})
        if isinstance(d.get("value"), (int, float)):
            chg = d.get("change_pct", 0)
            direction = "▲" if chg >= 0 else "▼"
            bold = chg and abs(chg) >= 2
            if bold:
                lines.append(f"  <b>{direction} {ind} {d['value']} ({chg:+.1f}%)</b>")
            else:
                lines.append(f"  {direction} {ind} {d['value']} ({chg:+.1f}%)")
    return "\n".join(lines)


def _gpt_call(system: str, user: str, max_tokens: int = 500) -> str:
    """Make a GPT-4o call with error handling."""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.35,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"GPT call failed: {e}")
        return "⚠️ AI analysis unavailable. Check data manually."


def _berlin_now():
    """Get current Berlin time."""
    import pytz
    return datetime.now(pytz.timezone(TIMEZONE))


def _build_header(title: str, ctx: Dict) -> str:
    """Build standard briefing header with Berlin time."""
    regime_emoji = {"CALM": "🟢", "NORMAL": "🔵", "FEAR": "🟡", "CRISIS": "🔴"}.get(ctx["regime"], "⚪")
    now = _berlin_now()
    return (
        f"🔱 <b>{title}</b>\n"
        f"📅 {now.strftime('%Y-%m-%d %H:%M')} Berlin\n"
        f"{regime_emoji} {ctx['regime']} · VIX {ctx['vix']} · Deploy {ctx['deploy_pct']}%\n"
        f"{'━' * 28}\n\n"
    )


def _build_footer() -> str:
    return (
        f"\n{'━' * 28}\n"
        f"🔱 <a href=\"{TITAN_SYSTEM_URL}\">Open TITAN SYSTEM</a>"
    )


# ══════════════════════════════════════════════════════════════════════════════
# BRIEFING TYPE: morning_macro (08:30)
# ══════════════════════════════════════════════════════════════════════════════

def generate_morning_macro() -> str:
    """08:30 — Late night global issues → portfolio insights → today's plan."""
    ctx = _fetch_live_context()

    analysis = _gpt_call(
        system="""You are Minerva, briefing Titan at 8:30am Berlin.
FORMAT: Bullet points only. Max 15 words per bullet. This is read on a phone.

Structure:
🌍 OVERNIGHT
• [2-3 bullets: what happened globally while Titan slept]

💼 PORTFOLIO IMPACT
• [only positions affected — skip stable ones]
• format: TICKER → impact → action

📋 TODAY'S PLAN
• [3-5 specific actions for today with prices/times]
• Include any earnings, limit orders to set, exits to execute""",
        user=f"""LIVE DATA:
{ctx['key_moves']}
EUR/USD: {ctx['fx_rate']}

PORTFOLIO:
{ctx['portfolio_text']}

WATCHLIST:
{ctx['watchlist_text']}

EARNINGS TODAY: {', '.join(e['ticker'] + ' ' + e['timing'] for e in ctx['earnings_today']) or 'None'}""",
        max_tokens=500,
    )

    msg = _build_header("MORNING MACRO", ctx)
    msg += analysis
    msg += "\n\n<b>📊 KEY MOVES</b>\n" + _format_key_moves(ctx)
    msg += _build_footer()
    return msg


# ══════════════════════════════════════════════════════════════════════════════
# BRIEFING TYPE: kr_close (12:30)
# ══════════════════════════════════════════════════════════════════════════════

def generate_kr_close() -> str:
    """12:30 — Korean market close summary."""
    ctx = _fetch_live_context()

    # Korean tickers specifically
    kr_tickers = ["000660.KS", "272210.KS"]
    kr_lines = []
    for t in kr_tickers:
        p = ctx["prices"].get(t, {})
        for broker, positions in PORTFOLIO.items():
            for pos in positions:
                if pos["ticker"] == t:
                    kr_lines.append(
                        f"{t} ({pos['name']}) | Price: {p.get('price','?')} ({p.get('change_pct',0):+.1f}%) | {pos.get('action','HOLD')}"
                    )

    analysis = _gpt_call(
        system="""You are Minerva. Korean market just closed (12:30 Berlin = 19:30 Seoul).
FORMAT: Bullet points. Max 15 words per bullet.

Structure:
🇰🇷 KOREAN CLOSE
• [2-3 bullets: KOSPI direction, key Korean market themes]

💼 KR PORTFOLIO
• [SK Hynix and Hanwha status — price, change, any news]

🇺🇸 US PREVIEW
• [how Korean close signals for US open in 3 hours]
• [any actions to prepare for US session]""",
        user=f"""KOREAN POSITIONS:
{chr(10).join(kr_lines)}

GLOBAL CONTEXT:
{ctx['key_moves']}
EUR/USD: {ctx['fx_rate']}

FULL PORTFOLIO:
{ctx['portfolio_text']}""",
        max_tokens=400,
    )

    msg = _build_header("🇰🇷 KOREAN CLOSE", ctx)
    msg += analysis
    msg += _build_footer()
    return msg


# ══════════════════════════════════════════════════════════════════════════════
# BRIEFING TYPE: us_premarket (15:00)
# ══════════════════════════════════════════════════════════════════════════════

def generate_us_premarket() -> str:
    """15:00 — Final check before US market opens at 15:30 Berlin."""
    ctx = _fetch_live_context()

    analysis = _gpt_call(
        system="""You are Minerva. US market opens in 30 minutes (15:30 Berlin).
FORMAT: Bullet points. Max 15 words per bullet. Battle-ready.

Structure:
🎯 PRE-MARKET STATUS
• [futures direction, pre-market movers for Titan's stocks]

⚡ ORDERS CHECK
• [list every active limit order and stop — confirm they're armed]
• [any new orders to place before open?]

⚠️ WATCH AT OPEN
• [which stocks to watch in first 30min and why]
• [reminder: do NOT buy at open, wait 30min]""",
        user=f"""PORTFOLIO:
{ctx['portfolio_text']}

WATCHLIST:
{ctx['watchlist_text']}

MACRO:
{ctx['key_moves']}
EUR/USD: {ctx['fx_rate']}

EARNINGS TODAY: {', '.join(e['ticker'] + ' ' + e['timing'] for e in ctx['earnings_today']) or 'None'}""",
        max_tokens=450,
    )

    msg = _build_header("🇺🇸 US PRE-MARKET", ctx)
    msg += analysis
    msg += _build_footer()
    return msg


# ══════════════════════════════════════════════════════════════════════════════
# BRIEFING TYPE: us_session (15:40, 17:30, 19:30, 22:00)
# ══════════════════════════════════════════════════════════════════════════════

def generate_us_session(session_label: str, session_context: str) -> str:
    """Generic US session check — used for 15:40, 17:30, 19:30, 22:00."""
    ctx = _fetch_live_context()

    analysis = _gpt_call(
        system=f"""You are Minerva. {session_context}
FORMAT: Bullet points. Max 15 words per bullet. Quick scan.

Structure:
📊 STATUS
• [top 3-4 movers in Titan's portfolio right now]
• [any stock hitting stop or limit level?]

⚡ ACTION
• [what to do RIGHT NOW — be specific or say "no action needed"]
• [flag any position that changed status since last check]""",
        user=f"""PORTFOLIO:
{ctx['portfolio_text']}

WATCHLIST:
{ctx['watchlist_text']}

MACRO:
{ctx['key_moves']}""",
        max_tokens=350,
    )

    msg = _build_header(session_label, ctx)
    msg += analysis
    msg += "\n\n<b>📊 MOVES</b>\n" + _format_key_moves(ctx)
    msg += _build_footer()
    return msg


# ══════════════════════════════════════════════════════════════════════════════
# BRIEFING TYPE: us_close (23:00)
# ══════════════════════════════════════════════════════════════════════════════

def generate_us_close() -> str:
    """23:00 — US market close summary + daily review."""
    ctx = _fetch_live_context()

    analysis = _gpt_call(
        system="""You are Minerva. US market just closed (23:00 Berlin).
FORMAT: Bullet points. Max 15 words per bullet.

Structure:
🏁 MARKET CLOSE
• [SPX, NDX, SOX final: direction + % change]
• [VIX close level and what it means for tomorrow]

💼 PORTFOLIO REVIEW
• [biggest winners and losers today in Titan's portfolio]
• [any stops that triggered? any limits that filled?]

📋 SCORECARD UPDATE
• [any stock whose score should change based on today?]
• [positions that need attention tomorrow]

🌅 TOMORROW
• [1-2 bullets: what to prepare for tomorrow]
• [any earnings or macro events tomorrow?]""",
        user=f"""PORTFOLIO (end of day):
{ctx['portfolio_text']}

WATCHLIST:
{ctx['watchlist_text']}

MACRO:
{ctx['key_moves']}
EUR/USD: {ctx['fx_rate']}

TODAY'S EARNINGS: {', '.join(e['ticker'] + ' ' + e['timing'] for e in ctx['earnings_today']) or 'None'}""",
        max_tokens=600,
    )

    msg = _build_header("🏁 US MARKET CLOSE", ctx)
    msg += analysis
    msg += "\n\n<b>📊 FINAL</b>\n" + _format_key_moves(ctx)
    msg += _build_footer()
    return msg


# ══════════════════════════════════════════════════════════════════════════════
# MASTER DISPATCHER
# ══════════════════════════════════════════════════════════════════════════════

def generate_briefing(briefing_id: str) -> str:
    """Generate the appropriate briefing based on schedule ID."""
    logger.info(f"🔱 Generating briefing: {briefing_id}")

    if briefing_id == "blog":
        return None  # Blog briefing handled separately in main.py

    elif briefing_id == "morning_macro":
        return generate_morning_macro()

    elif briefing_id == "kr_close":
        return generate_kr_close()

    elif briefing_id == "us_premarket":
        return generate_us_premarket()

    elif briefing_id == "us_open_40":
        return generate_us_session(
            "⚡ 40min AFTER OPEN",
            "US market opened 40 minutes ago. First volatility wave is settling."
        )

    elif briefing_id == "us_midday_1":
        return generate_us_session(
            "📊 MID-SESSION #1",
            "US market mid-session (17:30 Berlin = 11:30 EST). Lunch hour, volume dips."
        )

    elif briefing_id == "us_midday_2":
        return generate_us_session(
            "📊 MID-SESSION #2",
            "US market afternoon (19:30 Berlin = 13:30 EST). Institutional flows resume."
        )

    elif briefing_id == "us_late":
        return generate_us_session(
            "📊 LATE SESSION",
            "US market late session (22:00 Berlin = 16:00 EST). Power hour — final positioning."
        )

    elif briefing_id == "us_close":
        return generate_us_close()

    else:
        logger.error(f"Unknown briefing_id: {briefing_id}")
        return None
