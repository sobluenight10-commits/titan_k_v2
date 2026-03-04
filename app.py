import streamlit as st
import json, os
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from scraper import fetch_posts
from analyzer import analyze_post
from market_data import fetch_market_snapshot, calculate_titan_k_index
from portfolio import fetch_portfolio_data, generate_morning_briefing
from config import WEIGHTS, DATA_FILE

st.set_page_config(
    page_title="🔱 titan_K Investment Dashboard",
    page_icon="🔱",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
body { background-color: #0a0a1a; color: #e0e0e0; }
.stApp { background: linear-gradient(135deg, #0a0a1a 0%, #0d1b2a 100%); }
.metric-card {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border: 1px solid #0f3460;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin: 5px;
}
.gem-card {
    background: linear-gradient(135deg, #1a1200, #2d2000);
    border: 2px solid #FFD700;
    border-radius: 12px;
    padding: 15px;
    margin: 8px 0;
}
h1, h2, h3 { color: #FFD700 !important; }
</style>
""", unsafe_allow_html=True)


def load_data() -> dict:
    os.makedirs("data", exist_ok=True)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
                if "analyses" not in loaded:
                    loaded["analyses"] = []
                if "stocks" not in loaded:
                    loaded["stocks"] = []
                if "last_run" not in loaded:
                    loaded["last_run"] = None
                return loaded
            except:
                pass
    return {"analyses": [], "stocks": [], "last_run": None}


def save_data(data: dict):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔱 titan_K Control")
    st.markdown("---")
    days_back = st.selectbox(
        "📅 Fetch posts from:",
        options=[1, 3, 7, 14, 30, 90],
        format_func=lambda x: f"Past {x} day(s)",
        index=0
    )
    run_btn = st.button("🚀 Run titan_K Analysis", use_container_width=True, type="primary")
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    show_all = st.checkbox("Show all stocks (incl. low score)", value=False)
    min_score = st.slider("Min titan_K score", 1.0, 10.0, 6.0, 0.5)
    st.markdown("---")
    data = load_data()
    if data.get("last_run"):
        st.markdown(f"**Last run:** {data['last_run']}")
    st.markdown(f"**Total articles:** {len(data.get('analyses', []))}")
    st.markdown(f"**Total stocks tracked:** {len(data.get('stocks', []))}")


# ── Run Analysis ──────────────────────────────────────────────────────────────
if run_btn:
    with st.spinner("🔱 titan_K is analyzing the blog..."):
        posts = fetch_posts(days_back=days_back)
        if not posts:
            st.warning("No posts found in this date range. Try a longer period.")
        else:
            progress = st.progress(0)
            new_analyses = []
            new_stocks = []
            for i, post in enumerate(posts):
                st.write(f"🔍 Analyzing: {post['title'][:70]}...")
                result = analyze_post(post)
                if not result.get("error"):
                    new_analyses.append(result)
                    new_stocks.extend(result.get("companies", []))
                progress.progress((i + 1) / len(posts))

            existing_urls = {a.get("url") for a in data.get("analyses", [])}
            data["analyses"] = data.get("analyses", []) + [a for a in new_analyses if a.get("url") not in existing_urls]
            existing_stock_keys = {(s.get("name"), s.get("date_mentioned")) for s in data.get("stocks", [])}
            data["stocks"] = data.get("stocks", []) + [
                s for s in new_stocks
                if (s.get("name"), s.get("date_mentioned")) not in existing_stock_keys
            ]
            data["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(data)
            st.success(f"✅ Done! Analyzed {len(new_analyses)} posts, found {len(new_stocks)} companies.")
            st.rerun()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🔱 titan_K Investment Intelligence Dashboard")
st.markdown(f"*Your invincible investment weapon — {datetime.now().strftime('%Y-%m-%d %H:%M')} Berlin Time*")
st.markdown("---")


# ── Market Snapshot ───────────────────────────────────────────────────────────
st.markdown("## 📡 Live Market Pulse")
with st.spinner("Fetching market data..."):
    snapshot = fetch_market_snapshot()
    titan_score = calculate_titan_k_index(snapshot, WEIGHTS)

col1, col2, col3, col4 = st.columns(4)
score_color = "#00ff88" if titan_score >= 60 else "#FFD700" if titan_score >= 45 else "#ff4444"
with col1:
    st.markdown(f"""<div class="metric-card">
        <h2 style="color:{score_color};font-size:2.5em;">{titan_score}</h2>
        <p style="color:#aaa;">🔱 titan_K Index</p>
        <p style="color:{score_color};font-size:0.8em;">{"🟢 DEPLOY" if titan_score>=60 else "🟡 WAIT" if titan_score>=45 else "🔴 CAUTION"}</p>
    </div>""", unsafe_allow_html=True)

key_inds = [("VIX", "Fear Gauge"), ("SOX", "Chip Index"), ("Gold", "Chaos Hedge")]
for (ind, label), col in zip(key_inds, [col2, col3, col4]):
    d = snapshot.get(ind, {})
    val = d.get("value", "N/A")
    chg = d.get("change_pct", 0) or 0
    sig = d.get("signal", "")
    chg_color = "#00ff88" if chg >= 0 else "#ff4444"
    with col:
        st.markdown(f"""<div class="metric-card">
            <h3 style="color:#FFD700;">{ind}</h3>
            <p style="font-size:1.4em;">{val}</p>
            <p style="color:{chg_color};">{'+' if chg>=0 else ''}{chg}%</p>
            <p style="font-size:0.75em;color:#aaa;">{sig[:40]}</p>
        </div>""", unsafe_allow_html=True)

with st.expander("📊 Full 30-Indicator Breakdown"):
    rows = []
    from config import WEIGHTS
    for ind, w in WEIGHTS.items():
        d = snapshot.get(ind, {})
        rows.append({
            "Indicator": ind,
            "Weight": f"{w*100:.1f}%",
            "Value": d.get("value", "—"),
            "Change %": d.get("change_pct", "—"),
            "Signal": d.get("signal", "—")
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("---")


# ── MY PORTFOLIO ──────────────────────────────────────────────────────────────
st.markdown("## 💼 My Invincible Portfolio")
st.markdown("*Live tracking of your holdings with titan_K analysis*")

with st.spinner("Fetching your portfolio data..."):
    portfolio_data = fetch_portfolio_data()

if portfolio_data:
    df_port = pd.DataFrame(portfolio_data)
    total_stocks = len(portfolio_data)
    strong_buys = sum(1 for s in portfolio_data if "STRONG BUY" in s.get("recommendation", ""))
    reviews = sum(1 for s in portfolio_data if "REVIEW" in s.get("recommendation", ""))
    avg_score = round(sum(s.get("titan_k_score", 0) for s in portfolio_data) / total_stocks, 1)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <h2 style="color:#FFD700;">{total_stocks}</h2>
            <p style="color:#aaa;">Total Holdings</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <h2 style="color:#00ff88;">{strong_buys}</h2>
            <p style="color:#aaa;">Strong Buy</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <h2 style="color:#ff4444;">{reviews}</h2>
            <p style="color:#aaa;">Need Review</p>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <h2 style="color:#FFD700;">{avg_score}/10</h2>
            <p style="color:#aaa;">Avg titan_K Score</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    display_cols = ["name", "ticker", "broker", "category", "current_price",
                    "change_1d_pct", "return_pct", "target_price", "titan_k_score", "recommendation"]
    show_cols = [c for c in display_cols if c in df_port.columns]
    st.dataframe(
        df_port[show_cols].rename(columns={
            "name": "Company", "ticker": "Ticker", "broker": "Broker",
            "category": "Category", "current_price": "Current Price",
            "change_1d_pct": "Today %", "return_pct": "Your Return %",
            "target_price": "Target Price", "titan_k_score": "titan_K Score",
            "recommendation": "Recommendation"
        }),
        use_container_width=True,
        hide_index=True
    )

    chart_data = [s for s in portfolio_data if s.get("return_pct") is not None]
    if chart_data:
        fig = px.bar(
            pd.DataFrame(chart_data),
            x="ticker", y="return_pct", color="category",
            title="Your Portfolio Returns by Holding",
            labels={"ticker": "Stock", "return_pct": "Return %", "category": "Category"},
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.3)
        fig.update_layout(plot_bgcolor="#0d1b2a", paper_bgcolor="#0a0a1a", font_color="#e0e0e0")
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Full Thesis & Action Points"):
        for s in sorted(portfolio_data, key=lambda x: x.get("titan_k_score", 0), reverse=True):
            rec = s.get("recommendation", "")
            st.markdown(f"""
**{s['name']}** ({s['ticker']}) — Score: **{s.get('titan_k_score')}/10**

📌 *Thesis:* {s.get('thesis', '')}

🎯 *Recommendation:* {rec}

💰 Buy price: {s.get('buy_price')} | Current: {s.get('current_price')} | Target: {s.get('target_price')}

---""")

st.markdown("---")


# ── Stock Watchlist ───────────────────────────────────────────────────────────
st.markdown("## 🏆 Invincible Portfolio Watchlist")
st.markdown("*Ranked by titan_K conviction score — buy/watch candidates from blog*")

stocks = data.get("stocks", [])
if not stocks:
    st.info("👆 Click 'Run titan_K Analysis' in the sidebar to populate the watchlist.")
else:
    df = pd.DataFrame(stocks)
    if "titan_k_score" in df.columns:
        df = df[df["titan_k_score"] >= (0 if show_all else min_score)]
        df = df.sort_values("titan_k_score", ascending=False)
    if "name" in df.columns:
        df = df.drop_duplicates(subset=["name"])

    gems = df[df["hidden_gem"] == True] if "hidden_gem" in df.columns else pd.DataFrame()
    if not gems.empty:
        st.markdown("### 💎 Hidden Gems")
        for _, row in gems.iterrows():
            st.markdown(f"""<div class="gem-card">
                <b style="color:#FFD700;font-size:1.2em;">💎 {row.get('name','')} ({row.get('ticker','N/A')})</b>
                &nbsp;&nbsp;<span style="background:#FFD700;color:#000;padding:2px 8px;border-radius:10px;">Score: {row.get('titan_k_score','')}/10</span>
                &nbsp;&nbsp;<span style="color:#aaa;">{row.get('future_state_category','')}</span><br><br>
                <b>Why:</b> {row.get('why_mentioned','')}<br>
                <b>When to buy:</b> {row.get('when_to_buy','')}<br>
                <b>Target:</b> {row.get('target_price','N/A')} &nbsp;|&nbsp; <b>Risk:</b> {row.get('risk','')}<br>
                <b>TR (DE):</b> {row.get('available_trade_republic','')} &nbsp;|&nbsp; <b>Kiwoom (KR):</b> {row.get('available_kiwoom','')}
            </div>""", unsafe_allow_html=True)

    st.markdown("### 📋 Full Watchlist")
    display_cols = ["name", "ticker", "future_state_category", "titan_k_score",
                    "sentiment", "when_to_buy", "target_price", "available_trade_republic", "date_mentioned"]
    show_cols = [c for c in display_cols if c in df.columns]
    if show_cols:
        st.dataframe(df[show_cols].rename(columns={
            "name": "Company", "ticker": "Ticker",
            "future_state_category": "Category", "titan_k_score": "titan_K Score",
            "sentiment": "Signal", "when_to_buy": "When to Buy",
            "target_price": "Target Price", "available_trade_republic": "Trade Republic",
            "date_mentioned": "Date"
        }), use_container_width=True, hide_index=True)

    if "titan_k_score" in df.columns and len(df) > 0:
        st.markdown("### 📊 Score Distribution")
        fig = px.bar(
            df.head(20), x="name", y="titan_k_score", color="future_state_category",
            title="Top 20 Stocks by titan_K Conviction Score",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(plot_bgcolor="#0d1b2a", paper_bgcolor="#0a0a1a",
                          font_color="#e0e0e0", xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# ── Blog Feed ─────────────────────────────────────────────────────────────────
st.markdown("## 📰 Blog Intelligence Feed")
analyses = data.get("analyses", [])
if not analyses:
    st.info("No articles analyzed yet. Run the analysis first.")
else:
    for a in sorted(analyses, key=lambda x: x.get("date", ""), reverse=True)[:20]:
        sig = a.get("watch_signal", "")
        sig_color = "#00ff88" if "STRONG BUY" in sig else "#FFD700" if "WATCH" in sig else "#ff4444"
        paradigm = "🌍 PARADIGM SHIFT" if a.get("paradigm_shift") else ""

        with st.expander(f"{'💎' if a.get('paradigm_shift') else '📰'} {a.get('date','')} | {a.get('title','')[:80]} {paradigm}"):
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown(f"**📌 Summary:** {a.get('summary_en','')}")
                st.markdown(f"**💡 Insight:** {a.get('investment_insight','')}")
                st.markdown(f"**🌍 Macro context:** {a.get('global_macro_context','')}")
                if a.get("paradigm_description"):
                    st.markdown(f"**🌍 Paradigm:** {a.get('paradigm_description','')}")
                st.markdown(f"**🔑 Keywords:** {', '.join(a.get('keywords',[]))}")
            with c2:
                st.markdown(f"<p style='color:{sig_color};font-size:1.3em;'><b>{sig}</b></p>", unsafe_allow_html=True)
                st.markdown(f"**Indicators:** {', '.join(a.get('titan_k_indicators',[]))}")
                st.markdown(f"[📖 Read original]({a.get('url','')})")

            companies = a.get("companies", [])
            if companies:
                st.markdown("**🏢 Companies:**")
                for c in companies:
                    gem = "💎" if c.get("hidden_gem") else ""
                    st.markdown(
                        f"- {gem} **{c.get('name','')}** ({c.get('ticker','N/A')}) "
                        f"| Score: **{c.get('titan_k_score','')}/10** "
                        f"| {c.get('sentiment','').upper()} "
                        f"| Buy when: {c.get('when_to_buy','')}"
                    )
