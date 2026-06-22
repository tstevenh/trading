#!/usr/bin/env python3
"""Step 0 — Universe ranking: which instruments suit trend-pullback?

Computes trend-pullback suitability metrics for all 8 instruments on DAILY data
(2010+), ranks them, and recommends KEEP / DROP. Direction-agnostic: we trade
both long and short, so 'trendiness' (ADX, efficiency ratio) matters more than
directional bias.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from indicators import load_csv, atr, adx, efficiency_ratio, swing_stats

INSTRUMENTS = {
    "EUR/USD": "data/raw/eurusd_d1.csv",
    "XAU/USD": "data/raw/xauusd_d1.csv",
    "GBP/USD": "data/raw/gbpusd_d1.csv",
    "USD/JPY": "data/raw/usdjpy_d1.csv",
    "AUD/USD": "data/raw/audusd_d1.csv",
    "USD/CAD": "data/raw/usdcad_d1.csv",
    "USD/CHF": "data/raw/usdchf_d1.csv",
    "NZD/USD": "data/raw/nzdusd_d1.csv",
}


def metrics(path: str) -> dict:
    df = load_csv(path)
    a = adx(df)
    df["atr"] = atr(df)
    df["atr_pct"] = df["atr"] / df["close"]
    df["sma200"] = df["close"].rolling(200).mean()
    er = efficiency_ratio(df["close"], 10)
    adx_v = a["adx"].dropna()
    dur, amp = swing_stats(df, df["atr"], k=3)
    return {
        "bars": len(df),
        "atr_pct_med": df["atr_pct"].median() * 100,
        "adx_trend_frac": (adx_v > 25).mean() * 100,
        "adx_range_frac": (adx_v < 20).mean() * 100,
        "eff_ratio": er.mean(),
        "above200_frac": (df["close"] > df["sma200"]).mean() * 100,
        "swing_dur_med": float(np.median(dur)) if len(dur) else np.nan,
        "swing_amp_med": float(np.median(amp)) if len(amp) else np.nan,
        "swing_ge2atr": (amp >= 2).mean() * 100 if len(amp) else np.nan,
    }


def main():
    rows = {name: metrics(path) for name, path in INSTRUMENTS.items()}
    df = pd.DataFrame(rows).T

    # --- transparent suitability score (rank-based, scale-free) ---
    # trend-pullback wants: trends often (adx_trend), clean trends (eff_ratio),
    # swing room for 2:1 (swing_ge2atr), and enough volatility vs costs (atr_pct).
    score = (
        df["adx_trend_frac"].rank()
        + df["eff_ratio"].rank()
        + df["swing_ge2atr"].rank()
        + df["atr_pct_med"].rank()
        - df["adx_range_frac"].rank()  # penalize choppiness
    )
    df["suitability"] = (score / score.max() * 100).round(1)
    df = df.sort_values("suitability", ascending=False)

    # recommendation: keep top, drop bottom-2 unless they clear absolute bars
    df["verdict"] = "KEEP"
    bottom2 = df.index[-2:]
    for name in bottom2:
        df.loc[name, "verdict"] = "DROP?"

    # pretty print
    show = df.copy()
    show.columns = [c for c in show.columns]
    fmt = {
        "bars": "{:.0f}", "atr_pct_med": "{:.2f}%", "adx_trend_frac": "{:.1f}%",
        "adx_range_frac": "{:.1f}%", "eff_ratio": "{:.3f}", "above200_frac": "{:.1f}%",
        "swing_dur_med": "{:.0f}", "swing_amp_med": "{:.1f}x", "swing_ge2atr": "{:.1f}%",
        "suitability": "{:.1f}",
    }
    lines = ["# Step 0 — Universe Ranking (trend-pullback suitability)\n",
             "_Daily 2010+. Direction-agnostic trendiness + R:R room + volatility. "
             "Higher suitability = better fit._\n"]
    cols = ["suitability", "adx_trend_frac", "adx_range_frac", "eff_ratio",
            "swing_ge2atr", "atr_pct_med", "swing_dur_med", "above200_frac", "verdict"]
    hdr = ["Instrument", "Score", "ADX>25", "ADX<20", "EffRatio",
           "Swing≥2ATR", "ATR%med", "SwingDur", "Above200", "Verdict"]
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    for name, r in show.iterrows():
        cells = [name]
        for c in cols:
            if c == "verdict":
                cells.append(r[c])
            else:
                cells.append(fmt.get(c, "{:.2f}").format(r[c]))
        lines.append("| " + " | ".join(cells) + " |")

    text = "\n".join(lines)
    print(text)
    with open("reports/step0_universe.md", "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
