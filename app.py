"""Live stock screener dashboard.  Run:  streamlit run app.py
Data: Yahoo Finance via yfinance (free, ~15 min delayed for NSE). Signals only - NOT advice."""
import pandas as pd
import streamlit as st
from data import load_yfinance, synthetic
from signals import analyze

st.set_page_config(page_title="Stock Signal Screener", layout="wide")
st.title("📈 Stock Signal Screener (NSE)")
st.caption("Rule-based signals on daily data. Educational tool, not financial advice. Markets can and do go against any signal.")

DEFAULT = "RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS, ICICIBANK.NS, SBIN.NS, ITC.NS, LT.NS, BHARTIARTL.NS, TATAMOTORS.NS, SUNPHARMA.NS, MARUTI.NS"
with st.sidebar:
    tickers = [t.strip().upper() for t in st.text_area("Watchlist (comma separated, add .NS for NSE)", DEFAULT).split(",") if t.strip()]
    capital = st.number_input("Your capital (₹)", 10_000, 10_000_000, 100_000, 10_000)
    risk = st.slider("Risk per trade (% of capital)", 0.25, 2.0, 1.0, 0.25)
    stop = st.slider("Stop-loss distance (%)", 2.0, 10.0, 5.0, 0.5)
    demo = st.checkbox("Demo mode (fake data, for testing)")
    if st.button("🔄 Refresh data"):
        st.cache_data.clear()


@st.cache_data(ttl=900, show_spinner=False)
def get(symbol: str, demo: bool):
    return synthetic(seed=sum(map(ord, symbol)) % 1000) if demo else load_yfinance(symbol, start="2023-01-01")


rows, frames = [], {}
bar = st.progress(0.0, text="Fetching data...")
for i, t in enumerate(tickers):
    try:
        df = get(t, demo)
        frames[t] = df
        rows.append({"symbol": t, **analyze(df, capital, risk, stop)})
    except Exception as e:
        rows.append({"symbol": t, "verdict": "ERROR", "reasons": str(e)[:80]})
    bar.progress((i + 1) / len(tickers))
bar.empty()

res = pd.DataFrame(rows)
if not res.empty:
    order = {"BUY SIGNAL": 0, "WATCH": 1, "AVOID": 2}
    res = res.sort_values("verdict", key=lambda s: s.map(order).fillna(3)).reset_index(drop=True)
    st.dataframe(res, width="stretch", hide_index=True)

    pick = st.selectbox("Chart", [s for s in res["symbol"] if s in frames])
    if pick:
        d = frames[pick].tail(250).copy()
        d["SMA20"], d["SMA50"], d["SMA200"] = (frames[pick]["close"].rolling(n).mean().tail(250) for n in (20, 50, 200))
        st.line_chart(d[["close", "SMA20", "SMA50", "SMA200"]])
        r = res[res.symbol == pick].iloc[0]
        st.info(f"**{pick}: {r['verdict']}**  \n{r.get('reasons', '')}  \n"
                f"Stop-loss: ₹{r.get('stop_loss')}  |  Quantity for {risk}% risk: {r.get('qty_for_risk')} shares")
