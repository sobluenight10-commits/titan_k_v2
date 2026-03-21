"""
🔱 titan_K v2 — Macro Briefing Generator
Generates the overnight global macro digest with portfolio-specific impact analysis.
This is Mission 2: the strategic brain that connects global events to your positions.
"""
import logging
from datetime import datetime
from typing import Dict

from config import PORTFOLIO, WATCHLIST, EARNINGS_CALENDAR, MACRO_CALENDAR
from market_data import fetch_market_snapshot, calculate_titan_k_index, get_vix_regime, fetch_stock_prices, fetch_fx_rate
from config import WEIGHTS

logger = logging.getLogger("titan_k.macro_briefing")


def generate_full_macro_briefing() -> Dict:
    """
    Generate the complete macro + portfolio briefing.
    This is the primary function called by main.py for Mission 2.
    """
    logger.info("═" * 50)
    logger.info("🔱 Generating Macro + Portfolio Briefing...")
    logger.info("═" * 50)
    
    # ── Step 1: Macro Snapshot ────────────────────────────────────────────
    logger.info("Step 1: Fetching 30-indicator macro snapshot...")
    snapshot = fetch_market_snapshot()
    
    # ── Step 2: Composite Score & Regime ──────────────────────────────────
    composite = calculate_titan_k_index(snapshot, WEIGHTS)
    vix_data = snapshot.get("VIX", {})
    vix_value = vix_data.get("value", 25)
    
    if isinstance(vix_value, (int, float)):
        regime, deploy_pct, label = get_vix_regime(vix_value)
    else:
        regime, deploy_pct, label = "UNKNOWN", 0, "DATA ERROR"
    
    logger.info(f"Composite: {composite} | VIX: {vix_value} | Regime: {regime} ({deploy_pct}%)")
    
    # ── Step 3: Key Market Moves ──────────────────────────────────────────
    key_indicators = ["VIX", "SPX", "NDX", "SOX", "Gold", "Oil", "Copper", "DXY", "US10Y", "BTC", "Uranium"]
    key_moves = []
    for ind in key_indicators:
        data = snapshot.get(ind, {})
        if isinstance(data.get("value"), (int, float)):
            key_moves.append({
                "name": ind,
                "value": data["value"],
                "change_pct": data.get("change_pct", 0),
                "signal": data.get("signal", ""),
            })
    key_moves.sort(key=lambda x: abs(x.get("change_pct", 0)), reverse=True)
    
    # ── Step 4: Portfolio Prices ──────────────────────────────────────────
    logger.info("Step 4: Fetching portfolio prices...")
    all_tickers = set()
    for broker_positions in PORTFOLIO.values():
        for pos in broker_positions:
            all_tickers.add(pos["ticker"])
    for w in WATCHLIST:
        all_tickers.add(w["ticker"])
    
    prices = fetch_stock_prices(list(all_tickers))
    fx_rate = fetch_fx_rate()
    
    # ── Step 5: Earnings Check ────────────────────────────────────────────
    today = datetime.now().strftime("%Y-%m-%d")
    earnings_today = [e for e in EARNINGS_CALENDAR if e["date"] == today]
    macro_events = [e for e in MACRO_CALENDAR if e["date"] == today]
    
    # ── Step 6: GPT-4o Analysis ───────────────────────────────────────────
    logger.info("Step 6: Generating GPT-4o analysis...")
    overnight_summary = _gpt_overnight_analysis(snapshot, key_moves, prices, fx_rate)
    portfolio_impact = _gpt_portfolio_impact(snapshot, prices, fx_rate, regime, deploy_pct)
    action_items = _compile_action_items(prices, earnings_today, macro_events, regime, deploy_pct, fx_rate)
    
    logger.info("✅ Macro briefing complete")
    
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "vix": vix_data,
        "regime": regime,
        "deploy_pct": deploy_pct,
        "composite_score": composite,
        "key_moves": key_moves[:8],
        "overnight_summary": overnight_summary,
        "portfolio_impact": portfolio_impact,
        "todays_actions": action_items,
        "earnings_today": earnings_today,
        "fx_rate": fx_rate,
    }


def _gpt_overnight_analysis(snapshot: Dict, key_moves: list, prices: Dict, fx_rate: float) -> str:
    """GPT-4o generates the overnight macro narrative."""
    from openai import OpenAI
    from config import OPENAI_API_KEY
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    moves_block = "\n".join(
        f"  {m['name']}: {m['value']} ({m['change_pct']:+.1f}%) — {m['signal']}"
        for m in key_moves[:10]
    )
    
    # Portfolio biggest movers
    movers = []
    for ticker, data in sorted(prices.items(), key=lambda x: abs(x[1].get("change_pct", 0)), reverse=True)[:8]:
        movers.append(f"  {ticker}: ${data['price']} ({data['change_pct']:+.1f}%)")
    movers_block = "\n".join(movers)
    
    prompt = f"""You are Minerva — Titan's strategic investment advisor. 7am Berlin briefing.

Titan's sectors: AI/Intelligence (PLTR, COHR, SK Hynix), Defense (KTOS, AVAV), Energy/Nuclear (UEC, URNM, FCX), 
Bio-Engineering (CRSP, NTLA, TMO), Space (RKLB), Gold (IAU), Quantum (IONQ)

MACRO DATA:
{moves_block}

TITAN'S STOCKS:
{movers_block}

EUR/USD: {fx_rate}

FORMAT RULES — THIS IS FOR A PHONE SCREEN:
• Write ONLY bullet points. One line per bullet. Max 15 words per bullet.
• Use this exact structure:

🌍 WHAT HAPPENED
• [bullet 1 — key global event]
• [bullet 2 — second event if any]

⚔️ SECTOR IMPACT
• [which Titan sector was hit/helped + why, one bullet per sector affected]

📡 REGIME READ
• [is buying window widening or closing? one bullet]

👁️ WATCH TODAY
• [single most important thing to watch]

NO paragraphs. NO long sentences. This is read on a phone at 7am."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35,
            max_tokens=350,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"GPT overnight analysis failed: {e}")
        vix = snapshot.get("VIX", {}).get("value", "?")
        return f"VIX at {vix}. Top movers: {', '.join(m['name'] for m in key_moves[:4])}. Manual review required."


def _gpt_portfolio_impact(snapshot: Dict, prices: Dict, fx_rate: float, regime: str, deploy_pct: int) -> str:
    """GPT-4o generates position-by-position impact analysis."""
    from openai import OpenAI
    from config import OPENAI_API_KEY
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Build position list with prices
    lines = []
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            ticker = pos["ticker"]
            price_data = prices.get(ticker, {})
            price = price_data.get("price", "?")
            change = price_data.get("change_pct", 0)
            lines.append(
                f"{ticker} ({pos['name']}) | ${price} ({change:+.1f}%) | "
                f"Score: {pos.get('score', '?')}/10 | Action: {pos.get('action', 'HOLD')} | "
                f"Thesis: {pos.get('thesis', '?')}"
            )
    
    watchlist_lines = []
    for w in WATCHLIST:
        price_data = prices.get(w["ticker"], {})
        price = price_data.get("price", "?")
        watchlist_lines.append(
            f"{w['ticker']} ({w['name']}) | ${price} | Entry: {w['entry']} | Score: {w.get('score', '?')}/10"
        )
    
    prompt = f"""You are Minerva. Overnight macro impact on Titan's portfolio.

REGIME: {regime} — Deploy {deploy_pct}%
EUR/USD: {fx_rate}

CURRENT PORTFOLIO:
{chr(10).join(lines)}

WATCHLIST (pending entries):
{chr(10).join(watchlist_lines)}

FORMAT RULES — PHONE SCREEN:
• ONLY list positions that need attention today. Skip "no action" positions entirely.
• One bullet per position. Format: "• TICKER → [what changed] → [action]"
• Max 12 words per bullet
• Group into: 🔴 NEEDS ACTION and 🟢 ON TRACK (list tickers only for on-track)
• If a stock is near its stop loss, flag it with 🚨
• If earnings are approaching, flag with ⏳

Example output:
🔴 NEEDS ACTION
• UEC → uranium +3.4%, earnings tomorrow → hold, add if beats
• FCX → copper weak, near stop $54.50 → 🚨 monitor

🟢 ON TRACK: PLTR, COHR, KTOS, RKLB, TMO, IAU

NO paragraphs. NO long explanations."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"GPT portfolio impact failed: {e}")
        return "Portfolio impact analysis unavailable. Check positions manually."


def _compile_action_items(prices: Dict, earnings_today: list, macro_events: list, 
                          regime: str, deploy_pct: int, fx_rate: float) -> str:
    """Compile concrete action items for today."""
    items = []
    
    # Regime
    items.append(f"⚡ REGIME: {regime} → Deploy up to {deploy_pct}%")
    
    # Earnings
    for e in earnings_today:
        ticker = e["ticker"]
        price = prices.get(ticker, {}).get("price", "?")
        items.append(f"🔴 EARNINGS: {ticker} ${price} — {e['timing']} — {e.get('importance', '')}")
        
        # Add specific triggers from calendar
        for ec in EARNINGS_CALENDAR:
            if ec["ticker"] == ticker and ec["date"] == e["date"]:
                items.append(f"   → Trigger: Check TITAN_SYSTEM_v4 for {ticker} response protocol")
    
    # Macro events
    for event in macro_events:
        items.append(f"📅 {event['event']}: {event['rule']}")
    
    # EXIT signals (exclude LEGEND/NEVER SELL — those are holds, not exits)
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            action = pos.get("action", "")
            # Only flag actual exits/sells, not "NEVER SELL" legends
            if "NEVER SELL" in action.upper() or "LEGEND" in action.upper():
                continue
            if any(word in action.upper() for word in ["EXIT", "SELL", "BROKEN"]):
                price = prices.get(pos["ticker"], {}).get("price", "?")
                items.append(f"⚠️ {pos['ticker']} ${price} → {action}")
    
    # Stop proximity alerts
    for broker, positions in PORTFOLIO.items():
        for pos in positions:
            stop = pos.get("stop_usd")
            if stop:
                price = prices.get(pos["ticker"], {}).get("price")
                if price and isinstance(price, (int, float)):
                    proximity = ((price - stop) / price) * 100
                    if proximity < 5:
                        items.append(f"🚨 STOP ALERT: {pos['ticker']} at ${price} — stop ${stop} ({proximity:.1f}% away)")
    
    # Watchlist limit proximity
    for w in WATCHLIST:
        price = prices.get(w["ticker"], {}).get("price")
        if price and w.get("entry"):
            # Try to extract limit price from entry string
            import re
            match = re.search(r'\$(\d+\.?\d*)', w["entry"])
            if match:
                limit = float(match.group(1))
                if price <= limit * 1.05:  # within 5% of limit
                    items.append(f"📌 NEAR LIMIT: {w['ticker']} at ${price} — limit {w['entry']} ({w['amount']})")
    
    # FX rate
    items.append(f"💱 EUR/USD: {fx_rate}")
    
    return "\n".join(items) if items else "No actions required. Limits armed. Go to work."
