#!/usr/bin/env python3
"""Gold-only (XAUUSD) disciplined evaluation of all archetype variants.
Same protocol: IS (pre-2023) vs OOS (2023+). Reports per-variant gold stats."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib
import pandas as pd
from swingbot import indicators as ind
from swingbot.search import build_features_rich, run_strategy
from swingbot.costs import SPREADS
from swingbot.metrics import summarize

SYM = "XAUUSD"
CUTOFF = pd.Timestamp("2023-01-01", tz="UTC")
m15 = ind.load_csv("data/raw/xauusd_m15.csv")
h1 = ind.load_csv("data/raw/xauusd_h1.csv")
d1 = ind.load_csv("data/raw/xauusd_d1.csv")
feats = build_features_rich(m15, h1, d1)
print(f"Window: {feats.index[0].date()} -> {feats.index[-1].date()}  ({len(feats)} M15 bars)")
print(f"IS = pre-2023, OOS = 2023+\n")


def tpd(ts):
    if not ts:
        return 0.0
    span = (max(t.entry_ts for t in ts) - min(t.entry_ts for t in ts)).days
    return len(ts) / max(1, int(span * 5 / 7))


def variants(mod):
    v = mod.variants()
    return list(v.items()) if isinstance(v, dict) else list(v)


print(f"{'variant':40s} {'ISn':>5} {'ISexp':>7} {'OOSn':>6} {'OOSexp':>7} {'OOSpf':>6} {'win%':>5} {'OOS/day':>7}")
best = None
for name in ["trend_pullback_plus", "breakout_retest", "mean_reversion", "momentum"]:
    mod = importlib.import_module(f"swingbot.archetypes.{name}")
    f = feats.dropna(subset=list(getattr(mod, "REQUIRED_COLS", [])) or None)
    print(f"\n# {name}")
    for label, fn in variants(mod):
        trades = run_strategy(SYM, f, m15, SPREADS[SYM], fn)
        ist = [t for t in trades if t.entry_ts < CUTOFF]
        oost = [t for t in trades if t.entry_ts >= CUTOFF]
        a, b = summarize(ist), summarize(oost)
        print(f"{label:40s} {a['n']:>5} {a['expectancy_r']:>+7.3f} {b['n']:>6} "
              f"{b['expectancy_r']:>+7.3f} {b['profit_factor']:>6.2f} {b['win_rate']*100:>4.0f}% {tpd(oost):>7.2f}")
        if b["n"] >= 30 and (best is None or b["expectancy_r"] > best[1]["expectancy_r"]):
            best = (f"{name}/{label}", b, tpd(oost), a)
print("\n=== BEST gold OOS variant (n>=30) ===")
if best:
    lbl, b, d, a = best
    print(f"{lbl}: OOS n={b['n']} (~{d:.2f}/day), win={b['win_rate']*100:.1f}%, "
          f"exp={b['expectancy_r']:+.3f}R, PF={b['profit_factor']:.2f}, maxDD={b['max_drawdown_r']:.1f}R "
          f"| IS exp={a['expectancy_r']:+.3f}")
