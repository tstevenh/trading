# swingbot/run_backtest.py
import pandas as pd
from swingbot.indicators import load_csv
from swingbot.features import build_features
from swingbot.backtest import run_backtest
from swingbot.costs import SPREADS
from swingbot.metrics import summarize

UNIVERSE = ["XAUUSD", "USDJPY", "EURUSD", "USDCHF", "NZDUSD", "GBPUSD", "USDCAD"]
RELAXED = {"EURUSD": True}
CUTOFF = pd.Timestamp("2023-01-01", tz="UTC")


def load_instrument(sym):
    s = sym.lower()
    return (load_csv(f"data/raw/{s}_m15.csv"),
            load_csv(f"data/raw/{s}_h1.csv"),
            load_csv(f"data/raw/{s}_d1.csv"))


def run_one(sym):
    m15, h1, d1 = load_instrument(sym)
    feats = build_features(m15, h1, d1)
    trades = run_backtest(sym, feats, m15, SPREADS[sym],
                          relaxed_trend=RELAXED.get(sym, False))
    is_t = [t for t in trades if t.entry_ts < CUTOFF]
    oos_t = [t for t in trades if t.entry_ts >= CUTOFF]
    return {"is": summarize(is_t), "oos": summarize(oos_t), "trades": trades}


def run_all(symbols=UNIVERSE):
    results = {}
    for sym in symbols:
        try:
            results[sym] = run_one(sym)
        except FileNotFoundError as e:
            print(f"WARNING: {sym} — missing data file: {e}", flush=True)
            empty = summarize([])
            results[sym] = {"is": empty, "oos": empty, "trades": [], "_missing": str(e)}
    return results


def _tier_table(results):
    from collections import defaultdict
    buckets = defaultdict(list)
    for r in results.values():
        for t in r["trades"]:
            if t.entry_ts >= CUTOFF:           # OOS only
                buckets[t.tier].append(t.outcome_r)
    out = ["\n## OOS expectancy by tier (does higher tier win more?)\n",
           "| Tier | n | win% | expectancy(R) |", "|---|---|---|---|"]
    for tier in ("A", "AA", "SSS"):
        rs = buckets.get(tier, [])
        if rs:
            wr = sum(1 for x in rs if x > 0) / len(rs)
            out.append(f"| {tier} | {len(rs)} | {wr*100:.0f}% | {sum(rs)/len(rs):+.2f} |")
        else:
            out.append(f"| {tier} | 0 | – | – |")
    return "\n".join(out)


def render_report(results) -> str:
    lines = ["# Phase 1 — Backtest Validation Report\n",
             "_Trend-pullback swing profile. IS = pre-2023, OOS = 2023+. "
             "R-multiples net of spread. Flat 1% risk._\n",
             "| Sym | IS n | IS win% | IS exp(R) | IS PF | OOS n | OOS win% | "
             "OOS exp(R) | OOS PF | OOS maxDD(R) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for sym, r in results.items():
        a, b = r["is"], r["oos"]
        lines.append(
            f"| {sym} | {a['n']} | {a['win_rate']*100:.0f}% | {a['expectancy_r']:+.2f} "
            f"| {a['profit_factor']:.2f} | {b['n']} | {b['win_rate']*100:.0f}% | "
            f"{b['expectancy_r']:+.2f} | {b['profit_factor']:.2f} | {b['max_drawdown_r']:.1f} |")
    return "\n".join(lines) + "\n" + _tier_table(results)


if __name__ == "__main__":
    results = run_all()
    report = render_report(results)
    print(report)
    with open("reports/phase1_backtest.md", "w") as f:
        f.write(report + "\n")
