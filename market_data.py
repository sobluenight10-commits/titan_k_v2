import yfinance as yf
import requests
from datetime import datetime

# Map titan_K indicators to yfinance tickers where possible
TICKER_MAP = {
    "SOX":    "^SOX",
    "VIX":    "^VIX",
    "DXY":    "DX-Y.NYB",
    "TNX":    "^TNX",
    "BCOM":   "^BCOM",
    "WTI":    "CL=F",
    "SPXEW":  "RSP",
    "RUT":    "^RUT",
    "BTC":    "BTC-USD",
    "Gold":   "GC=F",
    "Copper": "HG=F",
    "Nikkei": "^N225",
    "FANG":   "NYFANG",
    "Uranium":"URA",
    "MSCI_EM":"EEM",
}

def fetch_market_snapshot() -> dict:
    """
    Fetch current values for all titan_K indicators.
    Returns dict of indicator -> {value, change_pct, signal}
    """
    snapshot = {}

    for name, ticker in TICKER_MAP.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if hist.empty:
                snapshot[name] = {"value": None, "change_pct": None, "signal": "N/A"}
                continue
            current = float(hist["Close"].iloc[-1])
            prev    = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
            chg     = round((current - prev) / prev * 100, 2)
            signal  = _signal(name, current, chg)
            snapshot[name] = {
                "value":      round(current, 2),
                "change_pct": chg,
                "signal":     signal
            }
        except Exception as e:
            snapshot[name] = {"value": None, "change_pct": None, "signal": "N/A"}

    # Fill remaining indicators with neutral placeholder
    all_indicators = [
        "PMI","GPR","FearGreed","HYSpread","InstRisk","BDI","BDI2",
        "CPI","PPI","UMich","Housing","FedRate","ECBRate","TradeBalance",
        "Jobless","HICP","DataCenter"
    ]
    for ind in all_indicators:
        if ind not in snapshot:
            snapshot[ind] = {"value": None, "change_pct": None, "signal": "Manual update needed"}

    return snapshot


def calculate_titan_k_index(snapshot: dict, weights: dict) -> float:
    """
    Calculate titan_K composite score (0-100).
    Normalizes each indicator to 0-100 scale then weights.
    """
    from config import WEIGHTS
    total, w_sum = 0.0, 0.0

    for ind, weight in WEIGHTS.items():
        data = snapshot.get(ind, {})
        val  = data.get("value")
        chg  = data.get("change_pct")

        if val is None:
            normalized = 50.0  # neutral if no data
        else:
            # Normalize change_pct to 0-100 (0% change = 50, +5% = ~75, -5% = ~25)
            normalized = 50.0 + (chg or 0) * 5
            normalized = max(0, min(100, normalized))

            # Invert for fear indicators (high VIX = bad = low score)
            if ind in ["VIX", "HYSpread", "Jobless", "CPI", "PPI"]:
                normalized = 100 - normalized

        total += normalized * weight
        w_sum += weight

    score = round(total / w_sum, 1) if w_sum > 0 else 50.0
    return score


def _signal(name: str, value: float, chg: float) -> str:
    """Generate human-readable signal for each indicator"""
    if name == "VIX":
        if value > 30: return "🔴 FEAR — Deploy cash"
        if value > 20: return "🟡 Caution"
        return "🟢 Calm market"
    if name == "BTC":
        if chg < -5: return "⚠️ Tech drop likely in 24h"
        if chg > 5:  return "🟢 Risk-on sentiment"
        return "🟡 Neutral"
    if name == "Gold":
        if chg > 1:  return "⚠️ Chaos hedge active"
        return "🟢 Stable"
    if name == "TNX":
        if value > 4.5: return "🔴 High gravity — growth stocks under pressure"
        return "🟢 Manageable yield"
    if name == "SOX":
        if chg > 2:  return "🟢 AI/Chip bull signal"
        if chg < -2: return "🔴 Chip weakness"
        return "🟡 Neutral"
    if chg > 2:  return "🟢 Bullish"
    if chg < -2: return "🔴 Bearish"
    return "🟡 Neutral"
