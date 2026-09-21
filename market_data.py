import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

def get_gold_data():
    """Fetch live-ish gold (XAUUSD) data using Yahoo Finance GC=F (Gold Futures)"""
    try:
        ticker = yf.Ticker("GC=F")
        info = ticker.info
        hist = ticker.history(period="5d", interval="1h")

        if hist.empty:
            hist = ticker.history(period="1mo", interval="1d")

        current_price = float(hist["Close"].iloc[-1]) if not hist.empty else info.get("regularMarketPrice", 0)

        # Simple technical indicators
        close = hist["Close"]
        sma20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else current_price
        sma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else current_price

        # RSI calculation
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1] if len(close) >= 14 else 50

        # Recent change
        change_1d = ((current_price - close.iloc[-2]) / close.iloc[-2] * 100) if len(close) > 1 else 0

        data = {
            "symbol": "XAUUSD (GC=F)",
            "current_price": round(current_price, 2),
            "change_1d_pct": round(change_1d, 2),
            "sma_20": round(float(sma20), 2),
            "sma_50": round(float(sma50), 2) if not pd.isna(sma50) else None,
            "rsi_14": round(float(rsi), 1) if not pd.isna(rsi) else 50,
            "high_24h": round(float(hist["High"].iloc[-24:].max()), 2) if len(hist) >= 24 else round(current_price, 2),
            "low_24h": round(float(hist["Low"].iloc[-24:].min()), 2) if len(hist) >= 24 else round(current_price, 2),
            "volume": int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0,
            "timestamp": datetime.now().isoformat(),
            "note": "Data from Yahoo Finance Gold Futures (GC=F). Close enough for analysis."
        }
        return data
    except Exception as e:
        return {
            "symbol": "XAUUSD",
            "current_price": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
