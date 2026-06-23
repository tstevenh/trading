#!/usr/bin/env python3
"""Phase 1 validation on the H1-entry profile (Daily bias -> H4 pullback -> H1 entry).

We pivot to H1 entries because Dukascopy's bulk M15 feed proved unreliable
(only 1/7 pairs downloaded complete). H1 + Daily data is clean for all 7 pairs.
Strategy logic is IDENTICAL — only the timeframe ladder shifts up one step.
Reuses the reviewed swingbot core (indicators, align, gates, strategy, backtest,
metrics, grading) unchanged; only feature assembly is adapted for the H1 ladder.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from swingbot import indicators as ind
from swingbot.align import tf_close_index, align_htf
from swingbot.backtest import run_backtest
from swingbot.costs import SPREADS
from swingbot.metrics import summarize

UNIVERSE = ["XAUUSD", "USDJPY", "EURUSD", "USDCHF", "NZDUSD", "GBPUSD", "USDCAD"]
RELAXED = {"EURUSD": True}
CUTOFF = pd.Timestamp("2023-01-01", tz="UTC")


def build_features_h1(h1: pd.DataFrame, d1: pd.DataFrame) -> pd.DataFrame:
    """Entry TF = H1, pullback zone = H4 (resampled), bias = Daily.
    Reuses the gate column names (m15_* = entry TF, h1_* = pullback TF)."""
    m = h1.copy()
    m["atr"] = ind.atr(m, 14)
    m["m15_ema20"] = ind.ema(m["close"], 20)        # entry-TF EMA (H1 here)
    m["m15_rsi"] = ind.rsi(m["close"], 14)
    m["m15_rsi_prev"] = m["m15_rsi"].shift(1)

    h4 = h1.resample("4h").agg({"open": "first", "high": "max", "low": "min",
                                "close": "last", "volume": "sum"}).dropna()
    h4["h1_ema20"] = ind.ema(h4["close"], 20)        # pullback-TF (H4 here)
    h4["h1_ema50"] = ind.ema(h4["close"], 50)
    h4["h1_rsi"] = ind.rsi(h4["close"], 14)
    h4_feat = tf_close_index(h4[["h1_ema20", "h1_ema50", "h1_rsi"]], "4h")

    d = d1.copy()
    d["d1_close"] = d["close"]
    d["d1_sma50"] = ind.sma(d["close"], 50)
    d["d1_sma200"] = ind.sma(d["close"], 200)
    d_feat = tf_close_index(d[["d1_close", "d1_sma50", "d1_sma200"]], "d1")

    out = align_htf(m, h4_feat, prefix="")
    out = align_htf(out, d_feat, prefix="")
    return out


def trades_per_day(trades, feats):
    if not trades:
        return 0.0
    span = (feats.index[-1] - feats.index[0]).days
    trading_days = max(1, int(span * 5 / 7))         # weekdays approx
    return len(trades) / trading_days


def stats(trades):
    s = summarize(trades, risk_pct=1.0)
    s["avg_planned_rr"] = float(np.mean([t.rr for t in trades])) if trades else 0.0
    return s


def run_one(sym):
    s = sym.lower()
    h1 = ind.load_csv(f"data/raw/{s}_h1.csv")
    d1 = ind.load_csv(f"data/raw/{s}_d1.csv")
    feats = build_features_h1(h1, d1)
    trades = run_backtest(sym, feats, h1, SPREADS[sym],
                          relaxed_trend=RELAXED.get(sym, False),
                          pivot_lookback=40)
    is_t = [t for t in trades if t.entry_ts < CUTOFF]
    oos_t = [t for t in trades if t.entry_ts >= CUTOFF]
    return {"sym": sym, "feats_span": (feats.index[0], feats.index[-1]),
            "all": stats(trades), "is": stats(is_t), "oos": stats(oos_t),
            "tpd": trades_per_day(trades, feats), "trades": trades}


def tier_table(results):
    from collections import defaultdict
    b = defaultdict(list)
    for r in results:
        for t in r["trades"]:
            if t.entry_ts >= CUTOFF:
                b[t.tier].append(t.outcome_r)
    rows = []
    for tier in ("SSS", "AA", "A"):
        rs = b.get(tier, [])
        if rs:
            wr = sum(1 for x in rs if x > 0) / len(rs)
            rows.append((tier, len(rs), wr, float(np.mean(rs))))
        else:
            rows.append((tier, 0, 0.0, 0.0))
    return rows


def main():
    results = [run_one(s) for s in UNIVERSE]
    L = []
    L.append("# Phase 1 — H1-Entry Validation Report\n")
    L.append("_Daily bias -> H4 pullback -> H1 entry. Clean H1 data, all 7 pairs. "
             "R-multiples net of spread, flat 1% risk. IS = pre-2023, OOS = 2023+._\n")
    L.append("## Per-pair (OOS = out-of-sample, the honest test)\n")
    L.append("| Pair | OOS n | OOS/day | win% | avg planned R:R | expectancy(R) | profit factor | maxDD(R) | IS exp(R) | IS PF |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        o, i = r["oos"], r["is"]
        L.append(f"| {r['sym']} | {o['n']} | {r['tpd']:.2f} | {o['win_rate']*100:.0f}% | "
                 f"{o['avg_planned_rr']:.2f} | {o['expectancy_r']:+.3f} | {o['profit_factor']:.2f} | "
                 f"{o['max_drawdown_r']:.1f} | {i['expectancy_r']:+.3f} | {i['profit_factor']:.2f} |")
    # ranking
    ranked = sorted(results, key=lambda r: (r["oos"]["expectancy_r"], r["oos"]["profit_factor"]),
                    reverse=True)
    L.append("\n## Ranking by OOS expectancy (best -> worst)\n")
    for n, r in enumerate(ranked, 1):
        o = r["oos"]
        verdict = "KEEP" if (o["expectancy_r"] > 0 and o["profit_factor"] >= 1.2 and o["n"] >= 30) else "DROP?"
        L.append(f"{n}. **{r['sym']}** — exp {o['expectancy_r']:+.3f}R, PF {o['profit_factor']:.2f}, "
                 f"win {o['win_rate']*100:.0f}%, n={o['n']}  → **{verdict}**")
    # tiers
    L.append("\n## OOS expectancy by confluence tier (does higher tier win more?)\n")
    L.append("| Tier | n | win% | expectancy(R) |")
    L.append("|---|---|---|---|")
    for tier, n, wr, exp in tier_table(results):
        L.append(f"| {tier} | {n} | {wr*100:.0f}% | {exp:+.3f} |")
    # portfolio totals (OOS)
    all_oos = [t for r in results for t in r["trades"] if t.entry_ts >= CUTOFF]
    tot = stats(all_oos)
    total_tpd = sum(r["tpd"] for r in results)
    L.append("\n## Portfolio (all pairs, OOS)\n")
    L.append(f"- Total OOS trades: **{tot['n']}**  (~**{total_tpd:.2f}/day** across the universe)")
    L.append(f"- Win rate: **{tot['win_rate']*100:.1f}%**  | avg planned R:R: **{tot['avg_planned_rr']:.2f}**")
    L.append(f"- Expectancy: **{tot['expectancy_r']:+.3f}R/trade**  | profit factor: **{tot['profit_factor']:.2f}**")
    L.append(f"- Max drawdown: **{tot['max_drawdown_r']:.1f}R**  | final equity: **{tot['equity_final_r']:+.1f}R**")
    text = "\n".join(L)
    print(text)
    with open("reports/phase1_h1_backtest.md", "w") as f:
        f.write(text + "\n")


if __name__ == "__main__":
    main()
