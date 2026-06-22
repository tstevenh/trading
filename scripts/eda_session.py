#!/usr/bin/env python3
"""Step 0 — Intraday/session characterization from H1 Dukascopy CSVs.

Answers: which hours (UTC) do gold & EUR/USD actually move? When is the best
entry window? This shapes WHEN the bot should look for setups. Timestamps are
UTC (Dukascopy native).
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["dt"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("dt").sort_index()
    df = df[~df[["open", "high", "low", "close"]].isna().any(axis=1)]
    # drop weekend bars (Sat=5, Sun=6) that may carry near-zero volume
    df = df[df.index.dayofweek < 5]
    return df


SESSIONS = {  # UTC hour ranges (approx)
    "Asia (Tokyo)": range(0, 7),
    "London": range(7, 12),
    "London/NY overlap": range(12, 16),
    "New York": range(16, 21),
    "Late/illiquid": list(range(21, 24)),
}


def analyze(name: str, path: str) -> str:
    df = load(path)
    out = []
    w = out.append
    w(f"\n## {name}  (H1, {df.index[0].date()} → {df.index[-1].date()})\n")

    rng = (df["high"] - df["low"]) / df["close"] * 100  # bar range in %
    hour = df.index.hour
    by_hour = rng.groupby(hour).mean()

    w("**Avg hourly range (% of price) by UTC hour** — where the movement is:")
    peak = by_hour.idxmax()
    for h in range(24):
        bar = "█" * int(by_hour.get(h, 0) / by_hour.max() * 30)
        mark = "  <-- peak" if h == peak else ""
        w(f"  {h:02d}:00  {by_hour.get(h,0):.3f}%  {bar}{mark}")

    w("\n**By session (avg hourly range %):**")
    sess_vals = {}
    for sname, hrs in SESSIONS.items():
        hrs = list(hrs)
        v = by_hour[by_hour.index.isin(hrs)].mean()
        sess_vals[sname] = v
        w(f"  - {sname:20s}: {v:.3f}%")
    best = max(sess_vals, key=sess_vals.get)
    quiet = min(sess_vals, key=sess_vals.get)
    w(f"\n  → Most active: **{best}**  |  Quietest: **{quiet}**")
    w(f"  → Best entry-scan window: London open through the NY overlap "
      f"(~07:00–16:00 UTC), avoid the Asia/late illiquid hours.")
    return "\n".join(out)


if __name__ == "__main__":
    pairs = [
        ("XAU/USD (Gold)", "data/raw/xauusd_h1.csv"),
        ("EUR/USD", "data/raw/eurusd_h1.csv"),
    ]
    report = ["# Step 0 — Intraday / Session Characterization\n",
              "_When does each instrument actually move? (UTC hours, H1 data, weekdays only.)_"]
    for name, path in pairs:
        report.append(analyze(name, path))
    text = "\n".join(report)
    print(text)
    with open("reports/step0_session.md", "w") as f:
        f.write(text + "\n")
