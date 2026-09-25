import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
from supabase import create_client

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)


def log(agent, symbol, status, message, payload=None):
    try:
        supabase.table("agent_reports").insert({
            "agent_name": agent,
            "symbol": symbol,
            "status": status,
            "message": message,
            "payload": payload or {}
        }).execute()
    except Exception as e:
        print(f"[log fail] {agent} {symbol} {status}: {e}")


def get_btc():
    r = requests.get(
        "https://api.binance.com/api/v3/klines",
        params={"symbol": "BTCUSDT", "interval": "15m", "limit": 100},
        timeout=15
    )
    r.raise_for_status()
    raw = r.json()
    df = pd.DataFrame(raw, columns=[
        "time", "open", "high", "low", "close", "volume", "ct", "qav",
        "trades", "tbb", "tbq", "ignore"
    ])
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = df[c].astype(float)
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df


def get_gold():
    df = yf.download("GC=F", period="5d", interval="15m",
                     auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError("Gold data empty from yfinance")
    df.columns = [c.lower() if isinstance(c, str) else c[0].lower()
                  for c in df.columns]
    df = df[["open", "high", "low", "close", "volume"]].dropna()
    return df


def atr(df, period=14):
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def make_signal(symbol, df):
    close = df["close"].squeeze()
    price = float(close.iloc[-1])
    a = float(atr(df).iloc[-1])
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])

    if ema20 > ema50:
        action = "BUY"
        entry = price
        sl = entry - 1.5 * a
        tp = entry + 3 * a
    elif ema20 < ema50:
        action = "SELL"
        entry = price
        sl = entry + 1.5 * a
        tp = entry - 3 * a
    else:
        action = "HOLD"
        entry = sl = tp = price

    return {
        "symbol": symbol,
        "action": action,
        "entry": round(entry, 2),
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "confidence": 0.65,
        "reason": f"EMA20={ema20:.2f} EMA50={ema50:.2f} ATR={a:.2f}",
        "agent_name": "SignalAgent",
        "status": "pending"
    }


def process(symbol, fetch_fn):
    log("DataAgent", symbol, "running", f"Fetching {symbol} data")
    try:
        df = fetch_fn()
    except Exception as e:
        log("DataAgent", symbol, "error", f"Fetch failed: {e}")
        return
    log("DataAgent", symbol, "done", f"Fetched {len(df)} candles")

    log("TechAgent", symbol, "running", "Computing EMA20/50 + ATR")
    try:
        sig = make_signal(symbol, df)
    except Exception as e:
        log("TechAgent", symbol, "error", f"Signal failed: {e}")
        return
    log("TechAgent", symbol, "done",
        f"{sig['action']} @ {sig['entry']}", sig)

    log("ReportAgent", symbol, "running", "Writing signal to DB")
    try:
        supabase.table("signals").insert(sig).execute()
        log("ReportAgent", symbol, "done",
            "Pending signal saved for Team Lead")
    except Exception as e:
        log("ReportAgent", symbol, "error", f"DB insert failed: {e}")


def main():
    log("System", "ALL", "running",
        f"Agent cycle started at {datetime.utcnow().isoformat()}")
    process("BTC", get_btc)
    process("GOLD", get_gold)
    log("System", "ALL", "done", "Agent cycle complete")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("System", "ALL", "error", str(e))
        raise
