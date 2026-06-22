"""Reusable indicator + data helpers (pure pandas/numpy, Wilder-smoothed).

Self-contained module for the swingbot package. Ported from scripts/indicators.py
with additions: sma, ema, rsi.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def load_csv(path: str, weekdays_only: bool = False) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["dt"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("dt").sort_index()
    df = df[~df[["open", "high", "low", "close"]].isna().any(axis=1)]
    if weekdays_only:
        df = df[df.index.dayofweek < 5]
    return df[["open", "high", "low", "close", "volume"]]


def rma(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(alpha=1 / n, adjust=False).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    pc = df["close"].shift(1)
    return pd.concat(
        [df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()],
        axis=1,
    ).max(axis=1)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return rma(true_range(df), n)


def adx(df: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    up = df["high"].diff()
    dn = -df["low"].diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    atr_ = rma(true_range(df), n)
    plus_di = 100 * rma(pd.Series(plus_dm, index=df.index), n) / atr_
    minus_di = 100 * rma(pd.Series(minus_dm, index=df.index), n) / atr_
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return pd.DataFrame({"plus_di": plus_di, "minus_di": minus_di, "adx": rma(dx, n)})


def swing_pivots(df: pd.DataFrame, k: int = 3):
    highs, lows = df["high"].values, df["low"].values
    n = len(df)
    piv = []
    for i in range(k, n - k):
        win_h = highs[i - k : i + k + 1]
        win_l = lows[i - k : i + k + 1]
        if highs[i] == win_h.max() and win_h.argmax() == k:
            piv.append((i, "H", highs[i]))
        elif lows[i] == win_l.min() and win_l.argmin() == k:
            piv.append((i, "L", lows[i]))
    cleaned = []
    for p in piv:
        if cleaned and cleaned[-1][1] == p[1]:
            if (p[1] == "H" and p[2] > cleaned[-1][2]) or (
                p[1] == "L" and p[2] < cleaned[-1][2]
            ):
                cleaned[-1] = p
        else:
            cleaned.append(p)
    return cleaned


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = rma(gain, n)
    avg_loss = rma(loss, n)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    out = out.where(avg_loss != 0, 100.0)   # all-up → 100
    out = out.where(avg_gain != 0, 0.0)      # all-down → 0
    return out
