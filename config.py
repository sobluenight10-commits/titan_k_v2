"""
🔱 OLYMPUS — gods_plan Master Configuration
Civilization-Shift Investment System
Updated: 2026-03-21 — Full v5 rewrite
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY      = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_BOT_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID    = os.getenv("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN        = os.getenv("GITHUB_TOKEN", "")  # for auto-push dashboard

# ── GitHub Pages Config ───────────────────────────────────────────────────────
GITHUB_REPO         = "sobluenight10-commits/gods_plan"
GITHUB_BRANCH       = "master"
DASHBOARD_FILE      = "TITAN_SYSTEM_v5.html"
TITAN_SYSTEM_URL    = os.getenv(
    "TITAN_SYSTEM_URL",
    "https://sobluenight10-commits.github.io/gods_plan/TITAN_SYSTEM_v5.html"
)

# ── Timing ────────────────────────────────────────────────────────────────────
TIMEZONE = "Europe/Berlin"

# ── DAILY BATTLE RHYTHM ───────────────────────────────────────────────────────
# Revised schedule — cost-optimized, 3 briefings/day on weekdays
DAILY_SCHEDULE = [
    ("07:00", "master_daily",  "🌅 Morning Brief → Blog + Macro + Scores + Orders"),
    ("15:30", "us_open",       "🇺🇸 US Open → Futures + Key Levels + Alerts"),
    ("22:30", "us_close",      "🏁 US Close → Daily Review + Tomorrow Prep"),
]

# ── WEEKLY OLYMPUS ────────────────────────────────────────────────────────────
WEEKLY_SCHEDULE = [
    ("08:00", "olympus_weekly", "🏛 Olympus Weekly → Full Matrix + Dashboard Push"),
]

# ── Data Storage ──────────────────────────────────────────────────────────────
DATA_FILE = os.path.join("data", "titan_k_data.json")

# ── Blog Source ───────────────────────────────────────────────────────────────
NAVER_BLOG_ID  = "ranto28"
NAVER_BLOG_URL = f"https://blog.naver.com/{NAVER_BLOG_ID}"
NAVER_RSS_URL  = f"https://rss.blog.naver.com/{NAVER_BLOG_ID}.xml"

# ── Exchange Rate ─────────────────────────────────────────────────────────────
DEFAULT_EUR_USD = 1.09   # fallback if live fetch fails
DEFAULT_USD_KRW = 1350   # fallback for Korean stocks

# ── Models ────────────────────────────────────────────────────────────────────
FAST_MODEL  = "gpt-4o-mini"   # all daily briefings
DEEP_MODEL  = "gpt-4o-mini"   # weekly olympus (kept mini for cost)

# ── Cost Guard ────────────────────────────────────────────────────────────────
DAILY_COST_LIMIT_USD  = 0.20
MONTHLY_COST_LIMIT_USD = 3.00


# ══════════════════════════════════════════════════════════════════════════════
# CIVILIZATION-SHIFT STOCK UNIVERSE — v5
# ══════════════════════════════════════════════════════════════════════════════

# Status values: "portfolio", "watchlist", "ipo_watch", "radar", "locked", "exit"
# Broker values: "TR", "Kiwoom_KR", "Kiwoom_US", "watchlist"

STOCKS = [

    # ── 1. INTELLIGENCE ── AGI · Quantum · Neural Interfaces · Advanced Memory
    {
        "ticker": "000660.KS", "name": "SK Hynix",
        "category": "INTELLIGENCE", "status": "portfolio", "broker": "Kiwoom_KR",
        "score": 10, "signal": "LEGEND", "action": "NEVER SELL",
        "thesis": "World #1 HBM3E. Every AI chip stack runs on SK Hynix memory. Backbone of AGI civilization.",
        "buy_price": 130500, "currency": "KRW",
        "stop": None, "target_1y": 1120000, "target_5y": 1520000,
        "forecast": {"1w": 965000, "1m": 995000, "6m": 1050000, "1y": 1120000, "5y": 1520000},
    },
    {
        "ticker": "PLTR", "name": "Palantir Technologies",
        "category": "INTELLIGENCE", "status": "portfolio", "broker": "TR",
        "score": 7, "signal": "HOLD", "action": "Hold + add dips",
        "thesis": "Maven Smart System = NATO war AI. Every escalation = direct revenue.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 171, "target_5y": 241,
        "forecast": {"1w": 144, "1m": 151, "6m": 160, "1y": 171, "5y": 241},
    },
    {
        "ticker": "IONQ", "name": "IonQ Quantum",
        "category": "INTELLIGENCE", "status": "portfolio", "broker": "Kiwoom_US",
        "score": 7, "signal": "HOLD", "action": "Limit $25 active (Kiwoom $400)",
        "thesis": "Quantum computing inflection 2026-2027. Near stop = max asymmetry.",
        "buy_price": None, "currency": "USD",
        "stop": 25, "target_1y": 44, "target_5y": 69,
        "forecast": {"1w": 35, "1m": 37, "6m": 40, "1y": 44, "5y": 69},
    },
    {
        "ticker": "NVDA", "name": "Nvidia Corporation",
        "category": "INTELLIGENCE", "status": "watchlist", "broker": "watchlist",
        "score": 10, "signal": "BUY", "action": "Enter on next correction. Must own.",
        "thesis": "GPU = printing press of AGI era. Single most Future-Fit stock on earth.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 175, "target_5y": 400,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": 175, "5y": 400},
    },
    {
        "ticker": "SMCI", "name": "Super Micro Computer",
        "category": "INTELLIGENCE", "status": "watchlist", "broker": "watchlist",
        "score": 6, "signal": "WATCH", "action": "Wait for accounting clarity before entry.",
        "thesis": "AI rack assembler. Irreplaceable in build-out phase. Volatile.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "MSFT", "name": "Microsoft / OpenAI proxy",
        "category": "INTELLIGENCE", "status": "watchlist", "broker": "watchlist",
        "score": 8, "signal": "WATCH", "action": "Best public proxy for OpenAI. Watch for entry.",
        "thesis": "Copilot in every enterprise. AGI commercialization engine.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 550, "target_5y": 900,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": 550, "5y": 900},
    },

    # ── 2. ENERGY ── Uranium · Fusion · Solid-State Batteries · Nuclear Renaissance
    {
        "ticker": "UEC", "name": "Uranium Energy Corp",
        "category": "ENERGY", "status": "portfolio", "broker": "TR",
        "score": 9, "signal": "HOLD", "action": "Add after earnings. Stop $11.50.",
        "thesis": "In-situ recovery = lowest cost uranium miner. Nuclear renaissance locked in.",
        "buy_price": None, "currency": "USD",
        "stop": 11.50, "target_1y": 20.50, "target_5y": 30.50,
        "forecast": {"1w": 15.50, "1m": 16.50, "6m": 18, "1y": 20.50, "5y": 30.50},
    },
    {
        "ticker": "URNM", "name": "Sprott Uranium Miners ETF",
        "category": "ENERGY", "status": "portfolio", "broker": "TR",
        "score": 8, "signal": "HOLD", "action": "Add in 2 weeks.",
        "thesis": "Uranium ETF basket. Nuclear renaissance is structural, not cyclical.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 85.50, "target_5y": 121,
        "forecast": {"1w": 70.50, "1m": 72.50, "6m": 79, "1y": 85.50, "5y": 121},
    },
    {
        "ticker": "CWEN", "name": "Clearway Energy",
        "category": "ENERGY", "status": "portfolio", "broker": "TR",
        "score": 5, "signal": "HOLD", "action": "No additions. Watch IRA policy risk.",
        "thesis": "Clean energy yield play. Stable but not high conviction.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 44.50, "target_5y": 58.50,
        "forecast": {"1w": 37.50, "1m": 38.50, "6m": 42, "1y": 44.50, "5y": 58.50},
    },
    {
        "ticker": "CCJ", "name": "Cameco Corporation",
        "category": "ENERGY", "status": "watchlist", "broker": "watchlist",
        "score": 9, "signal": "BUY", "action": "Set limit on pullback. Saudi Aramco of uranium.",
        "thesis": "Largest Western uranium producer. Nuclear renaissance = CCJ is unavoidable.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 65, "target_5y": 110,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": 65, "5y": 110},
    },
    {
        "ticker": "OKLO", "name": "Oklo Inc",
        "category": "ENERGY", "status": "watchlist", "broker": "watchlist",
        "score": 8, "signal": "BUY", "action": "Micro-nuclear for AI data centers. Sam Altman backed.",
        "thesis": "AI power crisis = Oklo's market. NRC license decision 2026.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "QS", "name": "QuantumScape",
        "category": "ENERGY", "status": "watchlist", "broker": "watchlist",
        "score": 6, "signal": "WATCH", "action": "Binary outcome. Small position only if entering.",
        "thesis": "Solid-state battery. VW + Gates backed. If it works → ends fossil fuel dominance.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },

    # ── 3. SPACE / LOGISTICS ── Orbital · Satellite · Lunar Economy · Urban Air
    {
        "ticker": "RKLB", "name": "Rocket Lab USA",
        "category": "SPACE", "status": "portfolio", "broker": "TR",
        "score": 6, "signal": "HOLD", "action": "Hold. Neutron rocket = next inflection.",
        "thesis": "Only vertically integrated small-launch company actually launching.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 87.50, "target_5y": 124,
        "forecast": {"1w": 70.50, "1m": 73.50, "6m": 80, "1y": 87.50, "5y": 124},
    },
    {
        "ticker": "ASTS", "name": "AST SpaceMobile",
        "category": "SPACE", "status": "watchlist", "broker": "watchlist",
        "score": 8, "signal": "BUY", "action": "Buy on consolidation. Extreme asymmetry.",
        "thesis": "Direct-to-phone satellite. AT&T + Verizon contracted. 3B unconnected humans.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "LUNR", "name": "Intuitive Machines",
        "category": "SPACE", "status": "watchlist", "broker": "watchlist",
        "score": 7, "signal": "WATCH", "action": "Watch IM-3 mission. Moon economy = signed contracts.",
        "thesis": "NASA's only contracted lunar delivery partner. IM-1 landed Feb 2024.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "xAI", "name": "xAI Corp — Grok / Colossus",
        "category": "SPACE", "status": "ipo_watch", "broker": "watchlist",
        "score": 9, "signal": "IPO READY", "action": "Buy IPO day. S-1 expected H1 2026.",
        "thesis": "Colossus = world's largest AI cluster (100K H100s). Grok + SpaceX + Tesla pipelines.",
        "buy_price": None, "currency": "USD",
        "ipo_expected": "H2 2026", "valuation": "50B+",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "ACHR", "name": "Archer Aviation",
        "category": "SPACE", "status": "watchlist", "broker": "watchlist",
        "score": 6, "signal": "WATCH", "action": "Small position only. FAA certification = inflection.",
        "thesis": "Urban air mobility. United Airlines invested. Abu Dhabi contracted.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },

    # ── 4. BIO-ENGINEERING ── CRISPR · Base Editing · Longevity · AI Drug Discovery
    {
        "ticker": "CRSP", "name": "CRISPR Therapeutics",
        "category": "BIO", "status": "portfolio", "broker": "TR",
        "score": 5, "signal": "CAUTION", "action": "Wait below $40. Mar 26 catalyst.",
        "thesis": "Gene editing platform. $350M dilution overhang — wait for stabilization.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 50, "target_5y": 70,
        "forecast": {"1w": 40, "1m": 42, "6m": 46, "1y": 50, "5y": 70},
        "catalyst": "Earnings Mar 26",
    },
    {
        "ticker": "NTLA", "name": "Intellia Therapeutics",
        "category": "BIO", "status": "portfolio", "broker": "TR",
        "score": 6, "signal": "HOLD", "action": "Limit $10 active (TR €200).",
        "thesis": "In-vivo gene editing. Pairs with CRSP for full gene editing basket.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 21.50, "target_5y": 36.50,
        "forecast": {"1w": 14.70, "1m": 15.70, "6m": 18, "1y": 21.50, "5y": 36.50},
    },
    {
        "ticker": "BEAM", "name": "Beam Therapeutics",
        "category": "BIO", "status": "watchlist", "broker": "watchlist",
        "score": 8, "signal": "BUY", "action": "Set limit on weakness. David Liu founded.",
        "thesis": "Base editing = next-gen CRISPR. Strictly more precise. Phase 1/2 data 2026.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "RXRX", "name": "Recursion Pharma",
        "category": "BIO", "status": "watchlist", "broker": "watchlist",
        "score": 7, "signal": "WATCH", "action": "NVIDIA partnership. Watch pipeline readout.",
        "thesis": "AI drug discovery. Compresses 10yr development to 18 months.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "EDIT", "name": "Editas Medicine",
        "category": "BIO", "status": "watchlist", "broker": "watchlist",
        "score": 5, "signal": "WATCH", "action": "Third gene editing platform. Completes trio.",
        "thesis": "CRSP + NTLA + EDIT = full gene editing basket. Diversifies platform risk.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },

    # ── 5. ROBOTICS ── Humanoids · Autonomous Manufacturing · Defense Drones
    {
        "ticker": "272210.KS", "name": "Hanwha Systems",
        "category": "ROBOTICS", "status": "portfolio", "broker": "Kiwoom_KR",
        "score": 10, "signal": "LEGEND", "action": "NEVER SELL",
        "thesis": "Korea's premier autonomous weapons + propulsion. War is permanent demand. +820%.",
        "buy_price": 16418, "currency": "KRW",
        "stop": None, "target_1y": 183500, "target_5y": 253500,
        "forecast": {"1w": 158500, "1m": 163500, "6m": 175000, "1y": 183500, "5y": 253500},
    },
    {
        "ticker": "KTOS", "name": "Kratos Defense",
        "category": "ROBOTICS", "status": "portfolio", "broker": "Kiwoom_US",
        "score": 9, "signal": "HOLD", "action": "Add at $80 (Kiwoom $400). Stop $75.",
        "thesis": "Defense drones deployed in live conflict = real revenue. $1.5T DoD budget.",
        "buy_price": None, "currency": "USD",
        "stop": 75, "target_1y": 99.50, "target_5y": 130,
        "forecast": {"1w": 87.50, "1m": 89.50, "6m": 94, "1y": 99.50, "5y": 130},
    },
    {
        "ticker": "AVAV", "name": "AeroVironment",
        "category": "ROBOTICS", "status": "portfolio", "broker": "Kiwoom_US",
        "score": 6, "signal": "HOLD", "action": "Do not add. Reassess Q4 earnings.",
        "thesis": "Switchblade still deployed in conflict. Score 8→6 after earnings miss.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 205, "target_5y": 250,
        "forecast": {"1w": 180, "1m": 185, "6m": 195, "1y": 205, "5y": 250},
    },
    {
        "ticker": "TSLA", "name": "Tesla — Optimus thesis",
        "category": "ROBOTICS", "status": "watchlist", "broker": "watchlist",
        "score": 8, "signal": "WATCH", "action": "NOT the car thesis. Watch for dip entry.",
        "thesis": "Optimus humanoid = most underdiscussed asset. Labor company, not car company.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "ESLT", "name": "Elbit Systems",
        "category": "ROBOTICS", "status": "watchlist", "broker": "watchlist",
        "score": 8, "signal": "BUY", "action": "Set limit. Battle-proven autonomous defense.",
        "thesis": "Israeli autonomous defense. Western hemisphere Hanwha. IDF contract cycle.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "FigureAI", "name": "Figure AI Inc",
        "category": "ROBOTICS", "status": "ipo_watch", "broker": "watchlist",
        "score": 9, "signal": "IPO WATCH", "action": "BMW factory deployment live. Watch IPO filing.",
        "thesis": "Most advanced humanoid in production. OpenAI partnership. $40B private valuation.",
        "buy_price": None, "currency": "USD",
        "ipo_expected": "2026/2027",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },

    # ── 6. INFRASTRUCTURE ── Photonics · Power · Semiconductor Equipment · Water
    {
        "ticker": "COHR", "name": "Coherent Corp",
        "category": "INFRASTRUCTURE", "status": "portfolio", "broker": "TR",
        "score": 8, "signal": "HOLD", "action": "Hold. NVIDIA supply deal locked.",
        "thesis": "800G transceivers = photonics backbone of all AI data center networks.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 315, "target_5y": 425,
        "forecast": {"1w": 275, "1m": 280, "6m": 298, "1y": 315, "5y": 425},
    },
    {
        "ticker": "FCX", "name": "Freeport-McMoRan",
        "category": "INFRASTRUCTURE", "status": "portfolio", "broker": "Kiwoom_US",
        "score": 7, "signal": "REDUCE", "action": "Kiwoom stop $54.50. TR already sold.",
        "thesis": "Copper = AI wiring metal. Long term intact, tactical reduce now.",
        "buy_price": None, "currency": "USD",
        "stop": 54.50, "target_1y": 81, "target_5y": 107,
        "forecast": {"1w": 68.50, "1m": 70.50, "6m": 75, "1y": 81, "5y": 107},
    },
    {
        "ticker": "TMO", "name": "Thermo Fisher Scientific",
        "category": "INFRASTRUCTURE", "status": "portfolio", "broker": "TR",
        "score": 6, "signal": "HOLD", "action": "Hold. Biotech infrastructure enabler.",
        "thesis": "Life science instruments. Every gene editing lab needs TMO equipment.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": 601, "target_5y": 801,
        "forecast": {"1w": 506, "1m": 521, "6m": 560, "1y": 601, "5y": 801},
    },
    {
        "ticker": "VRT", "name": "Vertiv Holdings",
        "category": "INFRASTRUCTURE", "status": "watchlist", "broker": "watchlist",
        "score": 9, "signal": "BUY", "action": "Add immediately. This is overdue.",
        "thesis": "Every AI data center needs power + cooling. Vertiv supplies both. +20% revenue YoY.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "AMAT", "name": "Applied Materials",
        "category": "INFRASTRUCTURE", "status": "watchlist", "broker": "watchlist",
        "score": 8, "signal": "BUY", "action": "Cannot build chips without AMAT machines.",
        "thesis": "Semiconductor manufacturing equipment. SK Hynix partner. Unavoidable.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "AWK", "name": "American Water Works",
        "category": "INFRASTRUCTURE", "status": "watchlist", "broker": "watchlist",
        "score": 7, "signal": "WATCH", "action": "Water = scarcest resource of 2030s.",
        "thesis": "Monopoly utility. Pricing power. Infrastructure no civilization can replace.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },

    # ── GLOBAL ISSUE RADAR ── Rotating · Current: Food Security / War Fertilizer
    {
        "ticker": "NTR", "name": "Nutrien Ltd",
        "category": "RADAR", "status": "radar", "broker": "watchlist",
        "score": 8, "signal": "BUY", "action": "Priceless entry window. Food = national security.",
        "thesis": "World's largest potash producer. War disrupted 40% global supply.",
        "radar_theme": "Food Security / War Fertilizer Premium",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "MOS", "name": "Mosaic Company",
        "category": "RADAR", "status": "radar", "broker": "watchlist",
        "score": 7, "signal": "WATCH", "action": "Higher volatility = higher upside vs NTR.",
        "thesis": "Second largest fertilizer producer. Same thesis as NTR.",
        "radar_theme": "Food Security / War Fertilizer Premium",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
    {
        "ticker": "DE", "name": "John Deere",
        "category": "RADAR", "status": "radar", "broker": "watchlist",
        "score": 7, "signal": "WATCH", "action": "Precision autonomous agriculture.",
        "thesis": "Food scarcity demands yield maximization. Bridges ROBOTICS + RADAR.",
        "radar_theme": "Food Security / War Fertilizer Premium",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },

    # ── LOCKED ── TR promotional gift
    {
        "ticker": "MC.PA", "name": "LVMH",
        "category": "LOCKED", "status": "locked", "broker": "TR",
        "score": 8, "signal": "LOCKED", "action": "Cannot sell. Track only.",
        "thesis": "TR gift. Locked ~1 year from first transaction. Generational brand basket.",
        "buy_price": None, "currency": "EUR",
        "stop": None, "target_1y": 602, "target_5y": 802,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": 602, "5y": 802},
    },

    # ── EXIT QUEUE ── Legacy positions not aligned with civilization thesis
    {
        "ticker": "HUYA", "name": "HUYA Inc",
        "category": "EXIT", "status": "exit", "broker": "Kiwoom_US",
        "score": 2, "signal": "EXIT NOW", "action": "All scenarios → sell. No exceptions.",
        "thesis": "BROKEN. China ADR risk. No thesis. -79% underwater.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
        "exit_deadline": "2026-03-17",
    },
    {
        "ticker": "GEVO", "name": "Gevo Inc",
        "category": "EXIT", "status": "exit", "broker": "Kiwoom_US",
        "score": 2, "signal": "EXIT MAR 26", "action": "Hold ONLY until Mar 26. Then exit all scenarios.",
        "thesis": "BROKEN. -83% underwater. Dead capital. Redeploy into conviction.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
        "exit_deadline": "2026-03-26",
    },
    {
        "ticker": "IAU", "name": "iShares Gold ETF",
        "category": "EXIT", "status": "exit", "broker": "TR",
        "score": 3, "signal": "EXIT SOON", "action": "Exit on next strength. Redeploy into conviction.",
        "thesis": "Gold is a relic hedge. Not a civilization-shift asset.",
        "buy_price": None, "currency": "USD",
        "stop": None, "target_1y": None, "target_5y": None,
        "forecast": {"1w": None, "1m": None, "6m": None, "1y": None, "5y": None},
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_portfolio_tickers():
    """Return tickers of live portfolio positions only."""
    return [s["ticker"] for s in STOCKS if s["status"] == "portfolio"]

def get_all_tickers():
    """Return all tickers except IPO-watch and private companies."""
    skip = {"xAI", "FigureAI"}
    return [s["ticker"] for s in STOCKS if s["ticker"] not in skip]

def get_tradeable_tickers():
    """Return tickers that have live market prices."""
    skip = {"xAI", "FigureAI"}
    return [s["ticker"] for s in STOCKS
            if s["status"] in ("portfolio", "watchlist", "radar", "locked", "exit")
            and s["ticker"] not in skip]

def get_stocks_by_category(category: str):
    return [s for s in STOCKS if s["category"] == category]

def get_stock(ticker: str):
    for s in STOCKS:
        if s["ticker"] == ticker:
            return s
    return None

def get_exit_queue():
    return [s for s in STOCKS if s["status"] == "exit"]

def get_buy_signals():
    return [s for s in STOCKS if s["signal"] in ("BUY", "LEGEND")]


# ══════════════════════════════════════════════════════════════════════════════
# MACRO ENGINE WEIGHTS
# ══════════════════════════════════════════════════════════════════════════════

WEIGHTS = {
    "VIX": 0.08, "VVIX": 0.03, "SKEW": 0.03, "Put/Call": 0.04, "VIX_Term": 0.04, "MOVE": 0.03,
    "US10Y": 0.05, "US2Y": 0.03, "Yield_Curve": 0.04, "DXY": 0.04, "Fed_Funds": 0.04,
    "SPX": 0.04, "NDX": 0.03, "SOX": 0.05, "RSP_SPY": 0.03, "Adv_Dec": 0.03, "52W_HL": 0.02,
    "Gold": 0.04, "Oil": 0.03, "Copper": 0.03, "Uranium": 0.03, "Nat_Gas": 0.02,
    "HYG_Spread": 0.03, "IG_Spread": 0.02, "TED_Spread": 0.02, "LIBOR_OIS": 0.03,
    "AAII_Bull": 0.02, "CNN_FG": 0.03, "Geopolitical": 0.03, "BTC": 0.02,
}

VIX_REGIMES = {
    "CALM":   {"range": (0, 15),   "deploy_pct": 0,   "label": "HOLD CASH"},
    "NORMAL": {"range": (15, 20),  "deploy_pct": 25,  "label": "SELECTIVE"},
    "FEAR":   {"range": (20, 30),  "deploy_pct": 50,  "label": "DEPLOY 50%"},
    "CRISIS": {"range": (30, 100), "deploy_pct": 100, "label": "FULL DEPLOY"},
}

SCORECARD_FILTERS = [
    "F1: Analyst Consensus",
    "F2: Thesis Intact",
    "F3: Macro/War Alignment",
    "F4: Earnings Trajectory",
    "F5: Position Size vs Conviction",
]

# ── Earnings Calendar ─────────────────────────────────────────────────────────
from datetime import date as _date
EARNINGS_CALENDAR = [
    e for e in [
        {"ticker": "CRSP", "date": "2026-03-26", "importance": "CATALYST — gene editing"},
        {"ticker": "GEVO", "date": "2026-03-26", "importance": "EXIT TRIGGER"},
        {"ticker": "FCX",  "date": "2026-04-16", "importance": "REVIEW"},
    ]
    if e["date"] >= str(_date.today())
]

TITAN_BOT_TOKEN = ""  # loaded from .env
