import yfinance as yf
import pandas as pd
from datetime import datetime

# ── Your Actual Portfolio ─────────────────────────────────────────────────────

KIWOOM_PORTFOLIO = [
    {
        "name": "SK하이닉스 (SK Hynix)",
        "ticker": "000660.KS",
        "broker": "Kiwoom (KR)",
        "shares": 6,
        "avg_buy_price_krw": 130500,
        "currency": "KRW",
        "future_state_category": "Intelligence",
        "thesis": "World's leading HBM memory chip supplier for AI/NVIDIA. Core AI infrastructure play."
    },
    {
        "name": "한화시스템 (Hanwha Systems)",
        "ticker": "272210.KS",
        "broker": "Kiwoom (KR)",
        "shares": 158,
        "avg_buy_price_krw": 16418,
        "currency": "KRW",
        "future_state_category": "Space/Logistics",
        "thesis": "Korean defense + space tech leader. Satellite, radar, UAV systems. Paradigm shift play."
    },
]

TRADE_REPUBLIC_PORTFOLIO = [
    {
        "name": "Sprott Uranium Miners ETF",
        "ticker": "URNM",
        "broker": "Trade Republic (DE)",
        "shares": None,
        "avg_buy_price_eur": 295.19,
        "currency": "EUR",
        "future_state_category": "Energy",
        "thesis": "Uranium miners ETF. Nuclear energy renaissance driven by AI data center power demand."
    },
    {
        "name": "Coherent Corp",
        "ticker": "COHR",
        "broker": "Trade Republic (DE)",
        "shares": None,
        "avg_buy_price_eur": 254.53,
        "currency": "EUR",
        "future_state_category": "Intelligence",
        "thesis": "Optical components for AI data centers and semiconductor manufacturing. High conviction."
    },
    {
        "name": "Freeport-McMoRan",
        "ticker": "FCX",
        "broker": "Trade Republic (DE)",
        "shares": None,
        "avg_buy_price_eur": 247.60,
        "currency": "EUR",
        "future_state_category": "Energy",
        "thesis": "World's largest copper miner. Essential for green energy transition and AI infrastructure."
    },
    {
        "name": "Rocket Lab USA",
        "ticker": "RKLB",
        "broker": "Trade Republic (DE)",
        "shares": None,
        "avg_buy_price_eur": 152.38,
        "currency": "EUR",
        "future_state_category": "Space/Logistics",
        "thesis": "Small satellite launch leader. Neutron rocket development. Space economy infrastructure."
    },
    {
        "name": "LVMH Moët Hennessy",
        "ticker": "MC.PA",
        "broker": "Trade Republic (DE)",
        "shares": None,
        "avg_buy_price_eur": 41.52,
        "currency": "EUR",
        "future_state_category": "None",
        "thesis": "Luxury goods giant. Defensive position but facing China slowdown headwinds. Review needed."
    },
    {
        "name": "Clearway Energy",
        "ticker": "CWEN",
        "broker": "Trade Republic (DE)",
        "shares": None,
        "avg_buy_price_eur": 33.04,
        "currency": "EUR",
        "future_state_category": "Energy",
        "thesis": "Renewable energy operator. Wind and solar assets. AI data center clean energy demand."
    },
    {
        "name": "The Trade Desk",
        "ticker": "TTD",
        "broker": "Trade Republic (DE)",
        "shares": None,
        "avg_buy_price_eur": 21.39,
        "currency": "EUR",
        "future_state_category": "Intelligence",
        "thesis": "Programmatic advertising AI platform. Currently -39% — review thesis or accumulate?"
    },
    {
        "name": "Energy Fuels",
        "ticker": "UUUU",
        "broker": "Trade Republic (DE)",
        "shares": None,
        "avg_buy_price_eur": 17.91,
        "currency": "EUR",
        "future_state_category": "Energy",
        "thesis": "US uranium + rare earth producer. Strategic asset for energy independence."
    },
    {
        "name": "Uranium Energy Corp",
        "ticker": "UEC",
        "broker": "Trade Republic (DE)",
        "shares": None,
        "avg_buy_price_eur": 13.47,
        "currency": "EUR",
        "future_state_category": "Energy",
        "thesis": "Pure-play US uranium miner. Low cost ISR operations. Nuclear renaissance beneficiary."
    },
]

ALL_PORTFOLIO = KIWOOM_PORTFOLIO + TRADE_REPUBLIC_PORTFOLIO


def fetch_portfolio_data() -> list[dict]:
    """Fetch live prices and calculate titan_K metrics for all holdings"""
    results = []

    for stock in ALL_PORTFOLIO:
        ticker = stock.get("ticker")
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            info = t.info

            if hist.empty:
                current_price = None
                change_pct = None
            else:
                current_price = round(float(hist["Close"].iloc[-1]), 2)
                prev_price = round(float(hist["Close"].iloc[-2]), 2) if len(hist) > 1 else current_price
                change_pct = round((current_price - prev_price) / prev_price * 100, 2)

            # Calculate return
            buy_price = stock.get("avg_buy_price_eur") or stock.get("avg_buy_price_krw")
            if current_price and buy_price:
                return_pct = round((current_price - buy_price) / buy_price * 100, 2)
            else:
                return_pct = None

            # Analyst target price from yfinance
            target_price = info.get("targetMeanPrice") or info.get("targetHighPrice")

            # titan_K conviction scoring
            category = stock.get("future_state_category", "None")
            base_score = _base_conviction(category, return_pct, change_pct)

            # Buy/Sell/Hold recommendation
            recommendation = _recommend(return_pct, target_price, current_price, category)

            results.append({
                "name":           stock["name"],
                "ticker":         ticker,
                "broker":         stock["broker"],
                "category":       category,
                "thesis":         stock["thesis"],
                "buy_price":      buy_price,
                "current_price":  current_price,
                "change_1d_pct":  change_pct,
                "return_pct":     return_pct,
                "target_price":   round(target_price, 2) if target_price else "N/A",
                "titan_k_score":  base_score,
                "recommendation": recommendation,
                "currency":       stock["currency"],
                "shares":         stock.get("shares"),
            })

        except Exception as e:
            print(f"[PORTFOLIO ERROR] {ticker}: {e}")
            results.append({
                "name":           stock["name"],
                "ticker":         ticker,
                "broker":         stock["broker"],
                "category":       stock.get("future_state_category",""),
                "thesis":         stock.get("thesis",""),
                "buy_price":      stock.get("avg_buy_price_eur") or stock.get("avg_buy_price_krw"),
                "current_price":  "Error",
                "change_1d_pct":  None,
                "return_pct":     None,
                "target_price":   "N/A",
                "titan_k_score":  5.0,
                "recommendation": "⚠️ Check manually",
                "currency":       stock.get("currency",""),
                "shares":         stock.get("shares"),
            })

    return results


def _base_conviction(category: str, return_pct, change_pct) -> float:
    """Score holding based on Future-State category and momentum"""
    base = {
        "Intelligence":    8.5,
        "Energy":          7.5,
        "Space/Logistics": 7.0,
        "Bio-Engineering": 7.0,
        "Robotics":        7.5,
        "None":            4.0,
    }.get(category, 5.0)

    # Momentum boost
    if change_pct and change_pct > 2:
        base = min(10, base + 0.3)
    if change_pct and change_pct < -3:
        base = max(1, base - 0.5)

    return round(base, 1)


def _recommend(return_pct, target_price, current_price, category) -> str:
    """Generate actionable recommendation"""
    if category == "None":
        return "🔴 REVIEW — Not Future-State aligned"

    if target_price and target_price != "N/A" and current_price:
        upside = (float(target_price) - float(current_price)) / float(current_price) * 100
        if upside > 30:
            return f"🟢 STRONG BUY — {round(upside)}% upside to target"
        elif upside > 10:
            return f"🟡 HOLD/ACCUMULATE — {round(upside)}% upside"
        elif upside < -10:
            return f"🔴 CONSIDER TRIMMING — {round(upside)}% above target"

    if return_pct and return_pct < -20:
        return "🔴 REVIEW THESIS — Down 20%+"
    if return_pct and return_pct > 100:
        return "🟡 CONSIDER PARTIAL PROFIT TAKING"

    return "🟢 HOLD — Thesis intact"


def generate_morning_briefing(portfolio_data: list[dict], titan_k_score: float) -> str:
    """Generate the 7am daily review points"""
    lines = [
        "🔱 *titan\\_K Morning Portfolio Review*",
        f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} Berlin Time",
        f"🔱 titan\\_K Index: *{titan_k_score}/100*",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "📋 *WHAT TO REVIEW TODAY:*",
        "",
    ]

    # Alerts
    alerts = []
    for s in portfolio_data:
        chg = s.get("change_1d_pct")
        ret = s.get("return_pct")
        rec = s.get("recommendation", "")

        if chg and abs(chg) > 3:
            direction = "📈" if chg > 0 else "📉"
            alerts.append(f"{direction} *{s['name']}* moved {chg:+.1f}% today — check news")

        if "REVIEW" in rec or "TRIM" in rec:
            alerts.append(f"⚠️ *{s['name']}* — {rec}")

        if ret and ret < -15:
            alerts.append(f"🔴 *{s['name']}* down {ret:.1f}% from your buy price — review thesis")

    if alerts:
        lines.append("🚨 *ALERTS:*")
        lines.extend(alerts)
        lines.append("")

    # Global context points
    lines.extend([
        "🌍 *GLOBAL ISSUES TO WATCH TODAY:*",
        "  • Iran/Hormuz situation → affects WTI, URNM, FCX",
        "  • Fed rate signals → affects COHR, TTD, RKLB",
        "  • China macro data → affects SK Hynix, LVMH, FCX",
        "  • AI capex announcements → affects COHR, SK Hynix, URNM",
        "  • Uranium spot price → affects URNM, UUUU, UEC",
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "💼 *YOUR PORTFOLIO SNAPSHOT:*",
        "",
    ])

    for s in portfolio_data:
        chg = s.get("change_1d_pct")
        ret = s.get("return_pct")
        chg_str = f"{chg:+.1f}%" if chg else "N/A"
        ret_str = f"{ret:+.1f}%" if ret else "N/A"
        lines.append(
            f"• *{s['ticker']}* {chg_str} today | Return: {ret_str} | {s.get('recommendation','')[:35]}"
        )

    return "\n".join(lines)
