# tests/test_arch_trend_pullback_plus.py
"""Integration test for the trend_pullback_plus archetype on real XAUUSD."""
import pandas as pd

from swingbot.indicators import load_csv
from swingbot.search import build_features_rich, run_strategy
from swingbot.costs import SPREADS
from swingbot.archetypes.trend_pullback_plus import (
    make_signal_fn, REQUIRED_COLS,
)

# Best variant: strict daily bias, ADX strength gate at 18, H4 RSI pullback < 48.
BEST_SIGNAL_FN = make_signal_fn(adx_min=18.0, rsi_pull=48.0, relaxed=False)


def _load(pair="xauusd"):
    return (load_csv(f"data/raw/{pair}_m15.csv"),
            load_csv(f"data/raw/{pair}_h1.csv"),
            load_csv(f"data/raw/{pair}_d1.csv"))


def test_best_variant_xauusd_2020_2026():
    m15, h1, d1 = _load("xauusd")
    feats = build_features_rich(m15, h1, d1).dropna(subset=REQUIRED_COLS)
    feats = feats[(feats.index >= pd.Timestamp("2020-01-01", tz="UTC"))
                  & (feats.index < pd.Timestamp("2026-12-31", tz="UTC"))]

    spread = SPREADS["XAUUSD"]
    trades = run_strategy("XAUUSD", feats, feats, spread=spread,
                          signal_fn=BEST_SIGNAL_FN, pivot_lookback=40,
                          min_rr=2.0)

    assert len(trades) > 20, f"expected >20 trades, got {len(trades)}"
    assert all(t.rr >= 2.0 for t in trades), "every trade must have rr >= 2.0"
