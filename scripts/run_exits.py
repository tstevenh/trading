#!/usr/bin/env python3
"""Exit-policy comparison for the 3 locked strategies. Entries come from the
existing signal (so volume is IDENTICAL across policies); we only vary how the
trade is managed out. IS-select the exit, report OOS. No-lookahead trailing;
correct R accounting (incl. partials). Half-spread on entry + every exit leg."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import importlib
import numpy as np
import pandas as pd
from swingbot import indicators as ind
from swingbot.search import build_features_rich, run_strategy
from swingbot.costs import SPREADS

CUTOFF = pd.Timestamp("2023-01-01", tz="UTC")
LOCKED = [
    ("SPX500", "mean_reversion", "mr_adx18_rsi30_sm15"),
    ("ETHUSD", "trend_pullback_plus", "tpp_adx18_rsi45_relaxed"),
    ("EURUSD", "trend_pullback_plus", "tpp_adx18_rsi48"),
]


def fn_for(mod, label):
    v = mod.variants(); items = v.items() if isinstance(v, dict) else v
    return next(fn for lbl, fn in items if lbl == label)


# ---- exit simulators: return outcome_r (net of spread), given forward arrays ----
def sim_fixed(side, entry, stop, risk, highs, lows, closes, atrs, start, half, rr):
    tp = entry + side * rr * risk
    n = len(highs)
    for j in range(start, n):
        if side == 1:
            if lows[j] <= stop:  return (stop - half - entry) / risk, j - start
            if highs[j] >= tp:   return (tp - half - entry) / risk, j - start
        else:
            if highs[j] >= stop: return (entry - (stop + half)) / risk, j - start
            if lows[j] <= tp:    return (entry - (tp + half)) / risk, j - start
    return side * (closes[n - 1] - entry) / risk, n - 1 - start


def sim_timestop(side, entry, stop, risk, highs, lows, closes, atrs, start, half, rr, maxbars):
    tp = entry + side * rr * risk
    n = len(highs)
    for j in range(start, min(n, start + maxbars + 1)):
        if side == 1:
            if lows[j] <= stop:  return (stop - half - entry) / risk, j - start
            if highs[j] >= tp:   return (tp - half - entry) / risk, j - start
        else:
            if highs[j] >= stop: return (entry - (stop + half)) / risk, j - start
            if lows[j] <= tp:    return (entry - (tp + half)) / risk, j - start
    j = min(n - 1, start + maxbars)
    return side * (closes[j] - half - entry) / risk, j - start


def _trail_exit(side, entry, stop0, risk, highs, lows, closes, atrs, start, half,
                activate_rr, tmult, begin_stop):
    """Trail from best price once price has moved activate_rr in favor. begin_stop
    is the stop until activation. Returns (exit_r, bars)."""
    n = len(highs); best = entry; stop = begin_stop; active = False
    act_px = entry + side * activate_rr * risk
    for j in range(start, n):
        if side == 1:
            if lows[j] <= stop:  return (stop - half - entry) / risk, j - start
            best = max(best, highs[j])
            if not active and highs[j] >= act_px: active = True
            if active: stop = max(stop, best - tmult * atrs[j])
        else:
            if highs[j] >= stop: return (entry - (stop + half)) / risk, j - start
            best = min(best, lows[j])
            if not active and lows[j] <= act_px: active = True
            if active: stop = min(stop, best + tmult * atrs[j])
    return side * (closes[n - 1] - entry) / risk, n - 1 - start


def sim_atrtrail(side, entry, stop, risk, highs, lows, closes, atrs, start, half, activate_rr, tmult):
    return _trail_exit(side, entry, stop, risk, highs, lows, closes, atrs, start, half,
                       activate_rr, tmult, stop)


def sim_scaleout(side, entry, stop, risk, highs, lows, closes, atrs, start, half, t1, frac, tmult):
    """Bank `frac` at +t1*risk, move stop to breakeven, trail remainder by tmult*ATR."""
    t1_px = entry + side * t1 * risk
    n = len(highs)
    for j in range(start, n):
        # stop (initial) before t1
        if side == 1 and lows[j] <= stop:  return (stop - half - entry) / risk, j - start
        if side == -1 and highs[j] >= stop: return (entry - (stop + half)) / risk, j - start
        hit_t1 = (highs[j] >= t1_px) if side == 1 else (lows[j] <= t1_px)
        if hit_t1:
            banked = frac * ((t1_px - half - entry) / risk if side == 1 else (entry - (t1_px + half)) / risk)
            run_r, b = _trail_exit(side, entry, entry, risk, highs, lows, closes, atrs, j, half,
                                   0.0, tmult, entry)  # breakeven stop, trail immediately
            return banked + (1 - frac) * run_r, (j - start) + b
    return side * (closes[n - 1] - entry) / risk, n - 1 - start


def sim_breakeven(side, entry, stop, risk, highs, lows, closes, atrs, start, half, move_at, rr):
    """Move stop to breakeven once price reaches +move_at*risk; fixed target at rr."""
    tp = entry + side * rr * risk
    be_trig = entry + side * move_at * risk
    cur = stop; n = len(highs)
    for j in range(start, n):
        if side == 1:
            if lows[j] <= cur:  return (cur - half - entry) / risk, j - start
            if highs[j] >= tp:  return (tp - half - entry) / risk, j - start
            if highs[j] >= be_trig: cur = max(cur, entry)
        else:
            if highs[j] >= cur: return (entry - (cur + half)) / risk, j - start
            if lows[j] <= tp:   return (entry - (tp + half)) / risk, j - start
            if lows[j] <= be_trig: cur = min(cur, entry)
    return side * (closes[n - 1] - entry) / risk, n - 1 - start


def sim_partial_fixed(side, entry, stop, risk, highs, lows, closes, atrs, start, half, t1, frac, run_rr):
    """Bank frac at +t1*risk, move stop to breakeven, runner targets fixed run_rr (NO trail)."""
    t1_px = entry + side * t1 * risk
    run_tp = entry + side * run_rr * risk
    n = len(highs)
    for j in range(start, n):
        if side == 1 and lows[j] <= stop:  return (stop - half - entry) / risk, j - start
        if side == -1 and highs[j] >= stop: return (entry - (stop + half)) / risk, j - start
        hit = (highs[j] >= t1_px) if side == 1 else (lows[j] <= t1_px)
        if hit:
            banked = frac * (((t1_px - half - entry) / risk) if side == 1 else ((entry - (t1_px + half)) / risk))
            for k in range(j, n):           # runner: BE stop, fixed run_tp, no trail
                if side == 1:
                    if lows[k] <= entry:   return banked + (1 - frac) * ((entry - half - entry) / risk), k - start
                    if highs[k] >= run_tp: return banked + (1 - frac) * ((run_tp - half - entry) / risk), k - start
                else:
                    if highs[k] >= entry:  return banked + (1 - frac) * ((entry - (entry + half)) / risk), k - start
                    if lows[k] <= run_tp:  return banked + (1 - frac) * ((entry - (run_tp + half)) / risk), k - start
            return banked + (1 - frac) * side * (closes[n - 1] - entry) / risk, n - 1 - start
    return side * (closes[n - 1] - entry) / risk, n - 1 - start


POLICIES = {
    "fixed_2.0(base)":  lambda *a: sim_fixed(*a, 2.0),
    "fixed_3.0":        lambda *a: sim_fixed(*a, 3.0),
    "breakeven@1R_t2":  lambda *a: sim_breakeven(*a, 1.0, 2.0),
    "breakeven@1R_t3":  lambda *a: sim_breakeven(*a, 1.0, 3.0),
    "breakeven@1.5_t3": lambda *a: sim_breakeven(*a, 1.5, 3.0),
    "partial.5@1R_run3": lambda *a: sim_partial_fixed(*a, 1.0, 0.5, 3.0),
    "partial.5@2R_run4": lambda *a: sim_partial_fixed(*a, 2.0, 0.5, 4.0),
    "partial.7@1.5_run3": lambda *a: sim_partial_fixed(*a, 1.5, 0.7, 3.0),
    "atrtrail_1.0_2":   lambda *a: sim_atrtrail(*a, 1.0, 2.0),
}


def stats(rs):
    rs = np.array(rs)
    if not len(rs): return None
    wins = rs[rs > 0]; eq = np.cumsum(rs); peak = np.maximum.accumulate(eq)
    return dict(n=len(rs), win=(rs > 0).mean(), exp=rs.mean(),
                avgwin=wins.mean() if len(wins) else 0.0,
                pf=(wins.sum() / -rs[rs < 0].sum()) if (rs < 0).any() else float("inf"),
                dd=(peak - eq).max(), net=eq[-1])


# sanity check on scale-out accounting (synthetic long: runs to +4R cleanly)
def _sanity():
    h = np.array([100, 102, 104, 106, 108, 108]); l = np.array([100, 101, 103, 105, 103, 103])
    c = h.copy(); a = np.full(6, 1.0)
    # entry 100, stop 99 (risk 1), no spread; t1 at +2 (102), trail rest by 3*ATR
    r, _ = sim_scaleout(1, 100.0, 99.0, 1.0, h, l, c, a, 1, 0.0, 2.0, 0.5, 3.0)
    print(f"[sanity] scaleout long banks 0.5*2 + runner: outcome_r={r:.3f}")


_sanity()
L = ["# Exit-Policy Comparison (3 locked strategies)\n",
     "_Entries fixed (volume identical across policies). IS-select exit, report OOS. "
     "Half-spread on entry + each exit leg. No-lookahead trailing._\n"]
for sym, aname, label in LOCKED:
    mod = importlib.import_module(f"swingbot.archetypes.{aname}")
    s = sym.lower()
    feats = build_features_rich(ind.load_csv(f"data/raw/{s}_m15.csv"),
                                ind.load_csv(f"data/raw/{s}_h1.csv"),
                                ind.load_csv(f"data/raw/{s}_d1.csv"))
    f = feats.dropna(subset=list(getattr(mod, "REQUIRED_COLS", [])) or None)
    m15 = ind.load_csv(f"data/raw/{s}_m15.csv")
    sp = SPREADS[sym]; half = sp / 2.0
    highs = f["high"].values; lows = f["low"].values; closes = f["close"].values; atrs = f["atr"].values
    posmap = {ts: i for i, ts in enumerate(f.index)}
    trades = run_strategy(sym, f, m15, sp, fn_for(mod, label))
    entries = []
    for tr in trades:
        e = posmap.get(tr.entry_ts)
        if e is None or e + 1 >= len(f): continue
        entries.append((tr.entry_ts, tr.side, tr.entry, tr.stop, abs(tr.entry - tr.stop), e + 1))

    L.append(f"\n## {sym} — {aname}  ({len(entries)} entries, identical across policies)\n")
    L.append("| exit policy | IS exp | OOS n | OOS win% | OOS avgWin | OOS exp | OOS PF | OOS maxDD | OOS net |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    rankings = []
    for pname, pol in POLICIES.items():
        is_r, oos_r = [], []
        for ts, side, entry, stop, risk, start in entries:
            r, _ = pol(side, entry, stop, risk, highs, lows, closes, atrs, start, half)
            (is_r if ts < CUTOFF else oos_r).append(r)
        si, so = stats(is_r), stats(oos_r)
        rankings.append((pname, si["exp"] if si else -9, so))
        L.append(f"| {pname} | {si['exp']:+.3f} | {so['n']} | {so['win']*100:.0f}% | "
                 f"{so['avgwin']:+.2f} | {so['exp']:+.3f} | {so['pf']:.2f} | {so['dd']:.1f} | {so['net']:+.1f} |")
    best = max(rankings, key=lambda x: x[1])  # IS-selected
    L.append(f"\n**IS-selected exit: `{best[0]}`** → OOS exp {best[2]['exp']:+.3f}R, "
             f"win {best[2]['win']*100:.0f}%, avgWin {best[2]['avgwin']:+.2f}R, PF {best[2]['pf']:.2f}, "
             f"net {best[2]['net']:+.1f}R  (baseline fixed_2.0 OOS exp = "
             f"{[r[2]['exp'] for r in rankings if r[0]=='fixed_2.0(base)'][0]:+.3f}R)")

text = "\n".join(L)
print(text)
open("reports/exit_comparison.md", "w").write(text + "\n")
