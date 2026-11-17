"""Data loaders. Every loader returns a DataFrame with columns:
open, high, low, close, volume  and a DatetimeIndex."""
import numpy as np
import pandas as pd


def load_yfinance(symbol: str, start: str = "2015-01-01", end=None) -> pd.DataFrame:
    """Free daily data. Examples: ^NSEI (Nifty 50), RELIANCE.NS, BTC-USD."""
    import yfinance as yf

    raw = yf.download(symbol, start=start, end=end, auto_adjust=True, progress=False)
    if raw.empty:
        raise ValueError(f"No data for {symbol}")
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    raw.columns = [c.lower() for c in raw.columns]
    return raw[["open", "high", "low", "close", "volume"]].dropna()


def synthetic(n: int = 2500, seed: int = 7, start_price: float = 10000.0) -> pd.DataFrame:
    """Fake market with alternating bull/bear/sideways regimes. ONLY for testing."""
    rng = np.random.default_rng(seed)
    drift = np.zeros(n)
    vol = np.zeros(n)
    i = 0
    while i < n:
        length = int(rng.integers(60, 250))
        d, v = [(0.0006, 0.009), (-0.0007, 0.013), (0.0, 0.007)][int(rng.integers(0, 3))]
        drift[i:i + length], vol[i:i + length] = d, v
        i += length
    rets = rng.normal(drift, vol)
    close = start_price * np.exp(np.cumsum(rets))
    open_ = np.r_[start_price, close[:-1]] * (1 + rng.normal(0, 0.002, n))
    spread = np.abs(rng.normal(0, vol)) * close
    high = np.maximum(open_, close) + spread * rng.uniform(0.2, 1.0, n)
    low = np.minimum(open_, close) - spread * rng.uniform(0.2, 1.0, n)
    idx = pd.bdate_range("2015-01-01", periods=n)
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close,
                         "volume": rng.integers(1_000_000, 5_000_000, n)}, index=idx)
