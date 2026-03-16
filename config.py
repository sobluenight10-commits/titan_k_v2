"""
🔱 titan_K v2 — Master Configuration
All portfolio positions, watchlist, indicator weights, and system constants.
Updated from TITAN_SYSTEM_v4.html (09 Mar 2026).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ── Timing ────────────────────────────────────────────────────────────────────
TIMEZONE = "Europe/Berlin"

# ── DAILY BATTLE RHYTHM (all times Berlin) ────────────────────────────────────
# Each entry: (time, briefing_id, description)
DAILY_SCHEDULE = [
    ("06:45", "olympus",      "🏛 Olympus Dashboard Update + 30-Index Forecast"),
    ("07:00", "blog",         "📰 Blog Summary"),
    ("08:30", "morning_macro","🌅 Late Night Global Issues → Portfolio Insights → Today's Plan"),
    ("12:30", "kr_close",     "🇰🇷 Korean Market Close Summary → Portfolio Impact"),
    ("15:00", "us_premarket", "🇺🇸 Final Check Before US Open → Preparation"),
    ("15:40", "us_open_40",   "⚡ 40min After US Open → Status + Actions"),
    ("17:30", "us_midday_1",  "📊 US Mid-Session Check #1"),
    ("19:30", "us_midday_2",  "📊 US Mid-Session Check #2"),
    ("22:00", "us_late",      "📊 US Late Session Check"),
    ("23:00", "us_close",     "🏁 US Market Close → Summary + Review"),
]

# ── Data Storage ──────────────────────────────────────────────────────────────
DATA_FILE = os.path.join("data", "titan_k_data.json")

# ── TITAN System Reference ────────────────────────────────────────────────────
# GitHub Pages URL for TITAN_SYSTEM_v4.html (update after deploying to GitHub Pages)
TITAN_SYSTEM_URL = os.getenv(
    "TITAN_SYSTEM_URL",
    "https://sobluenight10-commits.github.io/titan_k_v2/TITAN_SYSTEM_v4.html"
)

# ── Blog Source ───────────────────────────────────────────────────────────────
NAVER_BLOG_ID = "ranto28"
NAVER_BLOG_URL = f"https://blog.naver.com/{NAVER_BLOG_ID}"
NAVER_RSS_URL = f"https://rss.blog.naver.com/{NAVER_BLOG_ID}.xml"

# ── Exchange Rate Reference ───────────────────────────────────────────────────
DEFAULT_EUR_USD = 1.155  # fallback if live fetch fails

# ══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO — YOUR EXACT POSITIONS (from TITAN_SYSTEM_v4)
# ══════════════════════════════════════════════════════════════════════════════

PORTFOLIO = {
    # ── Trade Republic (EUR) ──────────────────────────────────────────────
    "TR": [
        {
            "ticker": "COHR", "name": "Coherent Corp.", "category": "Intelligence",
            "buy_price_eur": None, "shares": None,  # largest TR position
            "score": 7, "action": "HOLD",
            "thesis": "AI optical networking — spine of AI infrastructure",
            "stop_usd": None, "target_usd": 110,
        },
        {
            "ticker": "PLTR", "name": "Palantir", "category": "Intelligence",
            "buy_price_eur": None, "shares": None,
            "score": 10, "action": "HOLD + ADD DIPS",
            "thesis": "AI × Military — Maven Smart System with NATO",
            "stop_usd": None, "target_usd": 200, "limit_eur": 88,
        },
        {
            "ticker": "UEC", "name": "Uranium Energy", "category": "Energy",
            "buy_price_eur": None, "shares": None,
            "score": 9, "action": "HOLD — ADD AFTER EARNINGS",
            "thesis": "Nuclear renaissance — energy security narrative",
            "stop_usd": 11.50, "target_usd": 18,
        },
        {
            "ticker": "RKLB", "name": "Rocket Lab", "category": "Space",
            "buy_price_eur": None, "shares": None,
            "score": 6, "action": "HOLD",
            "thesis": "Space infrastructure — every satellite launch = revenue",
            "stop_eur": 115, "target_eur": 220,
        },
        {
            "ticker": "FSLR", "name": "First Solar", "category": "Energy",
            "buy_price_eur": None, "shares": None,
            "score": 1, "action": "EXIT — BROKEN THESIS",
            "thesis": "BROKEN — guidance -$1B vs consensus, Jefferies downgrade",
            "stop_usd": None, "target_usd": None,
        },
        {
            "ticker": "CWEN", "name": "Clearway Energy", "category": "Energy",
            "buy_price_eur": None, "shares": None,
            "score": None, "action": "HOLD",
            "thesis": "Clean energy yield play",
        },
        {
            "ticker": "TMO", "name": "Thermo Fisher", "category": "Bio-Engineering",
            "buy_price_eur": None, "shares": None,
            "score": 6, "action": "HOLD",
            "thesis": "Life sciences infrastructure — steady compounder",
        },
        {
            "ticker": "MC.PA", "name": "LVMH", "category": "Luxury",
            "buy_price_eur": None, "shares": None,
            "score": None, "action": "HOLD (locked ~1yr promo)",
            "thesis": "Promotional gift — locked position",
        },
        {
            "ticker": "FCX", "name": "Freeport-McMoRan", "category": "Energy",
            "buy_price_eur": None, "shares": None,
            "score": 4, "action": "SELL TR — KIWOOM STOP $54.50",
            "thesis": "Mine mudslide -28.5% production, recession fear hits copper",
            "stop_usd": 54.50,
        },
        {
            "ticker": "URNM", "name": "Sprott Uranium Miners", "category": "Energy",
            "buy_price_eur": None, "shares": None,
            "score": None, "action": "HOLD — ADD IN 2 WEEKS",
            "thesis": "Uranium ETF — nuclear renaissance basket",
        },
    ],

    # ── Kiwoom (KRW / USD) ────────────────────────────────────────────────
    "Kiwoom_KR": [
        {
            "ticker": "000660.KS", "name": "SK Hynix", "category": "Intelligence",
            "buy_price_krw": 130500, "shares": 6,
            "score": 10, "action": "LEGEND — NEVER SELL",
            "thesis": "HBM memory = hardware of AI. Irreplaceable. +657%",
        },
        {
            "ticker": "272210.KS", "name": "Hanwha Systems", "category": "Defense",
            "buy_price_krw": 16418, "shares": 128,
            "score": 10, "action": "LEGEND — NEVER SELL",
            "thesis": "Korean defense exports surging globally. +820%",
        },
    ],
    "Kiwoom_US": [
        {
            "ticker": "KTOS", "name": "Kratos Defense", "category": "Robotics/Defense",
            "buy_price_usd": None, "shares": 7,
            "score": 9, "action": "HOLD + ADD $80",
            "thesis": "Defense drones in active war — $1.5T DoD budget",
            "stop_usd": 75, "target_usd": 115, "limit_usd": 80,
        },
        {
            "ticker": "IONQ", "name": "IonQ Quantum", "category": "Intelligence",
            "buy_price_usd": None, "shares": 11,
            "score": 7, "action": "LIMIT $25 ACTIVE",
            "thesis": "Quantum computing inflection 2026-2027",
            "stop_usd": 25, "target_usd": 65, "limit_usd": 25,
        },
        {
            "ticker": "FCX", "name": "Freeport-McMoRan (KW)", "category": "Energy",
            "buy_price_usd": None, "shares": 3,
            "score": 4, "action": "STOP $54.50",
            "thesis": "Mine mudslide — stop protects until Apr 16",
            "stop_usd": 54.50,
        },
        {
            "ticker": "HUYA", "name": "HUYA", "category": "China/Platform",
            "buy_price_usd": None, "shares": None,
            "score": 2, "action": "EXIT MAR 17 — ALL SCENARIOS",
            "thesis": "BROKEN — no thesis, China ADR risk, -79% underwater",
        },
        {
            "ticker": "GEVO", "name": "Gevo", "category": "Energy",
            "buy_price_usd": None, "shares": None,
            "score": 4, "action": "HOLD TO MAR 26 ONLY",
            "thesis": "Recovering — new CEO, EBITDA positive. -84% underwater.",
        },
    ],
}

# ── WATCHLIST (pending buy orders / candidates) ───────────────────────────────
WATCHLIST = [
    {"ticker": "AVAV", "name": "AeroVironment", "category": "Robotics/Defense",
     "score": 8, "entry": "$205-240 post-earnings", "target_usd": 355,
     "amount": "€630 TR", "timing": "WED MAR 11 after Mar 10 earnings"},
    {"ticker": "CRSP", "name": "CRISPR Therapeutics", "category": "Bio-Engineering",
     "score": 8, "entry": "$44 limit", "target_usd": 106,
     "amount": "€300 TR", "timing": "Before Mar 26 earnings"},
    {"ticker": "NTLA", "name": "Intellia Therapeutics", "category": "Bio-Engineering",
     "score": 6, "entry": "$10 limit", "target_usd": 27,
     "amount": "€200 TR", "timing": "SET TODAY"},
    {"ticker": "IAU", "name": "iShares Gold ETF", "category": "Macro Hedge",
     "score": 10, "entry": "Any dip", "target_usd": None,
     "amount": "NEVER SELL", "timing": "HOLD FOREVER"},
]

# ── ALL TICKERS (for market data fetch) ───────────────────────────────────────
def get_all_tickers():
    """Return unique set of all tickers across portfolio + watchlist."""
    tickers = set()
    for broker_positions in PORTFOLIO.values():
        for pos in broker_positions:
            tickers.add(pos["ticker"])
    for w in WATCHLIST:
        tickers.add(w["ticker"])
    return sorted(tickers)


# ══════════════════════════════════════════════════════════════════════════════
# 30-INDICATOR COMPOSITE WEIGHTS (Macro Engine — Layer A)
# ══════════════════════════════════════════════════════════════════════════════

WEIGHTS = {
    # ── Fear & Volatility (25%) ───────────────────────────────────────────
    "VIX":           0.08,
    "VVIX":          0.03,
    "SKEW":          0.03,
    "Put/Call":      0.04,
    "VIX_Term":      0.04,
    "MOVE":          0.03,

    # ── Rates & Liquidity (20%) ───────────────────────────────────────────
    "US10Y":         0.05,
    "US2Y":          0.03,
    "Yield_Curve":   0.04,
    "DXY":           0.04,
    "Fed_Funds":     0.04,

    # ── Equity Internals (20%) ────────────────────────────────────────────
    "SPX":           0.04,
    "NDX":           0.03,
    "SOX":           0.05,
    "RSP_SPY":       0.03,
    "Adv_Dec":       0.03,
    "52W_HL":        0.02,

    # ── Commodities & Macro (15%) ─────────────────────────────────────────
    "Gold":          0.04,
    "Oil":           0.03,
    "Copper":        0.03,
    "Uranium":       0.03,
    "Nat_Gas":       0.02,

    # ── Credit & Risk (10%) ───────────────────────────────────────────────
    "HYG_Spread":    0.03,
    "IG_Spread":     0.02,
    "TED_Spread":    0.02,
    "LIBOR_OIS":     0.03,

    # ── Geopolitical & Sentiment (10%) ────────────────────────────────────
    "AAII_Bull":     0.02,
    "CNN_FG":        0.03,
    "Geopolitical":  0.03,
    "BTC":           0.02,
}

# ── VIX Regime Thresholds ─────────────────────────────────────────────────────
VIX_REGIMES = {
    "CALM":    {"range": (0, 15),    "deploy_pct": 0,   "label": "HOLD CASH"},
    "NORMAL":  {"range": (15, 20),   "deploy_pct": 25,  "label": "SELECTIVE"},
    "FEAR":    {"range": (20, 30),   "deploy_pct": 50,  "label": "DEPLOY 50%"},
    "CRISIS":  {"range": (30, 100),  "deploy_pct": 100, "label": "FULL DEPLOY"},
}

# ── Stock Scorecard Filters ───────────────────────────────────────────────────
SCORECARD_FILTERS = [
    "F1: Analyst Consensus",
    "F2: Thesis Intact",
    "F3: Macro/War Alignment",
    "F4: Earnings Trajectory",
    "F5: Position Size vs Conviction",
]

# ── Future-State Matrix Categories ────────────────────────────────────────────
FUTURE_STATE_CATEGORIES = [
    "Intelligence",      # AI, data, quantum
    "Energy",            # Nuclear, uranium, clean energy
    "Space",             # Launch, satellites, defense
    "Bio-Engineering",   # Gene editing, life sciences
    "Robotics",          # Drones, autonomous systems
]

# ── Earnings Calendar (upcoming) ──────────────────────────────────────────────
EARNINGS_CALENDAR = [
    {"ticker": "UEC",  "date": "2026-03-10", "timing": "BMO", "importance": "CRITICAL"},
    {"ticker": "AVAV", "date": "2026-03-10", "timing": "AMC", "importance": "CRITICAL"},
    {"ticker": "HUYA", "date": "2026-03-17", "timing": "BMO", "importance": "EXIT TRIGGER"},
    {"ticker": "CRSP", "date": "2026-03-26", "timing": "TBD", "importance": "CATALYST"},
    {"ticker": "GEVO", "date": "2026-03-26", "timing": "TBD", "importance": "EXIT TRIGGER"},
    {"ticker": "FCX",  "date": "2026-04-16", "timing": "TBD", "importance": "LOW"},
]

# ── Macro Events Calendar ─────────────────────────────────────────────────────
MACRO_CALENDAR = [
    {"event": "CPI Print", "date": "2026-03-11", "rule": "No new orders. Let limits work."},
    {"event": "PPI / PCE / GDP", "date": "2026-03-12", "rule": "Same. No reactions."},
]
