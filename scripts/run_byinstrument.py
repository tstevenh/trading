#!/usr/bin/env python3
"""Per-instrument credible-edge scan across all archetype variants.
A variant is 'credible' only if it is positive in BOTH in-sample AND out-of-sample
(with enough OOS trades). Reports the best credible variant per instrument, or none.
This is the honest test for instrument-specific edge (pooling hides it)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib
import numpy as np
import pandas as pd
from swingbot import indicators as ind
from swingbot.search import build_features_rich, run_strategy
from swingbot.costs import SPREADS
from swingbot.metrics import summarize

UNIVERSE = ["XAUUSD", "XAGUSD", "SPX500", "NAS100", "GER40", "JPN225", "UK100",
            "BTCUSD", "ETHUSD", "EURUSD"]
CUTOFF = pd.Timestamp("2023-01-01", tz="UTC")
ARCH = {n: importlib.import_module(f"swingbot.archetypes.{n}")
        for n in ["trend_pullback_plus", "breakout_retest", "mean_reversion", "momentum"]}


def vlist(mod):
    v = mod.variants()
    return list(v.items()) if isinstance(v, dict) else list(v)


def wf(trades):
    out = []
    for y in (2023, 2024, 2025, 2026):
        ts = [t for t in trades if t.entry_ts.year == y]
        out.append(np.mean([t.outcome_r for t in ts]) if ts else 0.0)
    return out


def tpd(ts):
    if not ts:
        return 0.0
    span = (max(t.entry_ts for t in ts) - min(t.entry_ts for t in ts)).days
    return len(ts) / max(1, int(span * 5 / 7))


print(f"{'instrument':11s} {'best credible variant':38s} {'ISexp':>7} {'OOSexp':>7} {'OOSn':>5} {'win%':>5} {'/day':>5}  WF(23/24/25/26)")
summary = []
for sym in UNIVERSE:
    s = sym.lower()
    try:
        m15 = ind.load_csv(f"data/raw/{s}_m15.csv")
        h1 = ind.load_csv(f"data/raw/{s}_h1.csv")
        d1 = ind.load_csv(f"data/raw/{s}_d1.csv")
        feats = build_features_rich(m15, h1, d1)
    except Exception as e:
        print(f"{sym:11s} SKIP ({str(e)[:40]})"); continue
    candidates = []
    for aname, mod in ARCH.items():
        f = feats.dropna(subset=list(getattr(mod, "REQUIRED_COLS", [])) or None)
        for label, fn in vlist(mod):
            trades = run_strategy(sym, f, m15, SPREADS[sym], fn)
            ist = [t for t in trades if t.entry_ts < CUTOFF]
            oost = [t for t in trades if t.entry_ts >= CUTOFF]
            a, b = summarize(ist), summarize(oost)
            if a["expectancy_r"] > 0 and b["expectancy_r"] > 0 and b["n"] >= 50:
                candidates.append((f"{aname}/{label}", a, b, oost))
    if candidates:
        name, a, b, oost = max(candidates, key=lambda c: c[2]["expectancy_r"])
        w = wf(oost)
        print(f"{sym:11s} {name:38s} {a['expectancy_r']:>+7.3f} {b['expectancy_r']:>+7.3f} "
              f"{b['n']:>5} {b['win_rate']*100:>4.0f}% {tpd(oost):>5.2f}  "
              f"{w[0]:+.2f}/{w[1]:+.2f}/{w[2]:+.2f}/{w[3]:+.2f}")
        summary.append((sym, name, b, w))
    else:
        print(f"{sym:11s} {'— no credible (IS+ & OOS+, n>=50) variant —':38s}")

print("\n=== CREDIBLE EDGES (positive IS & OOS, n>=50) ===")
if summary:
    for sym, name, b, w in summary:
        consistent = sum(1 for x in w if x > 0)
        print(f"{sym} {name}: OOS exp {b['expectancy_r']:+.3f}R, PF {b['profit_factor']:.2f}, "
              f"win {b['win_rate']*100:.0f}%, {consistent}/4 OOS years positive")
else:
    print("NONE. No instrument has a variant positive in both IS and OOS with n>=50.")
