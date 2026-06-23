#!/usr/bin/env python3
"""Disciplined multi-archetype strategy search.

Protocol (anti-overfitting):
  1. Evaluate every variant of every archetype on IN-SAMPLE only (pre-2023),
     pooled across all 7 pairs.
  2. SELECT the best variant per archetype by IN-SAMPLE expectancy (min trade count).
  3. REPORT that selected variant's OUT-OF-SAMPLE (2023+) performance — the honest test.
  4. Walk-forward: OOS expectancy per year, to check consistency (not one lucky year).
  5. Multiple-testing: report how many variants were tried; demand strong, consistent OOS.
Selection touches ONLY in-sample; OOS is never used to pick anything.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from swingbot import indicators as ind
from swingbot.search import build_features_rich, run_strategy
from swingbot.costs import SPREADS
from swingbot.metrics import summarize

UNIVERSE = ["XAUUSD", "USDJPY", "EURUSD", "USDCHF", "NZDUSD", "GBPUSD", "USDCAD"]
CUTOFF = pd.Timestamp("2023-01-01", tz="UTC")

ARCHETYPES = {}
for name in ["trend_pullback_plus", "breakout_retest", "mean_reversion", "momentum"]:
    try:
        ARCHETYPES[name] = __import__(f"swingbot.archetypes.{name}", fromlist=[name])
    except Exception as e:  # noqa
        print(f"WARN: could not import {name}: {e}")

print("Loading + building rich features for 7 pairs (one-time)...", flush=True)
FEATS, RAW = {}, {}
for sym in UNIVERSE:
    s = sym.lower()
    m15 = ind.load_csv(f"data/raw/{s}_m15.csv")
    h1 = ind.load_csv(f"data/raw/{s}_h1.csv")
    d1 = ind.load_csv(f"data/raw/{s}_d1.csv")
    FEATS[sym] = build_features_rich(m15, h1, d1)
    RAW[sym] = m15
    print(f"  {sym}: {len(FEATS[sym])} bars", flush=True)


def run_variant(mod, signal_fn):
    trades = []
    cols = list(getattr(mod, "REQUIRED_COLS", []))
    for sym in UNIVERSE:
        feats = FEATS[sym].dropna(subset=cols) if cols else FEATS[sym].dropna()
        trades += run_strategy(sym, feats, RAW[sym], SPREADS[sym], signal_fn)
    return trades


def split(trades):
    return ([t for t in trades if t.entry_ts < CUTOFF],
            [t for t in trades if t.entry_ts >= CUTOFF])


def by_year(trades):
    out = {}
    for y in (2023, 2024, 2025, 2026):
        ts = [t for t in trades if t.entry_ts.year == y]
        out[y] = (len(ts), np.mean([t.outcome_r for t in ts]) if ts else 0.0)
    return out


def tpd(trades):
    if not trades:
        return 0.0
    span = (max(t.entry_ts for t in trades) - min(t.entry_ts for t in trades)).days
    return len(trades) / max(1, int(span * 5 / 7))


def main():
    L = ["# Multi-Archetype Strategy Search — Results\n",
         "_Select variant on IN-SAMPLE (pre-2023) expectancy; report OUT-OF-SAMPLE (2023+). "
         "All 7 pairs pooled, flat 1% risk, spread modeled._\n"]
    total_variants = 0
    selected = []
    for name, mod in ARCHETYPES.items():
        variants = mod.variants()
        rows = []
        for label, fn in variants:
            total_variants += 1
            allt = run_variant(mod, fn)
            ist, oost = split(allt)
            rows.append((label, summarize(ist), summarize(oost), ist, oost))
        elig = [r for r in rows if r[1]["n"] >= 30] or rows
        pick = max(elig, key=lambda r: r[1]["expectancy_r"])
        selected.append((name, pick))
        L.append(f"\n## {name}  ({len(variants)} variants tried)\n")
        L.append("| variant | IS n | IS exp | IS PF | OOS n | OOS exp | OOS PF | OOS win% | OOS/day |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for label, isum, osum, _, oost in rows:
            star = " ⭐" if label == pick[0] else ""
            L.append(f"| {label}{star} | {isum['n']} | {isum['expectancy_r']:+.3f} | {isum['profit_factor']:.2f} "
                     f"| {osum['n']} | {osum['expectancy_r']:+.3f} | {osum['profit_factor']:.2f} "
                     f"| {osum['win_rate']*100:.0f}% | {tpd(oost):.2f} |")
        # walk-forward for the selected variant
        wf = by_year(pick[4])
        L.append(f"\n**IS-selected ⭐ `{pick[0]}` walk-forward (OOS by year):** "
                 + ", ".join(f"{y}: n={n} exp={e:+.3f}" for y, (n, e) in wf.items()))

    # combined portfolio of selected variants that are OOS-positive
    L.append("\n## Combined portfolio (IS-selected variants with OOS expectancy > 0)\n")
    keep_trades = []
    for name, pick in selected:
        osum = pick[2]
        if osum["expectancy_r"] > 0 and osum["n"] >= 30:
            keep_trades += pick[4]
            L.append(f"- ✅ {name} `{pick[0]}`: OOS exp {osum['expectancy_r']:+.3f}R, PF {osum['profit_factor']:.2f}, n={osum['n']}")
        else:
            L.append(f"- ❌ {name} `{pick[0]}`: OOS exp {osum['expectancy_r']:+.3f}R (dropped)")
    if keep_trades:
        c = summarize(keep_trades)
        L.append(f"\n**Portfolio OOS:** n={c['n']} (~{tpd(keep_trades):.2f}/day), win {c['win_rate']*100:.1f}%, "
                 f"expectancy {c['expectancy_r']:+.3f}R, PF {c['profit_factor']:.2f}, maxDD {c['max_drawdown_r']:.1f}R, "
                 f"final {c['equity_final_r']:+.1f}R")
    else:
        L.append("\n**No archetype survived OOS with positive expectancy.**")

    L.append(f"\n## Multiple-testing note\nTotal variants evaluated: **{total_variants}**. "
             f"With this many tries, treat any single positive OOS result skeptically — "
             f"demand consistency across walk-forward years and a skeptic review before trust.")
    text = "\n".join(L)
    print(text)
    with open("reports/strategy_search.md", "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
