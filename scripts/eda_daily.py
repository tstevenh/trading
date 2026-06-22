#!/usr/bin/env python3
"""Step 0 — Daily characterization of an instrument from a Dukascopy CSV.

Goal: understand the *nature* of the instrument (trend vs range, volatility,
swing duration, return distribution) so the strategy hypothesis is grounded in
how the market actually behaves — NOT to mine for a magic rule.

All indicators implemented in pure pandas/numpy (Wilder smoothing etc.) so the
exact same functions can be reused by the live bot.
"""
from __future__ import annotations

import sys
import numpy as np
import pandas as pd


# ----------------------------- data loading ------------------------------- #
def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["dt"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("dt").sort_index()
    # drop zero-volume / weekend artifacts if any slipped through
    df = df[~df[["open", "high", "low", "close"]].isna().any(axis=1)]
    return df[["open", "high", "low", "close", "volume"]]


# ----------------------------- indicators --------------------------------- #
def rma(s: pd.Series, n: int) -> pd.Series:
    """Wilder's smoothing (RMA)."""
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
    tr = true_range(df)
    atr_ = rma(tr, n)
    plus_di = 100 * rma(pd.Series(plus_dm, index=df.index), n) / atr_
    minus_di = 100 * rma(pd.Series(minus_dm, index=df.index), n) / atr_
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    out = pd.DataFrame({"plus_di": plus_di, "minus_di": minus_di, "adx": rma(dx, n)})
    return out


def efficiency_ratio(close: pd.Series, n: int = 10) -> pd.Series:
    """Kaufman ER: net move / sum of absolute moves. ~1 trending, ~0 choppy."""
    change = (close - close.shift(n)).abs()
    volatility = close.diff().abs().rolling(n).sum()
    return change / volatility.replace(0, np.nan)


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


# ----------------------------- swing analysis ------------------------------ #
def swing_pivots(df: pd.DataFrame, k: int = 3):
    """Fractal pivots: high[i] is a swing high if it's the max of [i-k, i+k]."""
    highs, lows = df["high"].values, df["low"].values
    n = len(df)
    piv = []  # (idx, type, price)
    for i in range(k, n - k):
        win_h = highs[i - k : i + k + 1]
        win_l = lows[i - k : i + k + 1]
        if highs[i] == win_h.max() and (win_h.argmax() == k):
            piv.append((i, "H", highs[i]))
        elif lows[i] == win_l.min() and (win_l.argmin() == k):
            piv.append((i, "L", lows[i]))
    # collapse consecutive same-type pivots, keeping the most extreme
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


def swing_stats(df: pd.DataFrame, atr_series: pd.Series, k: int = 3):
    piv = swing_pivots(df, k)
    durations, amplitudes_atr = [], []
    for a, b in zip(piv, piv[1:]):
        dur = b[0] - a[0]
        amp = abs(b[2] - a[2])
        atr_at = atr_series.iloc[a[0]]
        durations.append(dur)
        if atr_at and not np.isnan(atr_at):
            amplitudes_atr.append(amp / atr_at)
    return np.array(durations), np.array(amplitudes_atr)


# ----------------------------- report -------------------------------------- #
def analyze(name: str, path: str) -> str:
    df = load(path)
    out = []
    w = out.append

    w(f"\n## {name}\n")
    w(f"- **Span:** {df.index[0].date()} → {df.index[-1].date()}  ({len(df)} daily bars)")
    w(f"- **Price range:** {df['close'].min():.3f} → {df['close'].max():.3f}  "
      f"(start {df['close'].iloc[0]:.3f}, end {df['close'].iloc[-1]:.3f})")

    # returns
    ret = df["close"].pct_change()
    logret = np.log(df["close"]).diff()
    bh = df["close"].iloc[-1] / df["close"].iloc[0] - 1
    w(f"- **Buy & hold total return:** {pct(bh)}")
    w(f"- **Daily return:** mean {pct(ret.mean())}, std {pct(ret.std())}, "
      f"skew {ret.skew():.2f}, kurtosis {ret.kurtosis():.1f}")

    # ---- trend vs range ----
    a = adx(df)
    df["atr"] = atr(df)
    df["atr_pct"] = df["atr"] / df["close"]
    df["sma200"] = df["close"].rolling(200).mean()
    er = efficiency_ratio(df["close"], 10)

    adx_v = a["adx"].dropna()
    trending = (adx_v > 25).mean()
    ranging = (adx_v < 20).mean()
    above200 = (df["close"] > df["sma200"]).mean()
    # return autocorrelation (momentum vs mean-reversion)
    ac = {lag: logret.autocorr(lag) for lag in (1, 2, 3, 5, 10)}

    w("\n**Trend vs range character**")
    w(f"- ADX>25 (trending): {pct(trending)} of days | ADX<20 (ranging): {pct(ranging)} of days")
    w(f"- Days above 200-SMA: {pct(above200)}  → directional bias")
    w(f"- Mean efficiency ratio (10d): {er.mean():.2f}  (closer to 1 = cleaner trends)")
    w(f"- Daily log-return autocorrelation: "
      + ", ".join(f"lag{l}={v:+.3f}" for l, v in ac.items()))
    w("  → note: near-zero 1-day autocorrelation is NORMAL for liquid markets and does")
    w("    NOT mean trend-following fails. The trend lives in the multi-day swing/200-SMA")
    w("    structure below, not in predicting tomorrow from today.")
    # macro-trend evidence: how often a 50>200 SMA regime persists
    sma50 = df["close"].rolling(50).mean()
    bull_regime = (sma50 > df["sma200"]).mean()
    w(f"  → macro trend regime (50-SMA > 200-SMA): {pct(bull_regime)} of days")

    # ---- volatility ----
    atr_pct_now = df["atr_pct"].iloc[-1]
    w("\n**Volatility (stop/target sizing)**")
    w(f"- ATR(14) now: {df['atr'].iloc[-1]:.3f}  ({pct(atr_pct_now)} of price)")
    w(f"- ATR% percentiles: "
      f"p10={pct(df['atr_pct'].quantile(.1))}, median={pct(df['atr_pct'].median())}, "
      f"p90={pct(df['atr_pct'].quantile(.9))}")
    rng = (df["high"] - df["low"]) / df["close"]
    w(f"- Daily range %: median {pct(rng.median())}, p90 {pct(rng.quantile(.9))}")

    # ---- swings (does a 2-3 day hold fit?) ----
    dur, amp = swing_stats(df, df["atr"], k=3)
    if len(dur):
        w("\n**Swing structure (k=3 fractal pivots)**")
        w(f"- Avg swing duration: {dur.mean():.1f} bars (median {np.median(dur):.0f}), "
          f"so a 2-3 day hold captures a typical leg: "
          f"{'YES' if np.median(dur) >= 2 else 'borderline'}")
        w(f"- Avg swing amplitude: {amp.mean():.1f}× ATR (median {np.median(amp):.1f}×)")
        # fraction of swings >= 2x ATR → room for 2:1 R:R
        big = (amp >= 2).mean()
        w(f"- Swings ≥ 2× ATR: {pct(big)}  → these offer room for ≥2:1 R:R targets")

    return "\n".join(out)


if __name__ == "__main__":
    pairs = [
        ("XAU/USD (Gold)", "data/raw/xauusd_d1.csv"),
        ("EUR/USD", "data/raw/eurusd_d1.csv"),
    ]
    report = ["# Step 0 — Daily Instrument Characterization\n",
              "_Exploratory analysis to ground the strategy hypothesis. Data: Dukascopy bid, daily._"]
    for name, path in pairs:
        report.append(analyze(name, path))
    text = "\n".join(report)
    print(text)
    with open("reports/step0_daily.md", "w") as f:
        f.write(text + "\n")
