"""
🔱 titan_K v2 — GPT-4o Blog Post Analyzer
Deep surgical analysis of Korean investment blog posts.
Extracts companies, scores them, identifies paradigm shifts.
"""
import json
import logging
from typing import Dict

from openai import OpenAI
from config import OPENAI_API_KEY, FUTURE_STATE_CATEGORIES

logger = logging.getLogger("titan_k.analyzer")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are Minerva, the analytical brain of the titan_K Investment Intelligence System.
You analyze Korean investment blog posts (from ranto28 on Naver) and extract actionable intelligence.

Your analysis framework:
1. FUTURE-STATE MATRIX: Classify every mentioned company into one of: Intelligence, Energy, Space, Bio-Engineering, Robotics
2. TITAN_K SCORING: Score each stock 1-10 based on paradigm-shift potential, catalyst proximity, and conviction level
3. HIDDEN GEMS: Flag any small/mid-cap with score ≥ 7 that most investors would overlook
4. PARADIGM SHIFT: Identify if the post discusses a structural market change (not just a trade)

SCORING GUIDE:
- 9-10: World-changing thesis + near-term catalyst + strong analyst consensus
- 7-8: Strong thesis + catalyst within 6 months + buy-zone entry available
- 5-6: Valid thesis but unclear timing or entry
- 3-4: Thesis weakening or macro headwinds
- 1-2: Broken thesis or exit signal

CRITICAL: The blog is in Korean. Analyze the Korean text directly. Output in English.
CRITICAL: Be specific about entry prices, targets, and timing. Vague = useless."""

ANALYSIS_PROMPT = """Analyze this Korean investment blog post and return a JSON object.

POST TITLE: {title}
POST DATE: {date}
POST URL: {url}

CONTENT:
{content}

Return ONLY valid JSON with this exact structure (no markdown, no backticks):
{{
  "title": "English translation of title",
  "date": "{date}",
  "url": "{url}",
  "summary_en": "2-3 sentence English summary of the post's key argument",
  "investment_insight": "The single most actionable investment insight from this post",
  "watch_signal": "STRONG BUY | BUY | WATCH | HOLD | SELL | AVOID",
  "paradigm_shift": true/false,
  "paradigm_description": "If paradigm_shift is true, describe the structural change",
  "global_macro_context": "How does this connect to current global macro trends?",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "titan_k_indicators": ["Which of the 30 indicators are most relevant"],
  "companies": [
    {{
      "name": "Company Name",
      "ticker": "TICKER",
      "future_state_category": "Intelligence|Energy|Space|Bio-Engineering|Robotics",
      "titan_k_score": 8,
      "sentiment": "bullish|neutral|bearish",
      "why_mentioned": "Why the blog mentioned this company",
      "when_to_buy": "Specific entry condition or price level",
      "target_price": "$XXX or percentage upside",
      "risk": "Key risk factor",
      "hidden_gem": true/false,
      "available_trade_republic": "Yes/No/Unknown",
      "available_kiwoom": "Yes/No/Unknown",
      "date_mentioned": "{date}"
    }}
  ]
}}"""


def analyze_post(post: Dict) -> Dict:
    """Analyze a single blog post using GPT-4o."""
    content = post.get("content", "") or post.get("summary", "")
    
    if not content or len(content.strip()) < 50:
        logger.warning(f"Skipping post with insufficient content: {post.get('title', '?')}")
        return {"error": "Insufficient content", "title": post.get("title", "")}
    
    prompt = ANALYSIS_PROMPT.format(
        title=post.get("title", ""),
        date=post.get("date", ""),
        url=post.get("url", ""),
        content=content[:6000],  # Token budget management
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        # Validate required fields
        if "companies" not in result:
            result["companies"] = []
        if "watch_signal" not in result:
            result["watch_signal"] = "WATCH"
        
        # Ensure all companies have required fields
        for company in result["companies"]:
            company.setdefault("titan_k_score", 5)
            company.setdefault("hidden_gem", False)
            company.setdefault("future_state_category", "Intelligence")
            company.setdefault("date_mentioned", post.get("date", ""))
        
        logger.info(
            f"Analyzed: {result.get('title', '?')} → "
            f"{result.get('watch_signal', '?')} | "
            f"{len(result.get('companies', []))} companies"
        )
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return {"error": str(e), "title": post.get("title", "")}
    except Exception as e:
        logger.error(f"GPT-4o analysis error: {e}")
        return {"error": str(e), "title": post.get("title", "")}


def generate_blog_summary(analyses: list) -> str:
    """Generate an executive summary across multiple analyzed posts."""
    if not analyses:
        return "No posts analyzed in this period."
    
    # Collect all companies and signals
    all_companies = []
    signals = []
    paradigm_shifts = []
    
    for a in analyses:
        if a.get("error"):
            continue
        signals.append(a.get("watch_signal", ""))
        if a.get("paradigm_shift"):
            paradigm_shifts.append(a.get("paradigm_description", ""))
        all_companies.extend(a.get("companies", []))
    
    # Top stocks by score
    top_stocks = sorted(
        [c for c in all_companies if c.get("titan_k_score", 0) >= 7],
        key=lambda x: x.get("titan_k_score", 0),
        reverse=True,
    )[:5]
    
    # Hidden gems
    gems = [c for c in all_companies if c.get("hidden_gem")]
    
    # Build summary prompt
    summary_data = {
        "total_posts": len([a for a in analyses if not a.get("error")]),
        "signal_counts": {s: signals.count(s) for s in set(signals) if s},
        "top_stocks": [
            f"{c['name']} ({c.get('ticker', '?')}) — Score: {c['titan_k_score']}/10"
            for c in top_stocks
        ],
        "hidden_gems": [
            f"💎 {c['name']} ({c.get('ticker', '?')}) — {c.get('why_mentioned', '')}"
            for c in gems
        ],
        "paradigm_shifts": paradigm_shifts,
    }
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Minerva. Write a concise executive summary for Titan's morning briefing. Be direct, actionable, no fluff. Use plain text, no markdown."},
                {"role": "user", "content": f"Summarize today's blog analysis for the Telegram briefing:\n\n{json.dumps(summary_data, indent=2)}"},
            ],
            temperature=0.4,
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        # Fallback: manual summary
        top_names = ", ".join(c["name"] for c in top_stocks[:3]) if top_stocks else "None"
        return (
            f"Analyzed {summary_data['total_posts']} posts. "
            f"Top conviction: {top_names}. "
            f"{'Paradigm shift detected. ' if paradigm_shifts else ''}"
            f"Signals: {summary_data['signal_counts']}"
        )
