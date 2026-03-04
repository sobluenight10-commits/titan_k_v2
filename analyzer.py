import json, re, os
from openai import OpenAI
from config import OPENAI_API_KEY, FUTURE_STATE

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are titan_K — the world's most advanced investment intelligence AI.
Your job: analyze Korean financial blog posts and extract actionable investment intelligence.
ALWAYS respond with valid JSON only. No markdown. No explanation. Just JSON."""

USER_PROMPT = """Analyze this Korean blog post for investment intelligence.

Title: {title}
Date: {date}
Category: {category}
Content:
{content}

Return ONLY this JSON structure:
{{
  "summary_en": "3-sentence English summary of the post",
  "summary_kr": "3문장 한국어 요약",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "global_macro_context": "What global macro events or trends are referenced",
  "investment_insight": "The single most important actionable investment insight from this post",
  "companies": [
    {{
      "name": "Company name (Korean + English if known)",
      "ticker": "TICKER or null",
      "exchange": "NYSE/NASDAQ/KRX/ETF or null",
      "why_mentioned": "Exact reason blogger mentioned this company",
      "sentiment": "bullish/bearish/neutral",
      "hidden_gem": true/false,
      "future_state_category": "Intelligence/Energy/Space-Logistics/Bio-Engineering/Robotics/None",
      "conviction_score": 8,
      "when_to_buy": "Specific condition or price level to buy",
      "target_price": "Target price or null",
      "risk": "Main risk factor",
      "related_tickers": ["TICKER1", "TICKER2"]
    }}
  ],
  "watch_signal": "STRONG BUY/WATCH/AVOID",
  "titan_k_indicators": ["SOX", "VIX"],
  "paradigm_shift": true/false,
  "paradigm_description": "If true, describe the civilizational shift this represents"
}}

Rules:
- conviction_score: 1-10. Base on future-state fit + innovation quality + blogger confidence
- hidden_gem: true only if blogger hints at undiscovered/undervalued opportunity
- when_to_buy: be specific — price dip %, catalyst event, or technical level
- Include ALL companies even if ticker unknown (ticker = null)
- paradigm_shift: true if this post is about a world-changing trend"""


def analyze_post(post: dict) -> dict:
    content = post.get("content", "")
    if len(content) < 50:
        return {"error": "Content too short", **post}

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT.format(
                    title=post.get("title",""),
                    date=post.get("date",""),
                    category=post.get("category",""),
                    content=content[:6000]
                )}
            ],
            temperature=0.2,
            max_tokens=2500
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r'^```json\s*|\s*```$', '', raw)
        result = json.loads(raw)

        # Enrich companies with Future-State scoring
        for c in result.get("companies", []):
            c["titan_k_score"] = _score(c)
            c["date_mentioned"] = post.get("date","")
            c["source_url"] = post.get("url","")
            c["available_trade_republic"] = _check_tr(c.get("ticker",""))
            c["available_kiwoom"] = _check_kiwoom(c.get("exchange",""))

        result["title"] = post.get("title","")
        result["date"]  = post.get("date","")
        result["url"]   = post.get("url","")
        return result

    except Exception as e:
        print(f"[ANALYZER ERROR] {e}")
        return {"error": str(e), **post}


def _score(company: dict) -> float:
    """Compute titan_K conviction score with Future-State boost"""
    base = float(company.get("conviction_score", 5))
    boosts = {
        "Intelligence":    1.5,
        "Bio-Engineering": 1.3,
        "Energy":          1.2,
        "Robotics":        1.2,
        "Space/Logistics": 1.1,
        "None":            0.6
    }
    cat = company.get("future_state_category", "None")
    boosted = min(10.0, base * boosts.get(cat, 1.0))
    if company.get("hidden_gem"):
        boosted = min(10.0, boosted + 0.5)
    return round(boosted, 1)


def _check_tr(ticker: str) -> str:
    """Trade Republic supports most US/EU stocks and ETFs"""
    if not ticker:
        return "Check manually"
    us_exchanges = ["NYSE","NASDAQ","ETF","AMEX"]
    return "✅ Likely available" if ticker else "Check manually"


def _check_kiwoom(exchange: str) -> str:
    if not exchange:
        return "Check manually"
    return "✅ Available" if "KRX" in (exchange or "") else "Check via Kiwoom HTS"
