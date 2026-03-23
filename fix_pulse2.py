import re

content = open('/home/minerva/gods_plan/battle_rhythm.py', 'r').read()

# Find and replace the entire run_news_pulse function
new_func = """def run_news_pulse():
    \"\"\"
    Layer 3 - runs every 2 hours during US session (15:30-23:00 Berlin).
    Synthesizes NEW headlines into ONE actionable brief via GPT.
    Only sends if actionable signal detected. No raw headline dumps.
    \"\"\"
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
            "Analyze these NEW headlines and produce ONE concise actionable briefing. "
            "Rules: Max 4 lines total. "
            "Line 1: Market mood in one sentence. "
            "Line 2-3: 2-3 specific portfolio impacts (ticker + what it means + action if any). "
            "Line 4: ONE priority action or HOLD ALL if nothing urgent. "
            "If nothing actionable, reply exactly: SKIP. "
            "Never list raw headlines. Synthesize only. Be direct."
        )
        user = (
            f"Today {now.strftime('%Y-%m-%d %H:%M')} Berlin. New headlines since last check:"
            f"{chr(10)}{chr(10)}{headline_block}{chr(10)}{chr(10)}"
            "Portfolio: SK Hynix(LEGEND), Hanwha(LEGEND), PLTR(HOLD), COHR(HOLD), "
            "UEC(HOLD+stop$11.50), AVAV(CAUTION), VRT(HOLD), ARKQ/BOTZ(HOLD), "
            "RKLB(HOLD), TMO(HOLD), URNM(HOLD), NTR(STRIKE-add), "
            "Xiaomi(OBSERVE-Mar24earnings), IONQ(HOLD), TSMC(HOLD). "
            "EXIT: HUYA(-77%), GEVO(-87%), FCX(stop$54.50), IAU(+128%-sell-on-strength). "
            "Synthesize into ONE actionable briefing. If nothing material, reply SKIP."
        )

        response = _gpt_call(system, user, max_tokens=200)

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
"""

pattern = r'def run_news_pulse\(\):.*?(?=\ndef |\Z)'
new_content = re.sub(pattern, new_func + '\n', content, flags=re.DOTALL)
open('/home/minerva/gods_plan/battle_rhythm.py', 'w').write(new_content)
print("Done")
