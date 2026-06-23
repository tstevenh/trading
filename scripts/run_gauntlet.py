#!/usr/bin/env python3
"""Robustness/skeptic gauntlet on the 6 candidate edges.
Each candidate must pass: (1) parameter-neighborhood — >=50% of same-archetype
variants OOS-positive (not one lucky setting); (2) cost-sensitivity — still
OOS-positive at 1.5x spread; (3) sub-period — positive in BOTH OOS halves
(2023-24 and 2025-26). Survivors are combined into a portfolio."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib
import pandas as pd
from swingbot import indicators as ind
from swingbot.search import build_features_rich, run_strategy
from swingbot.costs import SPREADS
from swingbot.metrics import summarize

CUTOFF = pd.Timestamp("2023-01-01", tz="UTC")
MID = pd.Timestamp("2025-01-01", tz="UTC")

# (instrument, archetype module, winning variant label)
CANDIDATES = [
    ("ETHUSD", "trend_pullback_plus", "tpp_adx18_rsi45_relaxed"),
    ("SPX500", "mean_reversion", "mr_adx18_rsi30_sm15"),
    ("NAS100", "momentum", "mom_adx30_b20_s15_rr2.5"),
    ("GER40", "momentum", "mom_adx30_b50_s15_rr2.0"),
    ("EURUSD", "trend_pullback_plus", "tpp_adx18_rsi48"),
    ("JPN225", "breakout_retest", "breakout_retest_lb50_tol0.25_sm1.5"),
]


def variants(mod):
    v = mod.variants()
    return list(v.items()) if isinstance(v, dict) else list(v)


def oos(trades):
    return [t for t in trades if t.entry_ts >= CUTOFF]


def tpd(ts):
    if not ts:
        return 0.0
    span = (max(t.entry_ts for t in ts) - min(t.entry_ts for t in ts)).days
    return len(ts) / max(1, int(span * 5 / 7))


survivors = []
print(f"{'instrument/strategy':52s} {'neigh':>6} {'c1.0':>6} {'c1.5':>6} {'c2.0':>6} {'H1':>6} {'H2':>6}  verdict")
for sym, aname, label in CANDIDATES:
    mod = importlib.import_module(f"swingbot.archetypes.{aname}")
    s = sym.lower()
    feats = build_features_rich(ind.load_csv(f"data/raw/{s}_m15.csv"),
                                ind.load_csv(f"data/raw/{s}_h1.csv"),
                                ind.load_csv(f"data/raw/{s}_d1.csv"))
    f = feats.dropna(subset=list(getattr(mod, "REQUIRED_COLS", [])) or None)
    m15 = ind.load_csv(f"data/raw/{s}_m15.csv")
    sp = SPREADS[sym]

    # (1) neighborhood
    pos = tot = 0
    win_fn = None
    for lbl, fn in variants(mod):
        if lbl == label:
            win_fn = fn
        o = oos(run_strategy(sym, f, m15, sp, fn))
        if len(o) >= 30:
            tot += 1
            if summarize(o)["expectancy_r"] > 0:
                pos += 1
    neigh = pos / tot if tot else 0.0

    # (2) cost sensitivity
    c = {}
    for mult in (1.0, 1.5, 2.0):
        c[mult] = summarize(oos(run_strategy(sym, f, m15, sp * mult, win_fn)))["expectancy_r"]

    # (3) sub-period (1x cost)
    o1x = oos(run_strategy(sym, f, m15, sp, win_fn))
    h1 = summarize([t for t in o1x if t.entry_ts < MID])["expectancy_r"]
    h2 = summarize([t for t in o1x if t.entry_ts >= MID])["expectancy_r"]

    robust = (neigh >= 0.5) and (c[1.5] > 0) and (h1 > 0) and (h2 > 0)
    verdict = "ROBUST ✅" if robust else "fragile"
    print(f"{sym+'/'+aname:52s} {neigh*100:>5.0f}% {c[1.0]:>+6.3f} {c[1.5]:>+6.3f} "
          f"{c[2.0]:>+6.3f} {h1:>+6.3f} {h2:>+6.3f}  {verdict}")
    if robust:
        survivors.append((sym, aname, label, o1x))

print("\n=== PORTFOLIO of ROBUST survivors (OOS) ===")
if survivors:
    allt = [t for _, _, _, ts in survivors for t in ts]
    c = summarize(allt)
    names = ", ".join(f"{s}/{a}" for s, a, _, _ in survivors)
    print(f"Survivors: {names}")
    print(f"OOS n={c['n']} (~{tpd(allt):.2f}/day), win={c['win_rate']*100:.1f}%, "
          f"expectancy={c['expectancy_r']:+.3f}R, PF={c['profit_factor']:.2f}, "
          f"maxDD={c['max_drawdown_r']:.1f}R, finalEquity={c['equity_final_r']:+.1f}R")
else:
    print("No candidate passed the full gauntlet.")
