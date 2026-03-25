"""
🔱 titan_K v2 — Battle Rhythm Briefing Engine (v3)
Weekday-only briefings. GPT-4o-mini for cost efficiency.
TITAN orders sent daily at 07:00.

Schedule (Berlin time, Mon-Fri only):
  07:00  master_daily — Blog + Macro + Scores + TITAN Orders
  15:00  us_premarket — Final prep before US open
  18:00  us_midday    — Open summary + institutional flows
  23:00  us_close     — Daily review + tomorrow prep

Weekly (Saturday only):
  07:00  olympus_weekly — Full dashboard update
"""
import logging
import os
import asyncio
from datetime import datetime
from typing import Dict

import requests
from openai import OpenAI
from config import (
    STOCKS,
    OPENAI_API_KEY, PORTFOLIO, WATCHLIST, EARNINGS_CALENDAR,
    TITAN_SYSTEM_URL, TIMEZONE, TELEGRAM_CHAT_ID, TITAN_BOT_TOKEN,
)
from market_data import (
    fetch_stock_prices, fetch_market_snapshot, calculate_titan_k_index,
    get_vix_regime, fetch_fx_rate,
)
from config import WEIGHTS

FUTURE_STATE_CATEGORIES = ["Intelligence", "Energy", "Space", "Bio-Engineering", "Robotics", "Infrastructure"]

PORTFOLIO = {
    "TR":        [s for s in STOCKS if s.get("broker") == "TR"        and s["status"] == "portfolio"],
    "Kiwoom_US": [s for s in STOCKS if s.get("broker") == "Kiwoom_US" and s["status"] == "portfolio"],
    "Kiwoom_KR": [s for s in STOCKS if s.get("broker") == "Kiwoom_KR" and s["status"] == "portfolio"],
}
WATCHLIST = [s for s in STOCKS if s["status"] == "watchlist"]

logger = logging.getLogger("titan_k.battle_rhythm")

client = OpenAI(api_key=OPENAI_API_KEY)

# ── Model selection ───────────────────────────────────────────────────────────
FAST_MODEL = "gpt-4o-mini"   # cost-efficient for all briefings
DEEP_MODEL = "gpt-4o"        # reserved for Olympus weekly only

QUANT_BRIEFING_PATH = os.path.join("data", "QUANT_BRIEFING.md")
NEWS_CACHE_PATH = os.path.join("data", "news_cache.json")

GOD_MISSION = (
    "⚔️ <b>GOD'S MISSION</b>\n"
    "🎯 ₩170,000,000,000 (~€115M) by 2036\n"
    "📈 ~47% CAGR · Beat Buffett every year\n"
    "💰 €25,000 + €1,500/month deployed\n"
    "🏝 Destination: Thailand Islands\n"
    "🔱 Belief: <b>INVINCIBLE</b>\n"
)


# ══════════════════════════════════════════════════════════════════════════════
# SHARED UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def _berlin_now():
    import pytz
    return datetime.now(pytz.timezone(TIMEZONE))


def _is_weekday() -> bool:
    return _berlin_now().weekday() < 5  # 0=Mon, 4=Fri


def _build_header(title: str, ctx: Dict) -> str:
    regime_emoji = {"CALM": "🟢", "NORMAL": "🔵", "FEAR": "🟡", "CRISIS": "🔴"}.get(ctx["regime"], "⚪")
    now = _berlin_now()
    return (
        f"{GOD_MISSION}"
        f"{'━' * 28}\n\n"
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


def _gpt_call(system: str, user: str, max_tokens: int = 500, model: str = FAST_MODEL) -> str:
    try:
        resp = client.chat.completions.create(
            model=model,
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
        return "⚠️ AI analysis unavailable."


def _fetch_live_context() -> Dict:
    logger.info("Fetching live market context...")
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

    vix_val = snapshot.get("VIX", {}).get("value", 25)
    if isinstance(vix_val, (int, float)):
        regime, deploy_pct, label = get_vix_regime(vix_val)
    else:
        regime, deploy_pct, label = "UNKNOWN", 0, "?"

    portfolio_lines = []
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            t = pos["ticker"]
            p = prices.get(t, {})
            portfolio_lines.append(
                f"{t} ({pos['name']}) | ${p.get('price','?')} ({p.get('change_pct',0):+.1f}%) | "
                f"Score:{pos.get('score','?')}/10 | {pos.get('action','HOLD')}"
            )

    watchlist_lines = []
    for w in WATCHLIST:
        p = prices.get(w["ticker"], {})
        watchlist_lines.append(
            f"{w['ticker']} ({w['name']}) | ${p.get('price','?')} | Entry:{w['entry']} | Score:{w.get('score','?')}/10"
        )

    key_indicators = ["VIX", "SPX", "NDX", "SOX", "Gold", "Oil", "DXY", "US10Y", "BTC", "Copper", "Uranium"]
    key_moves = []
    for ind in key_indicators:
        d = snapshot.get(ind, {})
        if isinstance(d.get("value"), (int, float)):
            chg = d.get("change_pct", 0)
            direction = "▲" if chg >= 0 else "▼"
            bold = abs(chg) >= 2
            if bold:
                key_moves.append(f"  <b>{direction} {ind} {d['value']} ({chg:+.1f}%)</b>")
            else:
                key_moves.append(f"  {direction} {ind} {d['value']} ({chg:+.1f}%)")

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


# ══════════════════════════════════════════════════════════════════════════════
# NEWS SCANNER — fetch headlines for all portfolio stocks
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_portfolio_news() -> Dict[str, list]:
    """Fetch latest headlines for every portfolio + watchlist stock via yfinance."""
    import yfinance as yf
    all_tickers = set()
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            all_tickers.add(pos["ticker"])
    for w in WATCHLIST:
        all_tickers.add(w["ticker"])

    news_by_ticker = {}
    for ticker in all_tickers:
        try:
            t = yf.Ticker(ticker)
            news_items = t.news or []
            headlines = []
            for item in news_items[:5]:
                content = item.get("content", {})
                title = content.get("title", item.get("title", ""))
                if title:
                    headlines.append(title)
            if headlines:
                news_by_ticker[ticker] = headlines
        except Exception as e:
            logger.debug(f"News fetch failed for {ticker}: {e}")

    logger.info(f"News fetched for {len(news_by_ticker)} tickers")
    return news_by_ticker


def _detect_catalysts(prices: Dict, news: Dict) -> str:
    """Detect stocks with significant price moves + news catalysts."""
    import json
    import os

    # Load previous prices from cache
    prev_prices = {}
    if os.path.exists(NEWS_CACHE_PATH):
        try:
            with open(NEWS_CACHE_PATH, "r") as f:
                cache = json.load(f)
                prev_prices = cache.get("prices", {})
        except:
            pass

    # Save current prices to cache
    os.makedirs("data", exist_ok=True)
    with open(NEWS_CACHE_PATH, "w") as f:
        json.dump({"prices": {t: d.get("price") for t, d in prices.items()}}, f)

    catalysts = []
    for ticker, price_data in prices.items():
        chg = price_data.get("change_pct", 0)
        current = price_data.get("price", 0)

        # Flag any move >2% with news
        if abs(chg) >= 2 and ticker in news:
            direction = "🟢 ▲" if chg > 0 else "🔴 ▼"
            headlines = news[ticker][:2]
            catalysts.append(
                f"{direction} <b>{ticker}</b> {chg:+.1f}% @ ${current}\n"
                f"  📰 {headlines[0][:80]}\n"
                + (f"  📰 {headlines[1][:80]}\n" if len(headlines) > 1 else "")
            )
        # Flag any move >4% even without news — unusual move
        elif abs(chg) >= 4:
            direction = "🟢 ▲" if chg > 0 else "🔴 ▼"
            catalysts.append(
                f"{direction} <b>{ticker}</b> {chg:+.1f}% @ ${current} — ⚠️ No news found. Investigate.\n"
            )

    if catalysts:
        return "<b>🚨 CATALYST ALERTS</b>\n" + "\n".join(catalysts)
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — MACRO LEADING INDICATOR CORRELATIONS
# ══════════════════════════════════════════════════════════════════════════════

# Key leading pairs: {macro_indicator: [(portfolio_ticker, direction, lag_desc)]}
MACRO_CORRELATIONS = {
    "SOX":     [("000660.KS", "+", "SK Hynix typically follows SOX overnight"),
                ("COHR", "+", "Coherent follows semiconductor index")],
    "Uranium": [("UEC", "+", "UEC tracks uranium spot closely"),
                ("URNM", "+", "URNM mirrors uranium ETF moves")],
    "Gold":    [("IAU", "+", "IAU directly tracks gold price")],
    "Oil":     [("FCX", "+", "Copper/FCX correlated with oil risk sentiment")],
    "DXY":     [("PLTR", "-", "Strong DXY headwind for US tech exports"),
                ("UEC", "-", "Uranium priced in USD — DXY inverse")],
    "BTC":     [("IONQ", "+", "Quantum/crypto risk-on correlation"),
                ("RKLB", "+", "Space/growth stocks follow BTC risk appetite")],
}

MACRO_MOVE_THRESHOLD = 1.5  # % move in macro indicator to trigger alert


def _generate_macro_forecast(snapshot: Dict) -> str:
    """Layer 2 — detect macro moves and forecast impact on portfolio."""
    forecasts = []

    for indicator, correlations in MACRO_CORRELATIONS.items():
        ind_data = snapshot.get(indicator, {})
        chg = ind_data.get("change_pct", 0)
        val = ind_data.get("value", "?")

        if not isinstance(chg, (int, float)):
            continue
        if abs(chg) < MACRO_MOVE_THRESHOLD:
            continue

        direction = "▲" if chg > 0 else "▼"
        bold = abs(chg) >= 3

        for ticker, corr_dir, desc in correlations:
            # Determine expected impact
            if (chg > 0 and corr_dir == "+") or (chg < 0 and corr_dir == "-"):
                impact = "🟢 Tailwind"
                expected = "likely UP"
            else:
                impact = "🔴 Headwind"
                expected = "likely DOWN"

            forecasts.append(
                f"{'<b>' if bold else ''}{direction} {indicator} {chg:+.1f}%{'</b>' if bold else ''} "
                f"→ <b>{ticker}</b> {impact} ({expected})\n"
                f"  💡 {desc}"
            )

    if forecasts:
        return "<b>🔭 MACRO PRELIMINARY FORECAST</b>\n" + "\n".join(forecasts) + "\n"
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — PRE-MARKET SCANNER
# ══════════════════════════════════════════════════════════════════════════════

def _scan_premarket(prices: Dict) -> str:
    """Layer 1 — detect pre-market movers before US open."""
    import yfinance as yf

    movers = []
    all_tickers = []
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            if ".KS" not in pos["ticker"]:  # US stocks only
                all_tickers.append(pos["ticker"])
    for w in WATCHLIST:
        if ".KS" not in w["ticker"]:
            all_tickers.append(w["ticker"])

    for ticker in all_tickers:
        try:
            t = yf.Ticker(ticker)
            info = t.fast_info
            pre_price = getattr(info, "pre_market_price", None)
            prev_close = getattr(info, "previous_close", None)

            if pre_price and prev_close and prev_close > 0:
                pre_chg = ((pre_price - prev_close) / prev_close) * 100
                if abs(pre_chg) >= 1.0:  # Flag >1% pre-market move
                    direction = "🟢 ▲" if pre_chg > 0 else "🔴 ▼"
                    movers.append(
                        f"{direction} <b>{ticker}</b> pre-market {pre_chg:+.1f}% "
                        f"(${pre_price:.2f} vs close ${prev_close:.2f})"
                    )
        except Exception as e:
            logger.debug(f"Pre-market scan failed for {ticker}: {e}")

    if movers:
        return "<b>🌅 PRE-MARKET MOVERS</b>\n" + "\n".join(movers) + "\n"
    return ""


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 3 — 30-MIN NEWS PULSE (background task)
# ══════════════════════════════════════════════════════════════════════════════

_last_seen_headlines: Dict[str, set] = {}


def run_news_pulse():
    """Runs every 2 hours. Synthesizes new headlines into ONE actionable brief."""
    import pytz
    berlin = pytz.timezone(TIMEZONE)
    now = datetime.now(berlin)
    if now.weekday() >= 5:
        return
    hour = now.hour + now.minute / 60
    if hour < 15.5 or hour > 23.1:
        return
    logger.info("Running news pulse synthesis...")
    try:
        fresh_news = _fetch_portfolio_news()
    except Exception as e:
        logger.error(f"News pulse fetch failed: {e}")
        return
    new_items = []
    for ticker, headlines in fresh_news.items():
        if ticker not in _last_seen_headlines:
            _last_seen_headlines[ticker] = set()
        new_headlines = [h for h in headlines if h not in _last_seen_headlines[ticker]]
        if new_headlines:
            _last_seen_headlines[ticker].update(new_headlines)
            for h in new_headlines[:2]:
                new_items.append(f"{ticker}: {h[:120]}")
    if not new_items:
        logger.info("News pulse: no new headlines")
        return
    try:
        headline_block = chr(10).join(new_items[:20])
        system = (
            "You are MINERVA, investment intelligence for a civilization-shift portfolio. "
            "Analyze NEW headlines and produce ONE concise actionable briefing. "
            "Format: "
            "Line 1: Market mood in one sentence. "
            "Line 2-3: 2-3 portfolio impacts (ticker + what it means). "
            "Line 4: SO WHAT — one concrete directive: BUY/HOLD/SELL/WATCH + ticker + reason + price level if relevant. "
            "If nothing actionable reply exactly: SKIP. "
            "Never list raw headlines. Always end with SO WHAT directive."
        )
        user = (
            f"Today {now.strftime('%Y-%m-%d %H:%M')} Berlin. New headlines:{chr(10)}{chr(10)}"
            f"{headline_block}{chr(10)}{chr(10)}"
            "Portfolio: SK Hynix(LEGEND), Hanwha(LEGEND), PLTR(HOLD), COHR(HOLD), "
            "UEC(HOLD+stop$11.50), AVAV(CAUTION), VRT(HOLD), ARKQ/BOTZ(HOLD), "
            "RKLB(HOLD), TMO(HOLD), URNM(HOLD), NTR(STRIKE-add before Mar31), "
            "Xiaomi(OBSERVE-Mar24earnings), IONQ(HOLD), TSMC(HOLD). "
            "EXIT: HUYA(-77%), GEVO(-87%Mar26), FCX(stop$54.50), IAU(+128%-sell-on-strength). "
            "Synthesize. End with SO WHAT directive."
        )
        response = _gpt_call(system, user, max_tokens=250)
        if not response or response.strip() == "SKIP":
            logger.info("News pulse: nothing actionable")
            return
        from telegram_bot import send_telegram
        msg = (
            f"⚡ <b>PULSE | {now.strftime('%H:%M')} Berlin</b>"
            f"{chr(10)}{'━' * 22}{chr(10)}{chr(10)}"
            f"{response.strip()}"
            f"{chr(10)}{chr(10)}<i>{len(new_items)} headlines synthesized</i>"
        )
        send_telegram(msg)
        logger.info(f"News pulse sent: {len(new_items)} headlines synthesized")
    except Exception as e:
        logger.error(f"News pulse GPT failed: {e}")


def _send_to_titan(message: str):
    """Send a message to GOD's Telegram using TITAN's bot token."""
    if not TITAN_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("TITAN_BOT_TOKEN or TELEGRAM_CHAT_ID not set — skipping TITAN message")
        return
    try:
        url = f"https://api.telegram.org/bot{TITAN_BOT_TOKEN}/sendMessage"
        chunks = []
        if len(message) <= 4096:
            chunks = [message]
        else:
            lines = message.split("\n")
            current = ""
            for line in lines:
                if len(current) + len(line) + 1 > 4096:
                    if current:
                        chunks.append(current)
                    current = line
                else:
                    current = current + "\n" + line if current else line
            if current:
                chunks.append(current)

        for chunk in chunks:
            requests.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }, timeout=15)
        logger.info("TITAN orders sent via Telegram")
    except Exception as e:
        logger.error(f"Failed to send to TITAN: {e}")


def _generate_titan_orders(ctx: Dict, blog_analyses: list, scores_summary: str, portfolio_news: Dict = None) -> str:
    """Minerva generates specific daily orders for TITAN."""
    now = _berlin_now()
    today = now.strftime("%Y-%m-%d")
    weekday = now.strftime("%A")

    # Build news summary for TITAN
    news_summary = ""
    if portfolio_news:
        news_lines = []
        for ticker, headlines in portfolio_news.items():
            if headlines:
                news_lines.append(f"[{ticker}]")
                for h in headlines[:3]:
                    news_lines.append(f"  - {h}")
        if news_lines:
            news_summary = "\n## PORTFOLIO NEWS TODAY\n" + "\n".join(news_lines)

    # Build QUANT_BRIEFING.md
    quant_lines = [
        f"# QUANT_BRIEFING — {today} ({weekday})",
        f"Generated by Minerva at {now.strftime('%H:%M')} Berlin\n",
        "## MACRO SNAPSHOT",
        ctx["key_moves"],
        f"\nVIX: {ctx['vix']} | Regime: {ctx['regime']} | Deploy: {ctx['deploy_pct']}%",
        f"EUR/USD: {ctx['fx_rate']}",
        f"Composite Score: {ctx['composite']}/100\n",
        "## PORTFOLIO STATUS",
        ctx["portfolio_text"],
        "\n## WATCHLIST",
        ctx["watchlist_text"],
    ]

    if blog_analyses:
        quant_lines.append("\n## RANTO28 BLOG — TODAY'S POSTS")
        for post in blog_analyses:
            title = post.get("title", "Untitled")
            insight = post.get("investment_insight", "")
            signal = post.get("watch_signal", "")
            companies = post.get("companies", [])
            quant_lines.append(f"### {title}")
            quant_lines.append(f"Signal: {signal}")
            quant_lines.append(f"Insight: {insight}")
            if companies:
                for c in companies:
                    quant_lines.append(f"- {c.get('name','')} ({c.get('ticker','?')}) Score:{c.get('titan_k_score','?')}/10")
            quant_lines.append("")

    if scores_summary:
        quant_lines.append("\n## SCORE REVISIONS TODAY")
        quant_lines.append(scores_summary)

    if news_summary:
        quant_lines.append(news_summary)

    quant_content = "\n".join(quant_lines)

    # Save QUANT_BRIEFING.md
    os.makedirs("data", exist_ok=True)
    with open(QUANT_BRIEFING_PATH, "w", encoding="utf-8") as f:
        f.write(quant_content)
    logger.info(f"QUANT_BRIEFING.md saved: {QUANT_BRIEFING_PATH}")

    # Generate TITAN orders via GPT
    orders_analysis = _gpt_call(
        system="""You are Minerva briefing TITAN — GOD's autonomous investment strategist.
GOD's mission: ₩170,000,000,000 (~€115M) by 2036. ~47% CAGR required.
TITAN Filter (Gate 0): "Does this position move GOD toward €115M by 2036?"

Generate specific, actionable orders for TITAN today.
FORMAT: Direct commands. Max 15 words per bullet. No fluff.

Structure:
🔍 RESEARCH TODAY
• [specific things to search and verify]

📊 ANALYZE
• [specific positions or candidates to run ARCHITECT gate on]

🎯 OUTPUT REQUIRED BY 14:00 BERLIN
• [exact format of what TITAN must deliver]
• Include: stock name, Gate 0 verdict, gates passed, buy/skip recommendation""",
        user=f"""TODAY'S DATA:
{quant_content[:2000]}

BLOG POSTS TODAY: {len(blog_analyses)} posts
EARNINGS TODAY: {', '.join(e['ticker'] for e in ctx['earnings_today']) or 'None'}
WEEKDAY: {weekday}
{'MONDAY — also prepare weekly + next week event calendar.' if weekday == 'Monday' else ''}""",
        max_tokens=400,
    )

    # Format TITAN message
    titan_msg = (
        f"⚔️ <b>MINERVA → TITAN DAILY ORDERS</b>\n"
        f"📅 {today} {weekday} | {now.strftime('%H:%M')} Berlin\n"
        f"{'━' * 28}\n\n"
        f"<b>GOD'S MISSION:</b> ₩170,000,000,000 by 2036\n"
        f"<b>Today's composite:</b> {ctx['composite']}/100 | VIX {ctx['vix']} | {ctx['regime']}\n\n"
        f"{orders_analysis}\n\n"
        f"{'━' * 28}\n"
        f"🔍 <b>STANDING ORDER — INTRADAY MONITORING</b>\n"
        f"• Watch ALL portfolio stocks for news catalysts during US session\n"
        f"• If any position moves >3% with news → alert GOD immediately\n"
        f"• Format: TICKER ▲/▼ X% | Catalyst: [news] | Action: [buy/hold/sell]\n"
        f"• Do NOT wait for scheduled briefing — alert in real time\n\n"
        f"📁 Full quant data in QUANT_BRIEFING.md\n"
        f"⏰ Report back to GOD before 15:00 Berlin.\n"
        f"🔱 <i>Minerva out.</i>"
    )

    return titan_msg


# ══════════════════════════════════════════════════════════════════════════════
# BRIEFING: master_daily (07:00 — THE MAIN BRIEFING)
# ══════════════════════════════════════════════════════════════════════════════

def generate_master_daily() -> str:
    """07:00 — Blog + Macro + Scores + ARCHITECT gate + TITAN orders."""
    ctx = _fetch_live_context()
    now = _berlin_now()
    weekday = now.strftime("%A")
    is_monday = weekday == "Monday"

    # ── Macro leading indicator forecast (Layer 2) ────────────────────────
    macro_forecast = _generate_macro_forecast(ctx["snapshot"])

    # ── News scan + catalyst detection ────────────────────────────────────────
    catalyst_section = ""
    portfolio_news = {}
    try:
        portfolio_news = _fetch_portfolio_news()
        catalyst_alert = _detect_catalysts(ctx["prices"], portfolio_news)
        if catalyst_alert:
            catalyst_section = catalyst_alert + "\n\n"
    except Exception as e:
        logger.error(f"News scan failed: {e}")

    # ── Blog analysis ──────────────────────────────────────────────────────
    blog_analyses = []
    blog_section = ""
    try:
        from scraper import fetch_blog_posts
        from analyzer import analyze_post, generate_blog_summary
        posts = fetch_blog_posts(days_back=1, max_posts=3)
        if not posts:
            posts = fetch_blog_posts(days_back=3, max_posts=3)
        if posts:
            blog_analyses = [r for p in posts if not (r := analyze_post(p)).get("error")]
            if blog_analyses:
                summary = generate_blog_summary(blog_analyses)
                blog_section = f"<b>📰 RANTO28 TODAY</b>\n{summary}\n\n"
                for post in blog_analyses[:2]:
                    signal = post.get("watch_signal", "—")
                    signal_emoji = "🟢" if "BUY" in signal else "🟡" if "WATCH" in signal else "🔴"
                    blog_section += f"{signal_emoji} <b>{post.get('title','')[:50]}</b>\n"
                    blog_section += f"  💡 {post.get('investment_insight','')[:80]}\n"
                    companies = post.get("companies", [])
                    for c in companies[:2]:
                        blog_section += f"  • {c.get('name','')} ({c.get('ticker','?')}) {c.get('titan_k_score','?')}/10\n"
                blog_section += "\n"
        else:
            blog_section = "📭 No new ranto28 posts today.\n\n"
    except Exception as e:
        logger.error(f"Blog analysis failed: {e}")
        blog_section = "📭 Blog fetch failed.\n\n"

    # ── Main GPT analysis ──────────────────────────────────────────────────
    monday_extra = ""
    if is_monday:
        monday_extra = """
📅 WEEKLY PREVIEW (Monday only)
• [2-3 key events THIS week with dates]
• [1-2 key events NEXT week to prepare for]
"""

    analysis = _gpt_call(
        system=f"""You are Minerva. 07:00 Berlin master daily brief. Weekday: {weekday}.
FORMAT: Bullet points. Max 15 words per bullet. Phone reading.
GOD's mission: ₩170,000,000,000 (~€115M) by 2036. ~47% CAGR required.
Gate 0: "Does this position move GOD toward €115M by 2036?"

Structure:
🌍 OVERNIGHT
• [2-3 bullets: key global events while GOD slept]

💼 PORTFOLIO IMPACT
• [only affected positions — TICKER → event → action]
• Flag any ARCHITECT gate changes

🏛 SCORE ALERTS
• [any position whose score should change today and why]

📋 TODAY'S ACTION PLAN
• [3-5 specific actions with prices]
• Flag active limits/stops{monday_extra}""",
        user=f"""MACRO:
{ctx['key_moves']}
EUR/USD: {ctx['fx_rate']} | Composite: {ctx['composite']}/100

PORTFOLIO:
{ctx['portfolio_text']}

WATCHLIST:
{ctx['watchlist_text']}

EARNINGS TODAY: {', '.join(e['ticker'] + ' ' + e['timing'] for e in ctx['earnings_today']) or 'None'}""",
        max_tokens=600,
    )

    # Extract scores summary for TITAN
    scores_summary = ""
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            if pos.get("action") and ("EXIT" in pos.get("action","") or "SELL" in pos.get("action","")):
                scores_summary += f"⚠️ {pos['ticker']}: {pos.get('action','')}\n"

    # ── Build message ──────────────────────────────────────────────────────
    msg = _build_header("📰 MASTER DAILY BRIEF", ctx)
    msg += macro_forecast
    msg += catalyst_section
    msg += blog_section
    msg += analysis
    msg += "\n\n<b>📊 KEY MOVES</b>\n" + ctx["key_moves"]
    msg += _build_footer()

    # ── Send TITAN orders ──────────────────────────────────────────────────
    try:
        titan_orders = _generate_titan_orders(ctx, blog_analyses, scores_summary, portfolio_news)
        _send_to_titan(titan_orders)
        logger.info("TITAN orders sent")
    except Exception as e:
        logger.error(f"TITAN orders failed: {e}")

    return msg


# ══════════════════════════════════════════════════════════════════════════════
# BRIEFING: us_premarket (15:00)
# ══════════════════════════════════════════════════════════════════════════════

def generate_us_premarket() -> str:
    """15:00 — Final check before US open + pre-market movers."""
    ctx = _fetch_live_context()

    # Layer 1 — pre-market scanner
    premarket_section = ""
    try:
        premarket_section = _scan_premarket(ctx["prices"])
    except Exception as e:
        logger.error(f"Pre-market scan failed: {e}")
    analysis = _gpt_call(
        system="""You are Minerva. US market opens in 30 minutes (15:30 Berlin).
FORMAT: Bullet points. Max 15 words per bullet. Battle-ready.
GOD's mission: ₩170,000,000,000 by 2036. Gate 0 on every action.

Structure:
🎯 PRE-MARKET STATUS
• [futures direction, pre-market movers in GOD's stocks]

⚡ ORDERS CHECK
• [list every active limit/stop — confirm armed]
• [any new orders to place before open?]

⚠️ WATCH AT OPEN
• [which stocks to watch first 30min and why]
• [do NOT buy at open — wait 30min for price discovery]""",
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
    msg += premarket_section
    msg += analysis
    msg += _build_footer()
    return msg


# ══════════════════════════════════════════════════════════════════════════════
# BRIEFING: us_midday (18:00)
# ══════════════════════════════════════════════════════════════════════════════

def generate_us_midday() -> str:
    """18:00 — 2.5hrs after open + institutional flows + catalyst detection."""
    ctx = _fetch_live_context()

    # Catalyst scan — critical at mid-session
    catalyst_section = ""
    try:
        portfolio_news = _fetch_portfolio_news()
        catalyst_alert = _detect_catalysts(ctx["prices"], portfolio_news)
        if catalyst_alert:
            catalyst_section = catalyst_alert + "\n\n"
    except Exception as e:
        logger.error(f"Mid-session news scan failed: {e}")
    analysis = _gpt_call(
        system="""You are Minerva. US market has been open 2.5 hours (18:00 Berlin = 12:00 EST).
FORMAT: Bullet points. Max 15 words per bullet.
GOD's mission: ₩170,000,000,000 by 2036.

Structure:
📊 MARKET FLOW SINCE OPEN
• [summarize price action from open to now]
• [which sectors leading / lagging]

🏦 INSTITUTIONAL FLOWS — CRITICAL
• [big money moves — block trades, sector rotation, unusual volume]
• [what are institutions buying/selling RIGHT NOW?]
• [any dark pool activity or options flow worth noting]

💼 GOD'S PORTFOLIO STATUS
• [top movers in GOD's positions]
• [any stop/limit approaching?]

⚡ ACTION PLAN UPDATE
• [revise today's action plan based on current flow]
• [specific: buy/hold/sell with price levels]""",
        user=f"""PORTFOLIO:
{ctx['portfolio_text']}

WATCHLIST:
{ctx['watchlist_text']}

MACRO (live):
{ctx['key_moves']}""",
        max_tokens=550,
    )
    msg = _build_header("⚡ MID-SESSION + INSTITUTIONAL FLOWS", ctx)
    msg += catalyst_section
    msg += analysis
    msg += "\n\n<b>📊 LIVE MOVES</b>\n" + ctx["key_moves"]
    msg += _build_footer()
    return msg


# ══════════════════════════════════════════════════════════════════════════════
# BRIEFING: us_close (23:00)
# ══════════════════════════════════════════════════════════════════════════════

def generate_us_close() -> str:
    """23:00 — Full daily review + tomorrow prep."""
    ctx = _fetch_live_context()
    analysis = _gpt_call(
        system="""You are Minerva. US market just closed (23:00 Berlin).
FORMAT: Bullet points. Max 15 words per bullet.
GOD's mission: ₩170,000,000,000 by 2036. ~47% CAGR required.

Structure:
🏁 MARKET CLOSE
• [SPX, NDX, SOX final — direction + % change]
• [VIX close — what it signals for tomorrow]

💼 PORTFOLIO REVIEW
• [winners and losers in GOD's portfolio today]
• [any stops triggered? any limits filled?]
• [Gate 0 check: did today's moves help or hurt the €115M mission?]

📋 SCORE UPDATE
• [any position whose ARCHITECT score should change?]
• [positions needing attention tomorrow]

🌅 TOMORROW PREP
• [1-2 specific things to prepare]
• [earnings or macro events tomorrow?]""",
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
    msg += "\n\n<b>📊 FINAL</b>\n" + ctx["key_moves"]
    msg += _build_footer()
    return msg


# ══════════════════════════════════════════════════════════════════════════════
# MASTER DISPATCHER
# ══════════════════════════════════════════════════════════════════════════════

def generate_briefing(briefing_id: str) -> str:
    """Generate the appropriate briefing. Returns None if not a weekday."""
    logger.info(f"🔱 Generating briefing: {briefing_id}")

    # Weekday check for daily briefings
    if briefing_id != "olympus_weekly" and not _is_weekday():
        logger.info(f"Skipping {briefing_id} — weekend")
        return None

    if briefing_id == "master_daily":
        return generate_master_daily()
    elif briefing_id == "us_premarket":
        return generate_us_premarket()
    elif briefing_id == "us_midday":
        return generate_us_midday()
    elif briefing_id == "us_close":
        return generate_us_close()
    elif briefing_id == "olympus_weekly":
        # Olympus weekly handled separately in main.py
        return None
    else:
        logger.error(f"Unknown briefing_id: {briefing_id}")
        return None
