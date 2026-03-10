"""
🔱 titan_K v2 — Market Data Engine
Fetches the 30-indicator composite score and individual stock data via yfinance.
"""
import logging
from typing import Dict, Tuple

import yfinance as yf

from config import WEIGHTS, VIX_REGIMES

logger = logging.getLogger("titan_k.market_data")

# ── Ticker Mapping for 30 Indicators ─────────────────────────────────────────
INDICATOR_TICKERS = {
    # Fear & Volatility
    "VIX":       {"ticker": "^VIX",       "invert": True,  "thresholds": (15, 20, 30)},
    "VVIX":      {"ticker": "^VVIX",      "invert": True,  "thresholds": (80, 100, 120)},
    "SKEW":      {"ticker": "^SKEW",      "invert": True,  "thresholds": (120, 135, 150)},
    "Put/Call":  {"ticker": None,          "invert": True,  "thresholds": (0.7, 0.9, 1.2)},  # manual
    "VIX_Term":  {"ticker": None,          "invert": False, "thresholds": (0.85, 0.95, 1.05)},  # VIX/VIX3M
    "MOVE":      {"ticker": "^MOVE",       "invert": True,  "thresholds": (80, 110, 140)},

    # Rates & Liquidity
    "US10Y":     {"ticker": "^TNX",        "invert": True,  "thresholds": (3.5, 4.2, 4.8)},
    "US2Y":      {"ticker": "^IRX",        "invert": True,  "thresholds": (3.0, 4.0, 5.0)},
    "Yield_Curve": {"ticker": None,        "invert": False, "thresholds": (-0.5, 0, 0.5)},  # 10Y-2Y
    "DXY":       {"ticker": "DX-Y.NYB",   "invert": True,  "thresholds": (100, 104, 108)},
    "Fed_Funds": {"ticker": None,          "invert": True,  "thresholds": (3.0, 4.5, 5.5)},  # manual

    # Equity Internals
    "SPX":       {"ticker": "^GSPC",       "invert": False, "thresholds": None},
    "NDX":       {"ticker": "^NDX",        "invert": False, "thresholds": None},
    "SOX":       {"ticker": "^SOX",        "invert": False, "thresholds": None},
    "RSP_SPY":   {"ticker": None,          "invert": False, "thresholds": None},  # RSP/SPY ratio
    "Adv_Dec":   {"ticker": None,          "invert": False, "thresholds": None},  # manual
    "52W_HL":    {"ticker": None,          "invert": False, "thresholds": None},  # manual

    # Commodities & Macro
    "Gold":      {"ticker": "GC=F",        "invert": False, "thresholds": None},
    "Oil":       {"ticker": "CL=F",        "invert": False, "thresholds": (60, 75, 90)},
    "Copper":    {"ticker": "HG=F",        "invert": False, "thresholds": None},
    "Uranium":   {"ticker": "URA",         "invert": False, "thresholds": None},  # ETF proxy
    "Nat_Gas":   {"ticker": "NG=F",        "invert": True,  "thresholds": (2.5, 3.5, 5.0)},

    # Credit & Risk
    "HYG_Spread": {"ticker": "HYG",       "invert": True,  "thresholds": None},
    "IG_Spread":  {"ticker": "LQD",       "invert": True,  "thresholds": None},
    "TED_Spread": {"ticker": None,         "invert": True,  "thresholds": None},  # manual
    "LIBOR_OIS":  {"ticker": None,         "invert": True,  "thresholds": None},  # manual

    # Geopolitical & Sentiment
    "AAII_Bull":  {"ticker": None,         "invert": False, "thresholds": (25, 35, 45)},  # manual
    "CNN_FG":     {"ticker": None,         "invert": False, "thresholds": (25, 45, 60)},  # manual
    "Geopolitical": {"ticker": None,       "invert": True,  "thresholds": None},  # manual
    "BTC":        {"ticker": "BTC-USD",    "invert": False, "thresholds": None},
}


def fetch_market_snapshot() -> Dict:
    """
    Fetch current values for all 30 indicators.
    Returns dict: {indicator_name: {value, change_pct, signal}}
    """
    snapshot = {}
    
    # Batch fetch all available tickers
    fetchable = {
        name: info["ticker"]
        for name, info in INDICATOR_TICKERS.items()
        if info["ticker"] is not None
    }
    
    tickers_str = " ".join(fetchable.values())
    logger.info(f"Fetching {len(fetchable)} indicators via yfinance...")
    
    try:
        data = yf.download(tickers_str, period="5d", interval="1d", group_by="ticker", progress=False)
    except Exception as e:
        logger.error(f"yfinance batch download failed: {e}")
        data = None
    
    for name, ticker in fetchable.items():
        info = INDICATOR_TICKERS[name]
        try:
            if data is not None and len(fetchable) > 1:
                # Multi-ticker download
                if ticker in data.columns.get_level_values(0):
                    col = data[ticker]["Close"].dropna()
                else:
                    col = _fetch_single(ticker)
            else:
                col = _fetch_single(ticker)
            
            if col is not None and len(col) >= 2:
                current = float(col.iloc[-1])
                prev = float(col.iloc[-2])
                change_pct = round(((current - prev) / prev) * 100, 2) if prev != 0 else 0
                
                signal = _generate_signal(name, current, change_pct, info)
                
                snapshot[name] = {
                    "value": round(current, 2),
                    "change_pct": change_pct,
                    "signal": signal,
                }
            elif col is not None and len(col) == 1:
                current = float(col.iloc[-1])
                snapshot[name] = {
                    "value": round(current, 2),
                    "change_pct": 0,
                    "signal": "Data limited",
                }
            else:
                snapshot[name] = {"value": "N/A", "change_pct": 0, "signal": "No data"}
                
        except Exception as e:
            logger.warning(f"Failed to fetch {name} ({ticker}): {e}")
            snapshot[name] = {"value": "N/A", "change_pct": 0, "signal": "Error"}
    
    # Add manual/computed indicators with placeholder
    for name, info in INDICATOR_TICKERS.items():
        if info["ticker"] is None and name not in snapshot:
            snapshot[name] = {"value": "Manual", "change_pct": 0, "signal": "Requires manual input"}
    
    # Compute VIX Term Structure if possible
    if "VIX" in snapshot and isinstance(snapshot["VIX"]["value"], (int, float)):
        vix_val = snapshot["VIX"]["value"]
        # Estimate VIX term (VIX / VIX3M ~ 0.85-1.1 range)
        snapshot["VIX_Term"] = {
            "value": "~0.95",
            "change_pct": 0,
            "signal": "Contango" if vix_val < 25 else "Backwardation — fear elevated",
        }
    
    # Compute Yield Curve if we have both
    if (isinstance(snapshot.get("US10Y", {}).get("value"), (int, float)) and
        isinstance(snapshot.get("US2Y", {}).get("value"), (int, float))):
        spread = snapshot["US10Y"]["value"] - snapshot["US2Y"]["value"]
        snapshot["Yield_Curve"] = {
            "value": round(spread, 2),
            "change_pct": 0,
            "signal": "Normal" if spread > 0 else "INVERTED — recession signal",
        }
    
    return snapshot


def _fetch_single(ticker: str):
    """Fetch a single ticker's close prices."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d", interval="1d")
        if hist is not None and len(hist) > 0:
            return hist["Close"]
    except Exception as e:
        logger.warning(f"Single fetch failed for {ticker}: {e}")
    return None


def _generate_signal(name: str, value: float, change_pct: float, info: dict) -> str:
    """Generate a human-readable signal for an indicator."""
    thresholds = info.get("thresholds")
    invert = info.get("invert", False)
    
    if thresholds:
        low, mid, high = thresholds
        if invert:
            if value >= high:
                return f"EXTREME — deploy zone"
            elif value >= mid:
                return f"Elevated — watch"
            elif value >= low:
                return f"Normal range"
            else:
                return f"Low — caution (complacency)"
        else:
            if value >= high:
                return f"Strong — bullish momentum"
            elif value >= mid:
                return f"Normal"
            elif value >= low:
                return f"Weakening"
            else:
                return f"Weak — bearish"
    
    # Generic signal based on change
    if abs(change_pct) < 0.3:
        return "Flat"
    elif change_pct > 2:
        return f"Sharp move +{change_pct}%"
    elif change_pct < -2:
        return f"Sharp drop {change_pct}%"
    elif change_pct > 0:
        return f"Up {change_pct}%"
    else:
        return f"Down {change_pct}%"


def calculate_titan_k_index(snapshot: Dict, weights: Dict) -> int:
    """
    Calculate the composite titan_K index (0-100).
    Higher = more favorable for deployment.
    """
    total_score = 0
    total_weight = 0
    
    for indicator, weight in weights.items():
        data = snapshot.get(indicator, {})
        value = data.get("value")
        change_pct = data.get("change_pct", 0)
        
        if not isinstance(value, (int, float)):
            continue
        
        info = INDICATOR_TICKERS.get(indicator, {})
        thresholds = info.get("thresholds")
        invert = info.get("invert", False)
        
        # Score each indicator 0-100
        if thresholds:
            low, mid, high = thresholds
            if invert:
                # Higher value = more fear = better for buying
                if value >= high:
                    score = 90
                elif value >= mid:
                    score = 60
                elif value >= low:
                    score = 40
                else:
                    score = 15  # Complacent market = caution
            else:
                if value >= high:
                    score = 80
                elif value >= mid:
                    score = 55
                elif value >= low:
                    score = 35
                else:
                    score = 20
        else:
            # Use change direction as proxy
            if invert:
                score = 60 + min(change_pct * 5, 30)  # Rising fear = good for buyers
            else:
                score = 50 + min(change_pct * 3, 30)
        
        score = max(0, min(100, score))
        total_score += score * weight
        total_weight += weight
    
    if total_weight == 0:
        return 50  # neutral
    
    return round(total_score / total_weight)


def get_vix_regime(vix_value: float) -> Tuple[str, int, str]:
    """Determine current VIX regime. Returns (regime_name, deploy_pct, label)."""
    for regime, config in VIX_REGIMES.items():
        low, high = config["range"]
        if low <= vix_value < high:
            return regime, config["deploy_pct"], config["label"]
    return "CRISIS", 100, "FULL DEPLOY"


def fetch_stock_prices(tickers: list) -> Dict:
    """Fetch current prices and daily changes for a list of tickers.
    Uses batch download first, then individual fallback for any missing."""
    results = {}
    
    if not tickers:
        return results
    
    tickers_str = " ".join(tickers)
    
    try:
        data = yf.download(tickers_str, period="5d", interval="1d", progress=False)
    except Exception as e:
        logger.error(f"Stock price batch download failed: {e}")
        data = None
    
    # Parse batch results
    for ticker in tickers:
        try:
            if data is not None and len(tickers) > 1:
                if ticker in data.columns.get_level_values(0):
                    close = data[ticker]["Close"].dropna()
                else:
                    close = None
            elif data is not None and len(tickers) == 1:
                close = data["Close"].dropna()
            else:
                close = None
            
            if close is not None and len(close) >= 2:
                current = float(close.iloc[-1])
                prev = float(close.iloc[-2])
                change_pct = round(((current - prev) / prev) * 100, 2)
                results[ticker] = {
                    "price": round(current, 2),
                    "change_pct": change_pct,
                    "prev_close": round(prev, 2),
                }
            elif close is not None and len(close) == 1:
                results[ticker] = {
                    "price": round(float(close.iloc[-1]), 2),
                    "change_pct": 0,
                    "prev_close": round(float(close.iloc[-1]), 2),
                }
        except Exception as e:
            logger.warning(f"Batch parse failed for {ticker}: {e}")
    
    # Individual fallback for any tickers that batch missed
    missing = [t for t in tickers if t not in results]
    if missing:
        logger.info(f"Fetching {len(missing)} missing tickers individually: {missing}")
        for ticker in missing:
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="5d")
                if hist is not None and len(hist) >= 2:
                    close = hist["Close"].dropna()
                    current = float(close.iloc[-1])
                    prev = float(close.iloc[-2])
                    change_pct = round(((current - prev) / prev) * 100, 2)
                    results[ticker] = {
                        "price": round(current, 2),
                        "change_pct": change_pct,
                        "prev_close": round(prev, 2),
                    }
                elif hist is not None and len(hist) == 1:
                    results[ticker] = {
                        "price": round(float(hist["Close"].iloc[-1]), 2),
                        "change_pct": 0,
                        "prev_close": round(float(hist["Close"].iloc[-1]), 2),
                    }
                else:
                    logger.warning(f"No data returned for {ticker}")
            except Exception as e:
                logger.warning(f"Individual fetch failed for {ticker}: {e}")
    
    return results


def fetch_fx_rate() -> float:
    """Fetch EUR/USD exchange rate."""
    try:
        t = yf.Ticker("EURUSD=X")
        hist = t.history(period="1d")
        if hist is not None and len(hist) > 0:
            return round(float(hist["Close"].iloc[-1]), 4)
    except Exception as e:
        logger.warning(f"FX rate fetch failed: {e}")
    
    from config import DEFAULT_EUR_USD
    return DEFAULT_EUR_USD
