import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from agents.analysts import (
    create_technical_agent,
    create_fundamental_agent,
    create_sentiment_agent,
    create_liquidity_agent,
    create_chief_officer
)
from market_data import get_gold_data

# Page config - mobile friendly
st.set_page_config(
    page_title="Gold Command Center",
    page_icon="🥇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

load_dotenv()

# Paths
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
HISTORY_FILE = LOG_DIR / "agent_history.json"

# Initialize session state
if "agents" not in st.session_state:
    st.session_state.agents = {
        "technical": create_technical_agent(),
        "fundamental": create_fundamental_agent(),
        "sentiment": create_sentiment_agent(),
        "liquidity": create_liquidity_agent(),
        "chief": create_chief_officer()
    }
if "last_run" not in st.session_state:
    st.session_state.last_run = None
if "market_data" not in st.session_state:
    st.session_state.market_data = None
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = None

def save_history(reports: list):
    history = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except:
            history = []
    history.append({
        "run_time": datetime.now().isoformat(),
        "reports": reports
    })
    # Keep last 50 runs
    history = history[-50:]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def load_today_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        today = datetime.now().date().isoformat()
        return [h for h in history if h["run_time"].startswith(today)]
    except:
        return []

def run_full_analysis():
    """Run all 4 analysts then Chief Officer"""
    market = get_gold_data()
    st.session_state.market_data = market

    tech = st.session_state.agents["technical"]
    fund = st.session_state.agents["fundamental"]
    sent = st.session_state.agents["sentiment"]
    liq = st.session_state.agents["liquidity"]
    chief = st.session_state.agents["chief"]

    # Run the four analysts
    tech_report = tech.analyze(market)
    fund_report = fund.analyze(market)
    sent_report = sent.analyze(market)
    liq_report = liq.analyze(market)

    # Prepare context for Chief
    context = f"""
Technical Analyst Report:
{json.dumps(tech_report, indent=2)}

Fundamental Analyst Report:
{json.dumps(fund_report, indent=2)}

Sentiment Analyst Report:
{json.dumps(sent_report, indent=2)}

Liquidity Analyst Report (Smart Money Concepts):
{json.dumps(liq_report, indent=2)}
"""
    chief_report = chief.analyze(market, extra_context=context)

    all_reports = [tech_report, fund_report, sent_report, liq_report, chief_report]
    save_history(all_reports)
    st.session_state.last_run = datetime.now().isoformat()
    return all_reports

# ========== UI ==========
st.markdown("""
<style>
    .agent-card {
        background: linear-gradient(135deg, #1e1e2f 0%, #2a2a40 100%);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid #3a3a55;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .status-green { color: #00e676; font-weight: bold; }
    .status-yellow { color: #ffea00; font-weight: bold; }
    .status-red { color: #ff1744; font-weight: bold; }
    .bias-bullish { color: #00e676; font-weight: 700; font-size: 1.2em; }
    .bias-bearish { color: #ff1744; font-weight: 700; font-size: 1.2em; }
    .bias-neutral { color: #ffea00; font-weight: 700; font-size: 1.2em; }
    .chief-card {
        background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
        border: 2px solid #00bcd4;
        border-radius: 16px;
        padding: 24px;
    }
    h1 { text-align: center; }
</style>
""", unsafe_allow_html=True)

st.title("🥇 Gold Command Center")
st.caption("Multi-Agent AI Trading Desk • Live Dashboard")

# Top controls
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    if st.button("🔄 Run Full Analysis Now", type="primary", use_container_width=True):
        with st.spinner("Agents are analyzing gold market..."):
            run_full_analysis()
        st.success("Analysis complete!")
        st.rerun()

with col2:
    auto = st.toggle("Auto refresh (60s)", value=False)

with col3:
    if st.button("Clear Selection", use_container_width=True):
        st.session_state.selected_agent = None
        st.rerun()

# Live Gold Price Banner
market = st.session_state.market_data or get_gold_data()
st.session_state.market_data = market

price = market.get("current_price", 0)
change = market.get("change_1d_pct", 0)
change_color = "green" if change >= 0 else "red"

st.markdown(f"""
<div style="background:#111; padding:16px 24px; border-radius:12px; margin:16px 0; text-align:center;">
    <span style="font-size:1.1em; color:#aaa;">Live Gold (XAUUSD)</span><br>
    <span style="font-size:2.2em; font-weight:700; color:white;">${price:,.2f}</span>
    <span style="font-size:1.3em; color:{change_color}; margin-left:12px;">{change:+.2f}%</span>
    <br><span style="font-size:0.85em; color:#666;">RSI: {market.get('rsi_14', 'N/A')} | SMA20: {market.get('sma_20', 'N/A')}</span>
</div>
""", unsafe_allow_html=True)

# Agent Cards
st.subheader("🏢 Trading Desk Agents")

agents = st.session_state.agents
agent_keys = ["technical", "fundamental", "sentiment", "liquidity", "chief"]

# Create 2x2 grid on desktop, stack on mobile
cols = st.columns(2)

for idx, key in enumerate(agent_keys):
    agent = agents[key]
    report = agent.last_report
    with cols[idx % 2]:
        bias = report.get("bias", "—") if report else "—"
        conf = report.get("confidence", 0) if report else 0
        status = agent.status
        status_class = "status-green" if status == "Ready" else ("status-yellow" if "Analyzing" in status else "status-red")

        bias_class = "bias-bullish" if bias == "Bullish" else ("bias-bearish" if bias == "Bearish" else "bias-neutral")

        card_style = "chief-card" if key == "chief" else "agent-card"

        st.markdown(f"""
        <div class="{card_style}">
            <h3 style="margin:0 0 8px 0;">{agent.name}</h3>
            <p style="margin:0; color:#888; font-size:0.9em;">{agent.role}</p>
            <p style="margin:8px 0;">Status: <span class="{status_class}">{status}</span></p>
            <p style="margin:4px 0;">Bias: <span class="{bias_class}">{bias}</span> &nbsp; Confidence: <b>{conf}%</b></p>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"View {agent.name} Details", key=f"btn_{key}", use_container_width=True):
            st.session_state.selected_agent = key
            st.rerun()

# Detail Panel
if st.session_state.selected_agent:
    key = st.session_state.selected_agent
    agent = agents[key]
    report = agent.last_report

    st.divider()
    st.subheader(f"📋 {agent.name} — Detailed Report")

    if report:
        c1, c2, c3 = st.columns(3)
        c1.metric("Bias", report.get("bias", "—"))
        c2.metric("Confidence", f"{report.get('confidence', 0)}%")
        c3.metric("Suggested Action", report.get("suggested_action", "—"))

        st.markdown("**Summary**")
        st.info(report.get("summary", "No summary"))

        st.markdown("**Key Points**")
        for p in report.get("key_points", []):
            st.write(f"• {p}")

        st.markdown("**Full Reasoning**")
        st.write(report.get("reasoning", "—"))

        if report.get("entry") or report.get("stop_loss") or report.get("take_profit"):
            st.markdown("**Levels**")
            lc1, lc2, lc3 = st.columns(3)
            lc1.metric("Entry", report.get("entry") or "—")
            lc2.metric("Stop Loss", report.get("stop_loss") or "—")
            lc3.metric("Take Profit", report.get("take_profit") or "—")

        st.caption(f"Generated at: {report.get('timestamp', '—')}")
    else:
        st.warning("No analysis yet. Click **Run Full Analysis Now** first.")

# Chief Officer Final Decision Highlight - PROMINENT
if agents["chief"].last_report:
    st.divider()
    st.subheader("🎯 CHIEF OFFICER — FINAL TRADE SIGNAL")
    cr = agents["chief"].last_report
    action = cr.get("suggested_action", "Hold")
    color = "#00e676" if action == "Buy" else ("#ff1744" if action == "Sell" else "#ffea00")
    entry = cr.get("entry") or "—"
    sl = cr.get("stop_loss") or "—"
    tp = cr.get("take_profit") or "—"
    conf = cr.get("confidence", 0)

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0a192f 0%, #112240 100%); 
                border: 3px solid {color}; 
                border-radius: 20px; 
                padding: 30px; 
                text-align: center;
                box-shadow: 0 0 30px {color}40;">
        <h1 style="color:{color}; margin:0; font-size: 3em; text-shadow: 0 0 20px {color};">{action.upper()}</h1>
        <p style="font-size:1.5em; margin:15px 0; color: #ccd6f6;">Confidence: <b>{conf}%</b></p>
        <p style="color:#8892b0; font-size:1.1em; margin-bottom: 25px;">{cr.get('summary', '')}</p>
        
        <div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap;">
            <div style="background: #0a192f; padding: 15px 25px; border-radius: 12px; border: 1px solid #233554;">
                <div style="color: #8892b0; font-size: 0.9em;">ENTRY</div>
                <div style="color: #64ffda; font-size: 1.8em; font-weight: bold;">{entry}</div>
            </div>
            <div style="background: #0a192f; padding: 15px 25px; border-radius: 12px; border: 1px solid #233554;">
                <div style="color: #8892b0; font-size: 0.9em;">STOP LOSS</div>
                <div style="color: #ff6b6b; font-size: 1.8em; font-weight: bold;">{sl}</div>
            </div>
            <div style="background: #0a192f; padding: 15px 25px; border-radius: 12px; border: 1px solid #233554;">
                <div style="color: #8892b0; font-size: 0.9em;">TAKE PROFIT</div>
                <div style="color: #00e676; font-size: 1.8em; font-weight: bold;">{tp}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("View Chief Officer Full Reasoning"):
        st.write(cr.get("reasoning", "—"))

# Today's Activity Log
st.divider()
st.subheader("📅 Today's Agent Activity")
today_runs = load_today_history()
if today_runs:
    for run in reversed(today_runs[-5:]):
        with st.expander(f"Run at {run['run_time'][11:19]}"):
            for r in run["reports"]:
                st.write(f"**{r.get('agent')}** → {r.get('bias')} ({r.get('confidence')}%) — {r.get('suggested_action')}")
else:
    st.info("No analysis runs yet today. Click the button above to start.")

# Footer
st.markdown("---")
st.caption("Gold Command Center • Powered by Groq free models • For educational & research purposes only. Not financial advice. Always paper trade first.")
