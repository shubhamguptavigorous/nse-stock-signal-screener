"""Transparent scoring of a stock from daily OHLCV. Every point is explained in reasons."""
import numpy as np
import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    d = close.diff()
    g = d.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    l = (-d.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    return 100 - 100 / (1 + g / l.replace(0, np.nan))


def analyze(df: pd.DataFrame, capital: float = 100_000, risk_pct: float = 1.0, stop_pct: float = 5.0) -> dict:
    c = df["close"]
    if len(c) < 210:
        return {"verdict": "NO DATA", "score": 0, "reasons": "Need 210+ days of history"}
    sma20, sma50, sma200 = (c.rolling(n).mean().iloc[-1] for n in (20, 50, 200))
    px, r = float(c.iloc[-1]), float(rsi(c).iloc[-1])
    hi55 = float(df["high"].rolling(55).max().shift(1).iloc[-1])
    ret_3m = float(px / c.iloc[-63] - 1) * 100

    score, why = 0, []
    if px > sma200: score += 1; why.append("above 200-day avg (long-term uptrend)")
    else: score -= 1; why.append("below 200-day avg (long-term downtrend)")
    if sma20 > sma50: score += 1; why.append("20-day above 50-day (momentum up)")
    else: score -= 1; why.append("20-day below 50-day (momentum weak)")
    if 40 <= r <= 65: score += 1; why.append(f"RSI {r:.0f} healthy")
    elif r > 75: score -= 1; why.append(f"RSI {r:.0f} overbought, risky to chase")
    elif r < 30: why.append(f"RSI {r:.0f} oversold (bounce possible, trend still decides)")
    if px > hi55: score += 1; why.append("breaking 55-day high")
    if ret_3m > 0: score += 1; why.append(f"3-month return +{ret_3m:.1f}%")
    else: why.append(f"3-month return {ret_3m:.1f}%")

    verdict = "BUY SIGNAL" if score >= 4 else "WATCH" if score >= 2 else "AVOID"
    if r > 75 and verdict == "BUY SIGNAL": verdict = "WATCH"  # don't chase overbought
    stop = px * (1 - stop_pct / 100)
    qty = int((capital * risk_pct / 100) / (px - stop)) if px > stop else 0
    qty = min(qty, int(capital // px))
    return {"verdict": verdict, "score": score, "price": round(px, 2), "RSI": round(r, 1),
            "3m_%": round(ret_3m, 1), "stop_loss": round(stop, 2), "qty_for_risk": qty,
            "reasons": "; ".join(why)}
