"""Các chỉ báo kỹ thuật: MA, MACD, Stochastic, MFI, ADX, ATR, Heikin Ashi.

Mọi hàm nhận DataFrame có cột open, high, low, close, volume (chữ thường).
"""
import numpy as np
import pandas as pd


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _wilder(s: pd.Series, n: int) -> pd.Series:
    """Làm mượt kiểu Wilder (RMA) – dùng cho ATR, ADX."""
    return s.ewm(alpha=1 / n, adjust=False).mean()


def macd(df, fast=12, slow=26, signal=9) -> pd.DataFrame:
    line = ema(df["close"], fast) - ema(df["close"], slow)
    sig = ema(line, signal)
    return pd.DataFrame({"macd": line, "signal": sig, "hist": line - sig})


def stoch(df, k=14, smooth_k=3, d=3) -> pd.DataFrame:
    lo = df["low"].rolling(k, min_periods=k).min()
    hi = df["high"].rolling(k, min_periods=k).max()
    rng = (hi - lo).replace(0, np.nan)
    raw = 100 * (df["close"] - lo) / rng
    kk = raw.rolling(smooth_k, min_periods=1).mean()
    return pd.DataFrame({"k": kk, "d": kk.rolling(d, min_periods=1).mean()})


def mfi(df, n=14) -> pd.Series:
    """Money Flow Index 0..100. Trả về NaN nếu không có khối lượng (forex)."""
    tp = (df["high"] + df["low"] + df["close"]) / 3
    flow = tp * df["volume"]
    up = flow.where(tp.diff() > 0, 0.0).rolling(n, min_periods=n).sum()
    down = flow.where(tp.diff() < 0, 0.0).rolling(n, min_periods=n).sum()
    total = up + down
    return (100 * up / total.replace(0, np.nan)).clip(0, 100)


def atr(df, n=14) -> pd.Series:
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()],
                   axis=1).max(axis=1)
    return _wilder(tr, n)


def adx(df, n=14) -> pd.DataFrame:
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    tr = atr(df, n)
    pdi = 100 * _wilder(plus_dm, n) / tr.replace(0, np.nan)
    mdi = 100 * _wilder(minus_dm, n) / tr.replace(0, np.nan)
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return pd.DataFrame({"adx": _wilder(dx.fillna(0), n), "pdi": pdi, "mdi": mdi})


def heikin_ashi(df) -> pd.DataFrame:
    ha_close = (df["open"] + df["high"] + df["low"] + df["close"]) / 4
    ha_open = np.empty(len(df))
    o, c = df["open"].to_numpy(), ha_close.to_numpy()
    ha_open[0] = (o[0] + df["close"].iloc[0]) / 2
    for i in range(1, len(df)):
        ha_open[i] = (ha_open[i - 1] + c[i - 1]) / 2
    ha_open = pd.Series(ha_open, index=df.index)
    return pd.DataFrame({
        "open": ha_open,
        "close": ha_close,
        "high": pd.concat([df["high"], ha_open, ha_close], axis=1).max(axis=1),
        "low": pd.concat([df["low"], ha_open, ha_close], axis=1).min(axis=1),
    })
