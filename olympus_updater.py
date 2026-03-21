"""
🔱 OLYMPUS UPDATER
Pulls live prices → generates GPT forecasts → injects into TITAN_SYSTEM_v5.html → pushes to GitHub
Runs daily at 07:00 Berlin and weekly on Saturday 08:00
"""
import os
import json
import time
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, date
from pathlib import Path

import pytz

logger = logging.getLogger("titan_k.olympus_updater")

# ── Constants ─────────────────────────────────────────────────────────────────
BERLIN = pytz.timezone("Europe/Berlin")
DASHBOARD_PATH = Path(__file__).parent / "TITAN_SYSTEM_v5.html"
DATA_PATH = Path(__file__).parent / "data" / "live_prices.json"


# ══════════════════════════════════════════════════════════════════════════════
# 1. LIVE PRICE FETCHER (raw HTTP — no pandas, no yfinance)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_price(ticker: str) -> dict:
    """Fetch live price for a ticker via Yahoo Finance raw HTTP."""
    try:
        # Handle Korean tickers
        yf_ticker = ticker.replace(".", "%2E")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_ticker}?interval=1d&range=2d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        result = data["chart"]["result"][0]
        meta = result["meta"]
        price = meta.get("regularMarketPrice") or meta.get("previousClose")
        prev  = meta.get("previousClose") or price
        change_pct = ((price - prev) / prev * 100) if prev else 0
        return {
            "ticker": ticker,
            "price": round(price, 2),
            "prev_close": round(prev, 2),
            "change_pct": round(change_pct, 2),
            "currency": meta.get("currency", "USD"),
            "market_state": meta.get("marketState", "CLOSED"),
            "fetched_at": datetime.now(BERLIN).strftime("%Y-%m-%d %H:%M CET"),
            "error": None,
        }
    except Exception as e:
        logger.warning(f"Price fetch failed for {ticker}: {e}")
        return {"ticker": ticker, "price": None, "change_pct": None, "error": str(e)}


def fetch_macro_prices() -> dict:
    """Fetch key macro indicators."""
    macro_tickers = {
        "VIX": "^VIX",
        "SPX": "^GSPC",
        "NDX": "^NDX",
        "Gold": "GC=F",
        "Oil": "CL=F",
        "Copper": "HG=F",
        "BTC": "BTC-USD",
        "DXY": "DX-Y.NYB",
        "US10Y": "^TNX",
    }
    results = {}
    for name, ticker in macro_tickers.items():
        data = fetch_price(ticker)
        results[name] = data
        time.sleep(0.3)  # gentle rate limiting
    return results


def fetch_all_prices(tickers: list) -> dict:
    """Fetch prices for all tickers. Returns dict keyed by ticker."""
    prices = {}
    for ticker in tickers:
        if ticker in ("xAI", "FigureAI"):  # private companies
            continue
        prices[ticker] = fetch_price(ticker)
        time.sleep(0.3)
    return prices


# ══════════════════════════════════════════════════════════════════════════════
# 2. GPT FORECAST ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _gpt_call(system: str, user: str, max_tokens: int = 800) -> str:
    """Raw HTTP call to OpenAI API."""
    from config import OPENAI_API_KEY, FAST_MODEL
    try:
        payload = json.dumps({
            "model": FAST_MODEL,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ]
        }).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"GPT call failed: {e}")
        return ""


def generate_portfolio_forecasts(prices: dict, macro: dict, stocks: list) -> dict:
    """Generate GPT-4o-mini forecasts for portfolio stocks."""
    portfolio_stocks = [s for s in stocks if s["status"] == "portfolio"]
    if not portfolio_stocks:
        return {}

    # Build price summary for GPT
    price_lines = []
    for s in portfolio_stocks:
        p = prices.get(s["ticker"], {})
        current = p.get("price", "N/A")
        chg = p.get("change_pct", 0)
        price_lines.append(f"{s['ticker']} ({s['name']}): ${current} ({chg:+.1f}%) — Score {s['score']}/10 — {s['thesis'][:80]}")

    macro_summary = (
        f"VIX: {macro.get('VIX', {}).get('price', 'N/A')} | "
        f"SPX: {macro.get('SPX', {}).get('price', 'N/A')} | "
        f"Gold: {macro.get('Gold', {}).get('price', 'N/A')} | "
        f"Oil: {macro.get('Oil', {}).get('price', 'N/A')} | "
        f"BTC: {macro.get('BTC', {}).get('price', 'N/A')}"
    )

    system = """You are MINERVA, a sovereign investment intelligence system.
You analyze civilization-shift stocks across 6 categories: Intelligence, Energy, Space, Bio-Engineering, Robotics, Infrastructure.
Respond ONLY with valid JSON. No preamble. No explanation."""

    user = f"""Today: {date.today()} | Macro: {macro_summary}

Portfolio positions:
{chr(10).join(price_lines)}

For each ticker, provide updated forecasts and signal.
Respond with this exact JSON structure:
{{
  "TICKER": {{
    "signal": "BUY|HOLD|SELL|CAUTION|LEGEND|EXIT",
    "score": 1-10,
    "forecast_1w": number_or_null,
    "forecast_1m": number_or_null,
    "forecast_6m": number_or_null,
    "forecast_1y": number_or_null,
    "forecast_5y": number_or_null,
    "action": "one line action",
    "why": "one sentence reason for any change"
  }}
}}
Only include tickers that have meaningful updates. Keep forecasts realistic."""

    response = _gpt_call(system, user, max_tokens=1200)
    if not response:
        return {}

    try:
        # Strip markdown if present
        clean = response.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception as e:
        logger.error(f"Forecast JSON parse failed: {e}")
        return {}


def generate_morning_brief(prices: dict, macro: dict, forecasts: dict, stocks: list) -> str:
    """Generate the morning Telegram briefing text."""
    portfolio = [s for s in stocks if s["status"] == "portfolio"]
    exit_queue = [s for s in stocks if s["status"] == "exit"]

    # VIX regime
    vix = macro.get("VIX", {}).get("price", 0) or 0
    if vix < 15:   regime, deploy = "CALM", 0
    elif vix < 20: regime, deploy = "NORMAL", 25
    elif vix < 30: regime, deploy = "FEAR ⚠️", 50
    else:           regime, deploy = "CRISIS 🚨", 100

    # Build briefing
    now = datetime.now(BERLIN).strftime("%Y-%m-%d %H:%M")
    lines = [
        f"🔱 <b>OLYMPUS MORNING BRIEF</b>",
        f"<i>{now} CET</i>",
        f"",
        f"📊 <b>MACRO</b>",
        f"VIX: {vix} → {regime} → Deploy {deploy}%",
        f"SPX: {macro.get('SPX', {}).get('price', 'N/A')} ({macro.get('SPX', {}).get('change_pct', 0):+.1f}%)",
        f"Gold: {macro.get('Gold', {}).get('price', 'N/A')} | Oil: {macro.get('Oil', {}).get('price', 'N/A')}",
        f"",
        f"🎯 <b>PORTFOLIO</b>",
    ]

    # Portfolio positions
    for s in sorted(portfolio, key=lambda x: x["score"], reverse=True):
        p = prices.get(s["ticker"], {})
        price = p.get("price", "—")
        chg = p.get("change_pct")
        chg_str = f"({chg:+.1f}%)" if chg is not None else ""
        fc = forecasts.get(s["ticker"], {})
        signal = fc.get("signal", s["signal"])
        lines.append(f"{'🟢' if signal in ('BUY','LEGEND') else '🟡' if signal == 'HOLD' else '🔴'} "
                     f"<b>{s['ticker']}</b> {price} {chg_str} [{signal}]")
        if fc.get("why"):
            lines.append(f"   ↳ {fc['why']}")

    # Exit queue alerts
    if exit_queue:
        lines.append(f"")
        lines.append(f"⚠️ <b>EXIT QUEUE</b>")
        for s in exit_queue:
            p = prices.get(s["ticker"], {})
            price = p.get("price", "—")
            lines.append(f"🔴 {s['ticker']} {price} → {s['action']}")

    lines.append(f"")
    lines.append(f"📈 <a href='https://sobluenight10-commits.github.io/gods_plan/TITAN_SYSTEM_v5.html'>Full Dashboard →</a>")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# 3. HTML INJECTOR
# ══════════════════════════════════════════════════════════════════════════════

def inject_live_data_into_html(prices: dict, macro: dict, forecasts: dict) -> bool:
    """Inject live prices and forecasts into TITAN_SYSTEM_v5.html."""
    try:
        if not DASHBOARD_PATH.exists():
            logger.error(f"Dashboard not found: {DASHBOARD_PATH}")
            return False

        html = DASHBOARD_PATH.read_text(encoding="utf-8")
        now_str = datetime.now(BERLIN).strftime("%Y-%m-%d %H:%M CET")

        # Update last-updated timestamp
        import re
        html = re.sub(
            r'Last updated:.*?(?=<|")',
            f'Last updated: {now_str}',
            html
        )

        # Update VIX display
        vix_price = macro.get("VIX", {}).get("price")
        if vix_price:
            html = re.sub(r'(<div class="vix-num">)[^<]+(</div>)', f'\\g<1>{vix_price}\\g<2>', html)

            # Update regime
            if vix_price < 15:   regime_text = "CALM MARKET — HOLD CASH"
            elif vix_price < 20: regime_text = "NORMAL RANGE — SELECTIVE"
            elif vix_price < 30: regime_text = f"⚠ FEAR ZONE — DEPLOY 50%"
            else:                regime_text = f"🚨 CRISIS ZONE — FULL DEPLOY"
            html = re.sub(r'(<div class="regime-pill">)[^<]+(</div>)', f'\\g<1>{regime_text}\\g<2>', html)

        # Remove stale portfolio warning if we have fresh data
        if prices:
            html = html.replace(
                "⚠ Portfolio: Awaiting morning screenshot",
                f"✅ Live data: {now_str}"
            )

        DASHBOARD_PATH.write_text(html, encoding="utf-8")
        logger.info(f"Dashboard updated: {now_str}")
        return True

    except Exception as e:
        logger.error(f"HTML injection failed: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# 4. GITHUB PUSH
# ══════════════════════════════════════════════════════════════════════════════

def push_dashboard_to_github() -> bool:
    """Push updated TITAN_SYSTEM_v5.html to GitHub via git."""
    try:
        import subprocess
        repo_dir = Path(__file__).parent

        # Stage the dashboard file
        result = subprocess.run(
            ["git", "add", "TITAN_SYSTEM_v5.html"],
            cwd=repo_dir, capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(f"git add failed: {result.stderr}")
            return False

        # Commit
        now_str = datetime.now(BERLIN).strftime("%Y-%m-%d %H:%M")
        result = subprocess.run(
            ["git", "commit", "-m", f"auto: live update {now_str}"],
            cwd=repo_dir, capture_output=True, text=True
        )
        if result.returncode != 0:
            if "nothing to commit" in result.stdout:
                logger.info("No changes to push")
                return True
            logger.error(f"git commit failed: {result.stderr}")
            return False

        # Push
        result = subprocess.run(
            ["git", "push", "origin", "master"],
            cwd=repo_dir, capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.error(f"git push failed: {result.stderr}")
            return False

        logger.info(f"Dashboard pushed to GitHub Pages: {now_str}")
        return True

    except Exception as e:
        logger.error(f"GitHub push failed: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# 5. SAVE LIVE DATA
# ══════════════════════════════════════════════════════════════════════════════

def save_live_snapshot(prices: dict, macro: dict, forecasts: dict):
    """Save live snapshot to JSON for audit trail."""
    try:
        DATA_PATH.parent.mkdir(exist_ok=True)
        snapshot = {
            "timestamp": datetime.now(BERLIN).strftime("%Y-%m-%d %H:%M CET"),
            "prices": prices,
            "macro": macro,
            "forecasts": forecasts,
        }
        DATA_PATH.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Live snapshot saved")
    except Exception as e:
        logger.error(f"Snapshot save failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# 6. MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

def run_full_update(push_to_github: bool = True) -> dict:
    """
    Full daily update cycle:
    1. Fetch live prices
    2. Generate GPT forecasts
    3. Inject into HTML dashboard
    4. Push to GitHub Pages
    5. Return briefing data
    """
    from config import STOCKS, get_tradeable_tickers

    logger.info("=" * 50)
    logger.info("🔱 OLYMPUS UPDATE CYCLE STARTING")
    logger.info("=" * 50)

    # 1. Fetch macro
    logger.info("Fetching macro prices...")
    macro = fetch_macro_prices()
    vix = macro.get("VIX", {}).get("price", 0)
    logger.info(f"VIX: {vix}")

    # 2. Fetch portfolio prices
    logger.info("Fetching portfolio prices...")
    tickers = get_tradeable_tickers()
    prices = fetch_all_prices(tickers)
    fetched = sum(1 for p in prices.values() if p.get("price"))
    logger.info(f"Prices fetched: {fetched}/{len(tickers)}")

    # 3. Generate GPT forecasts (portfolio only to save tokens)
    logger.info("Generating GPT forecasts...")
    forecasts = generate_portfolio_forecasts(prices, macro, STOCKS)
    logger.info(f"Forecasts generated: {len(forecasts)} stocks")

    # 4. Save snapshot
    save_live_snapshot(prices, macro, forecasts)

    # 5. Inject into HTML
    logger.info("Injecting live data into dashboard...")
    inject_live_data_into_html(prices, macro, forecasts)

    # 6. Push to GitHub
    if push_to_github:
        logger.info("Pushing to GitHub Pages...")
        pushed = push_dashboard_to_github()
        logger.info(f"GitHub push: {'✅' if pushed else '❌'}")

    # 7. Generate briefing
    brief = generate_morning_brief(prices, macro, forecasts, STOCKS)

    logger.info("🔱 OLYMPUS UPDATE COMPLETE")
    return {
        "prices": prices,
        "macro": macro,
        "forecasts": forecasts,
        "brief": brief,
        "vix": vix,
    }


def run_daily_brief() -> str:
    """Called by scheduler at 07:00 Berlin. Returns Telegram message."""
    try:
        result = run_full_update(push_to_github=True)
        return result["brief"]
    except Exception as e:
        logger.error(f"Daily brief failed: {e}", exc_info=True)
        return f"🔱 ⚠️ Olympus update error: {str(e)[:200]}"


def run_weekly_olympus() -> str:
    """Called by scheduler on Saturday 08:00. Full deep update."""
    try:
        result = run_full_update(push_to_github=True)
        vix = result["vix"]

        # Determine regime
        if vix < 15:   regime, deploy = "CALM", 0
        elif vix < 20: regime, deploy = "NORMAL", 25
        elif vix < 30: regime, deploy = "FEAR ⚠️", 50
        else:           regime, deploy = "CRISIS 🚨", 100

        # Weekly summary
        from config import STOCKS
        buy_signals  = [s for s in STOCKS if s["signal"] in ("BUY",) and s["status"] in ("portfolio","watchlist")]
        exit_signals = [s for s in STOCKS if s["status"] == "exit"]

        msg = (
            f"🏛 <b>OLYMPUS WEEKLY REVIEW</b>\n"
            f"<i>{datetime.now(BERLIN).strftime('%Y-%m-%d')} Saturday</i>\n\n"
            f"📊 <b>REGIME: {regime}</b> → Deploy {deploy}% of dry powder\n"
            f"VIX: {vix}\n\n"
            f"🟢 BUY signals: {len(buy_signals)} stocks\n"
            f"🔴 Exit queue: {len(exit_signals)} positions\n\n"
            f"Dashboard refreshed and pushed to GitHub Pages.\n"
            f"📈 <a href='https://sobluenight10-commits.github.io/gods_plan/TITAN_SYSTEM_v5.html'>Full Dashboard →</a>"
        )
        return msg
    except Exception as e:
        logger.error(f"Weekly olympus failed: {e}", exc_info=True)
        return f"🏛 ⚠️ Weekly Olympus error: {str(e)[:200]}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    result = run_full_update(push_to_github=False)
    print(result["brief"])
