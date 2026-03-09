"""
🔱 titan_K v2 — Portfolio Tracker & Briefing Generator
Tracks all positions across Trade Republic + Kiwoom, scores them, generates briefings.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from config import PORTFOLIO, WATCHLIST, EARNINGS_CALENDAR, MACRO_CALENDAR
from market_data import fetch_stock_prices, fetch_fx_rate

logger = logging.getLogger("titan_k.portfolio")


def fetch_portfolio_data() -> List[Dict]:
    """Fetch current prices for all portfolio positions and enrich with live data."""
    all_positions = []
    
    # Collect all tickers
    all_tickers = set()
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            all_tickers.add(pos["ticker"])
    
    # Fetch prices in batch
    prices = fetch_stock_prices(list(all_tickers))
    fx_rate = fetch_fx_rate()
    
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            ticker = pos["ticker"]
            price_data = prices.get(ticker, {})
            
            enriched = {
                **pos,
                "broker": broker,
                "current_price": price_data.get("price"),
                "change_1d_pct": price_data.get("change_pct"),
                "fx_rate": fx_rate,
            }
            
            # Calculate return if we have buy price
            if enriched.get("buy_price_krw") and enriched.get("current_price"):
                # KRW position — price is in KRW
                enriched["return_pct"] = round(
                    ((enriched["current_price"] - enriched["buy_price_krw"]) / enriched["buy_price_krw"]) * 100, 1
                )
            elif enriched.get("buy_price_usd") and enriched.get("current_price"):
                enriched["return_pct"] = round(
                    ((enriched["current_price"] - enriched["buy_price_usd"]) / enriched["buy_price_usd"]) * 100, 1
                )
            elif enriched.get("buy_price_eur") and enriched.get("current_price"):
                enriched["return_pct"] = round(
                    ((enriched["current_price"] / fx_rate - enriched["buy_price_eur"]) / enriched["buy_price_eur"]) * 100, 1
                )
            else:
                enriched["return_pct"] = None
            
            # Generate recommendation
            score = enriched.get("score") or enriched.get("titan_k_score", 0)
            enriched["titan_k_score"] = score
            if score >= 8:
                enriched["recommendation"] = "STRONG BUY / HOLD + ADD"
            elif score >= 5:
                enriched["recommendation"] = "HOLD — NO ADDITIONS"
            elif score >= 3:
                enriched["recommendation"] = "REVIEW — SET STOP"
            elif score >= 1:
                enriched["recommendation"] = "EXIT — REDEPLOY"
            else:
                enriched["recommendation"] = "HOLD"
            
            # Override with explicit action if set
            if pos.get("action"):
                enriched["recommendation"] = pos["action"]
            
            all_positions.append(enriched)
    
    return all_positions


def generate_morning_briefing() -> Dict:
    """Generate the complete morning briefing with macro + portfolio data."""
    from market_data import fetch_market_snapshot, calculate_titan_k_index, get_vix_regime
    from config import WEIGHTS
    
    logger.info("Generating morning macro + portfolio briefing...")
    
    # 1. Fetch macro snapshot
    snapshot = fetch_market_snapshot()
    composite = calculate_titan_k_index(snapshot, WEIGHTS)
    
    # 2. VIX regime
    vix_data = snapshot.get("VIX", {})
    vix_value = vix_data.get("value", 25)
    if isinstance(vix_value, (int, float)):
        regime, deploy_pct, label = get_vix_regime(vix_value)
    else:
        regime, deploy_pct, label = "UNKNOWN", 0, "DATA ERROR"
    
    # 3. Key moves (biggest movers from the indicators)
    key_moves = []
    priority_indicators = ["VIX", "SOX", "Gold", "Oil", "SPX", "NDX", "DXY", "US10Y", "BTC", "Copper"]
    for ind in priority_indicators:
        data = snapshot.get(ind, {})
        if isinstance(data.get("value"), (int, float)):
            key_moves.append({
                "name": ind,
                "value": data["value"],
                "change_pct": data.get("change_pct", 0),
                "signal": data.get("signal", ""),
            })
    
    # Sort by absolute change
    key_moves.sort(key=lambda x: abs(x.get("change_pct", 0)), reverse=True)
    
    # 4. Portfolio data
    portfolio_data = fetch_portfolio_data()
    
    # 5. Earnings today
    today = datetime.now().strftime("%Y-%m-%d")
    earnings_today = [e for e in EARNINGS_CALENDAR if e["date"] == today]
    
    # 6. Generate overnight summary via GPT
    overnight_summary = _generate_overnight_summary(snapshot, key_moves, portfolio_data)
    
    # 7. Portfolio impact analysis
    portfolio_impact = _generate_portfolio_impact(portfolio_data, snapshot)
    
    # 8. Today's action items
    todays_actions = _generate_action_items(portfolio_data, earnings_today, regime, deploy_pct)
    
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "vix": vix_data,
        "regime": regime,
        "deploy_pct": deploy_pct,
        "composite_score": composite,
        "key_moves": key_moves[:8],
        "overnight_summary": overnight_summary,
        "portfolio_impact": portfolio_impact,
        "todays_actions": todays_actions,
        "earnings_today": earnings_today,
    }


def _generate_overnight_summary(snapshot: Dict, key_moves: list, portfolio: list) -> str:
    """Generate overnight market summary using GPT-4o."""
    from openai import OpenAI
    from config import OPENAI_API_KEY
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Build context
    moves_text = "\n".join(
        f"- {m['name']}: {m['value']} ({m['change_pct']:+.1f}%) — {m['signal']}"
        for m in key_moves[:10]
    )
    
    # Portfolio movers
    portfolio_movers = sorted(
        [p for p in portfolio if p.get("change_1d_pct") is not None],
        key=lambda x: abs(x.get("change_1d_pct", 0)),
        reverse=True,
    )[:5]
    
    portfolio_text = "\n".join(
        f"- {p['name']} ({p['ticker']}): {p.get('change_1d_pct', 0):+.1f}% | Score: {p.get('titan_k_score', '?')}/10"
        for p in portfolio_movers
    )
    
    vix = snapshot.get("VIX", {}).get("value", "?")
    gold = snapshot.get("Gold", {}).get("value", "?")
    oil = snapshot.get("Oil", {}).get("value", "?")
    
    prompt = f"""You are Minerva, briefing Titan at 7am Berlin time. Write a concise overnight market summary.
Be direct. No fluff. Focus on what matters for a paradigm-shift investor with positions in defense, AI, uranium, gene editing, and gold.

OVERNIGHT MACRO:
VIX: {vix}
Gold: {gold}
Oil: {oil}
Key Moves:
{moves_text}

TITAN'S PORTFOLIO MOVERS:
{portfolio_text}

Write 3-4 sentences covering: 1) What happened overnight 2) Why it matters for Titan's positions 3) Any regime change signal.
Plain text only, no markdown."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=300,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Overnight summary generation failed: {e}")
        return f"VIX at {vix}. Key moves: {', '.join(m['name'] for m in key_moves[:5])}. Check positions manually."


def _generate_portfolio_impact(portfolio: list, snapshot: Dict) -> str:
    """Analyze macro impact on each portfolio position."""
    from openai import OpenAI
    from config import OPENAI_API_KEY
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    positions_text = "\n".join(
        f"- {p['name']} ({p['ticker']}): Score {p.get('titan_k_score', '?')}/10 | "
        f"Today: {p.get('change_1d_pct', '?')}% | Action: {p.get('action', p.get('recommendation', '?'))}"
        for p in portfolio
        if p.get("ticker") not in ("MC.PA",)  # skip locked/irrelevant
    )
    
    vix = snapshot.get("VIX", {}).get("value", "?")
    
    prompt = f"""You are Minerva. Analyze how overnight macro changes impact each of Titan's positions.
Be surgical. Each position gets one line: ticker → impact → action.

Current VIX: {vix}
Positions:
{positions_text}

Watchlist: AVAV (pending earnings), CRSP ($44 limit), NTLA ($10 limit), IONQ ($25 limit), KTOS ($80 limit add)

Write a compact impact assessment. Focus on positions that need attention TODAY. Plain text, no markdown."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=400,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Portfolio impact generation failed: {e}")
        return "Unable to generate impact analysis. Check positions manually."


def _generate_action_items(portfolio: list, earnings_today: list, regime: str, deploy_pct: int) -> str:
    """Generate today's specific action items."""
    actions = []
    
    # Regime-based action
    actions.append(f"Regime: {regime} → Deploy up to {deploy_pct}% of available capital")
    
    # Earnings today
    for e in earnings_today:
        actions.append(f"🔴 EARNINGS: {e['ticker']} ({e['timing']}) — {e.get('importance', '')}")
    
    # Positions needing attention
    for p in portfolio:
        action = p.get("action", "")
        if any(word in action.upper() for word in ["EXIT", "SELL", "BROKEN"]):
            actions.append(f"⚠️ {p['ticker']}: {action}")
        elif "LIMIT" in action.upper() or "SET TODAY" in action.upper():
            actions.append(f"📌 {p['ticker']}: {action}")
    
    # Watchlist limit orders
    for w in WATCHLIST:
        if "today" in w.get("timing", "").lower() or "set" in w.get("timing", "").lower():
            actions.append(f"📌 WATCHLIST: {w['ticker']} — {w['entry']} ({w['amount']})")
    
    # Macro events
    today = datetime.now().strftime("%Y-%m-%d")
    for event in MACRO_CALENDAR:
        if event["date"] == today:
            actions.append(f"📅 MACRO: {event['event']} — {event['rule']}")
    
    return "\n".join(actions) if actions else "No specific actions today. Limits armed. Go to work."
