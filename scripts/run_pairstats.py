#!/usr/bin/env python3
"""Complete per-instrument stats for the candidate strategies, so we can decide
the winning pairs. Full metrics, IS vs OOS, walk-forward by year."""
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

CUTOFF = pd.Timestamp("2023-01-01", tz="UTC")

# instrument, archetype, winning variant, gauntlet verdict
CANDIDATES = [
    ("SPX500", "mean_reversion", "mr_adx18_rsi30_sm15", "ROBUST"),
    ("ETHUSD", "trend_pullback_plus", "tpp_adx18_rsi45_relaxed", "ROBUST"),
    ("EURUSD", "trend_pullback_plus", "tpp_adx18_rsi48", "ROBUST"),
    ("GER40", "momentum", "mom_adx30_b50_s15_rr2.0", "ROBUST (marginal)"),
    ("NAS100", "momentum", "mom_adx30_b20_s15_rr2.5", "fragile-decay"),
    ("JPN225", "breakout_retest", "breakout_retest_lb50_tol0.25_sm1.5", "fragile-cost"),
]


def fn_for(mod, label):
    v = mod.variants()
    items = v.items() if isinstance(v, dict) else v
    for lbl, fn in items:
        if lbl == label:
            return fn
    raise KeyError(label)


def tpd(ts):
    if not ts:
        return 0.0
    span = (max(t.entry_ts for t in ts) - min(t.entry_ts for t in ts)).days
    return len(ts) / max(1, int(span * 5 / 7))


def full(trades):
    if not trades:
        return None
    s = summarize(trades)
    r = np.array([t.outcome_r for t in trades])
    wins, losses = r[r > 0], r[r < 0]
    s["avg_planned_rr"] = float(np.mean([t.rr for t in trades]))
    s["avg_win_r"] = float(wins.mean()) if len(wins) else 0.0
    s["avg_loss_r"] = float(losses.mean()) if len(losses) else 0.0
    s["tpd"] = tpd(trades)
    s["avg_hold_bars"] = float(np.mean([t.bars_held for t in trades]))
    return s


def by_year(trades):
    out = {}
    for y in (2023, 2024, 2025, 2026):
        ts = [t for t in trades if t.entry_ts.year == y]
        out[y] = (len(ts), float(np.mean([t.outcome_r for t in ts])) if ts else None)
    return out


rows = []
detail = []
for sym, aname, label, verdict in CANDIDATES:
    mod = importlib.import_module(f"swingbot.archetypes.{aname}")
    s = sym.lower()
    feats = build_features_rich(ind.load_csv(f"data/raw/{s}_m15.csv"),
                                ind.load_csv(f"data/raw/{s}_h1.csv"),
                                ind.load_csv(f"data/raw/{s}_d1.csv"))
    f = feats.dropna(subset=list(getattr(mod, "REQUIRED_COLS", [])) or None)
    m15 = ind.load_csv(f"data/raw/{s}_m15.csv")
    trades = run_strategy(sym, f, m15, SPREADS[sym], fn_for(mod, label))
    ist = [t for t in trades if t.entry_ts < CUTOFF]
    oost = [t for t in trades if t.entry_ts >= CUTOFF]
    a, b = full(ist), full(oost)
    rows.append((sym, aname, verdict, a, b))
    wf = by_year(oost)
    detail.append(f"### {sym} — {aname} ({verdict})\n"
                  f"- M15 window 2020–2026 | IS=pre-2023, OOS=2023+\n"
                  f"- **OOS:** n={b['n']}, {b['tpd']:.2f}/day, win {b['win_rate']*100:.1f}%, "
                  f"avg planned R:R {b['avg_planned_rr']:.2f}, expectancy {b['expectancy_r']:+.3f}R, "
                  f"avg win {b['avg_win_r']:+.2f}R / avg loss {b['avg_loss_r']:+.2f}R, "
                  f"PF {b['profit_factor']:.2f}, maxDD {b['max_drawdown_r']:.1f}R, net {b['equity_final_r']:+.1f}R, "
                  f"avg hold {b['avg_hold_bars']:.0f} bars\n"
                  f"- **IS:** n={a['n']}, win {a['win_rate']*100:.1f}%, expectancy {a['expectancy_r']:+.3f}R, PF {a['profit_factor']:.2f}\n"
                  f"- **Walk-forward OOS by year:** "
                  + ", ".join(f"{y}: n={n} exp={e:+.3f}" if e is not None else f"{y}: —"
                              for y, (n, e) in wf.items()))

L = ["# Per-Instrument Strategy Stats (candidates)\n",
     "_M15 entries, 2020–2026. OOS = 2023+. Flat 1% risk, spread modeled. "
     "Verdict from robustness gauntlet (neighborhood + cost + sub-period)._\n",
     "## OOS summary table\n",
     "| Instrument | Strategy | Verdict | OOS n | /day | win% | avg R:R | exp(R) | avgWin | avgLoss | PF | maxDD | net R |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for sym, aname, verdict, a, b in rows:
    L.append(f"| {sym} | {aname.replace('_',' ')} | {verdict} | {b['n']} | {b['tpd']:.2f} | "
             f"{b['win_rate']*100:.0f}% | {b['avg_planned_rr']:.2f} | {b['expectancy_r']:+.3f} | "
             f"{b['avg_win_r']:+.2f} | {b['avg_loss_r']:+.2f} | {b['profit_factor']:.2f} | "
             f"{b['max_drawdown_r']:.1f} | {b['equity_final_r']:+.1f} |")
L.append("\n## Detail\n")
L += detail
text = "\n".join(L)
print(text)
with open("reports/pair_stats.md", "w") as fo:
    fo.write(text + "\n")
