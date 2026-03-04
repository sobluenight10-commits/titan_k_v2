import os
from dotenv import load_dotenv
load_dotenv()

# === API KEYS ===
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# === BLOG ===
BLOG_ID  = "ranto28"
BLOG_RSS = "https://rss.blog.naver.com/ranto28.xml"
BLOG_URL = "https://m.blog.naver.com/ranto28"

# === SCHEDULE ===
DAILY_TIME = "07:00"
TIMEZONE   = "Europe/Berlin"

# === FUTURE-STATE MATRIX ===
FUTURE_STATE = {
    "Intelligence":    ["AGI","Quantum","Neural","AI","반도체","양자","칩","semiconductor","nvidia","palantir"],
    "Energy":          ["Fusion","Battery","Hydrogen","Perovskite","Uranium","Solar","배터리","수소","원자력","태양광","희토류","rare earth"],
    "Space/Logistics": ["Space","Rocket","Hypersonic","Orbital","우주","발사체","SpaceX"],
    "Bio-Engineering": ["CRISPR","Longevity","Organoid","Lab-Grown","바이오","신약","유전자","오가노이드","제약"],
    "Robotics":        ["Robot","Humanoid","Autonomous","로봇","자율주행","Tesla","Figure"]
}

# === titan_K 30-INDEX WEIGHTS (must sum to 1.0) ===
# Tier 1 — The Pulse (0.35 total)
# Tier 2 — War & Energy (0.25 total)
# Tier 3 — Sentiment & Flow (0.22 total)
# Tier 4 — Macro Foundation (0.18 total)
WEIGHTS = {
    # Tier 1
    "SOX":            0.09,
    "VIX":            0.08,
    "DXY":            0.06,
    "TNX":            0.07,
    "BCOM":           0.05,
    # Tier 2
    "WTI":            0.05,
    "PMI":            0.04,
    "GPR":            0.04,
    "Uranium":        0.06,
    "Copper":         0.04,
    "DataCenter":     0.02,
    "BDI":            0.02,  # moved here, was missing
    # Tier 3
    "FearGreed":      0.04,
    "SPXEW":          0.03,
    "RUT":            0.03,
    "HYSpread":       0.04,
    "BTC":            0.02,
    "InstRisk":       0.04,
    "BDI2":           0.02,
    # Tier 4
    "CPI":            0.03,
    "PPI":            0.02,
    "UMich":          0.02,
    "Housing":        0.01,
    "FedRate":        0.03,
    "ECBRate":        0.02,
    "MSCI_EM":        0.01,
    "TradeBalance":   0.01,
    "Jobless":        0.01,
    "Nikkei":         0.01,
    "Gold":           0.01,
    "HICP":           0.01,
    "FANG":           0.01,
}

DATA_FILE = "data/titan_k_data.json"
