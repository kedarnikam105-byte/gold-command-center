import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client

st.set_page_config(
    page_title="Trading Signal App",
    page_icon="chart",
    layout="wide"
)

try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )
except Exception as e:
    st.error(f"Supabase connection failed: {e}")
    st.stop()

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60_000, key="auto")
except Exception:
    pass

st.sidebar.title("Trading Signal App")
role = st.sidebar.radio("Login as", ["Trader", "Team Lead", "Agent Monitor"])

if st.sidebar.button("Refresh now"):
    st.rerun()

st.sidebar.caption(f"UTC: {datetime.utcnow():%Y-%m-%d %H:%M:%S}")


if role == "Trader":
    st.title("Trade Signals")
    symbol = st.selectbox("Select market", ["BTC", "GOLD"])

    res = (
        supabase.table("signals")
        .select("*")
        .eq("symbol", symbol)
        .eq("status", "approved")
        .order("approved_at", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        st.warning("No approved signal for this market yet.")
    else:
        s = res.data[0]
        st.subheader(f"{s['symbol']} - {s['action']}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Entry", s["entry"])
        c2.metric("Stop Loss", s["sl"])
        c3.metric("Take Profit", s["tp"])

        st.markdown(f"**Confidence:** {s['confidence']}")
        st.markdown(f"**Reason:** {s['reason']}")
        st.markdown(
            f"**Approved by:** {s.get('approved_by','-')} "
            f"at {s.get('approved_at','-')}"
        )

    st.divider()
    st.caption(f"Last refreshed: {datetime.utcnow():%Y-%m-%d %H:%M:%S}")


elif role == "Team Lead":
    st.title("Team Lead - Approve Signals")

    pend = (
        supabase.table("signals")
        .select("*")
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )

    if not pend.data:
        st.info("No pending signals.")
    else:
        for s in pend.data:
            title = f"{s['symbol']} - {s['action']} ({s['created_at']})"
            with st.expander(title, expanded=True):
                action = st.selectbox(
                    "Action", ["BUY", "SELL", "HOLD"],
                    index=["BUY", "SELL", "HOLD"].index(s["action"]),
                    key=f"a{s['id']}"
                )
                entry = st.number_input(
                    "Entry", value=float(s["entry"] or 0), key=f"e{s['id']}"
                )
                sl = st.number_input(
                    "SL", value=float(s["sl"] or 0), key=f"s{s['id']}"
                )
                tp = st.number_input(
                    "TP", value=float(s["tp"] or 0), key=f"t{s['id']}"
                )
                reason = st.text_area(
                    "Reason", value=s["reason"] or "", key=f"r{s['id']}"
                )

                c1, c2 = st.columns(2)
                if c1.button("Approve", key=f"ap{s['id']}"):
                    supabase.table("signals").update({
                        "action": action,
                        "entry": entry,
                        "sl": sl,
                        "tp": tp,
                        "reason": reason,
                        "status": "approved",
                        "approved_by": "TeamLead",
                        "approved_at": datetime.utcnow().isoformat()
                    }).eq("id", s["id"]).execute()
                    st.success("Approved.")
                    st.rerun()

                if c2.button("Reject", key=f"rj{s['id']}"):
                    supabase.table("signals").update({
                        "status": "rejected",
                        "approved_by": "TeamLead",
                        "approved_at": datetime.utcnow().isoformat()
                    }).eq("id", s["id"]).execute()
                    st.warning("Rejected.")
                    st.rerun()

    st.divider()
    st.subheader("History (last 20)")
    hist = (
        supabase.table("signals")
        .select("id,symbol,action,entry,sl,tp,status,approved_by,created_at")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    if hist.data:
        st.dataframe(pd.DataFrame(hist.data), use_container_width=True)


else:
    st.title("Agent Activity Monitor")

    reports = (
        supabase.table("agent_reports")
        .select("*")
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )

    if not reports.data:
        st.info("No agent activity yet.")
    else:
        df = pd.DataFrame(reports.data)
        df = df[["created_at", "agent_name", "symbol", "status", "message"]]

        st.subheader("Latest agent actions")
        st.dataframe(df, use_container_width=True)

        st.subheader("Filter")
        agent = st.selectbox(
            "Agent", ["All"] + sorted(df["agent_name"].dropna().unique())
        )
        if agent != "All":
            st.dataframe(
                df[df["agent_name"] == agent],
                use_container_width=True
            )

        st.subheader("Messages (latest 30)")
        for _, r in df.head(30).iterrows():
            st.text(
                f"[{r['created_at']}] {r['agent_name']} "
                f"({r['symbol']}) {r['status']}: {r['message']}"
            )
