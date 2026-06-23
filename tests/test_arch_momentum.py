# tests/test_arch_momentum.py
"""Momentum/continuation archetype on real XAUUSD M15 data (2020-2026)."""
import pandas as pd

from swingbot.indicators import load_csv
from swingbot.search import build_features_rich, run_strategy
from swingbot.costs import SPREADS
from swingbot.archetypes import momentum


def _load(pair="xauusd"):
    return (load_csv(f"data/raw/{pair}_m15.csv"),
            load_csv(f"data/raw/{pair}_h1.csv"),
            load_csv(f"data/raw/{pair}_d1.csv"))


def test_momentum_best_variant_xauusd():
    m15, h1, d1 = _load("xauusd")
    feats = build_features_rich(m15, h1, d1)
    feats = feats.dropna(subset=momentum.REQUIRED_COLS).copy()
    feats = feats[(feats.index >= "2020-01-01") & (feats.index < "2026-12-31")]

    variants = momentum.variants()
    assert len(variants) >= 4 and len(variants) <= 6

    spread = SPREADS["XAUUSD"]

    # Pick the best variant by trade count (proxy for a workable archetype).
    results = {}
    for name, fn in variants.items():
        trades = run_strategy("XAUUSD", feats, feats, spread=spread,
                              signal_fn=fn, pivot_lookback=40, min_rr=2.0)
        results[name] = trades

    best_name = max(results, key=lambda k: len(results[k]))
    best = results[best_name]

    assert len(best) > 20, f"{best_name} only produced {len(best)} trades"
    assert all(t.rr >= 2.0 for t in best), "all trades must have rr >= 2.0"
