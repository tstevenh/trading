import pandas as pd

from swingbot.indicators import load_csv
from swingbot.search import build_features_rich, run_strategy
from swingbot.costs import SPREADS
from swingbot.archetypes import breakout_retest as br


def _load(pair="xauusd"):
    return (load_csv(f"data/raw/{pair}_m15.csv"),
            load_csv(f"data/raw/{pair}_h1.csv"),
            load_csv(f"data/raw/{pair}_d1.csv"))


def _prep():
    m15, h1, d1 = _load()
    feats = build_features_rich(m15, h1, d1)
    feats = feats.dropna(subset=br.REQUIRED_COLS).copy()
    # 2020-2026 window.
    feats = feats[(feats.index >= "2020-01-01") & (feats.index < "2026-12-31")]
    return feats


def test_required_cols_present():
    feats = _prep()
    assert set(br.REQUIRED_COLS).issubset(feats.columns)
    assert len(feats) > 1000


def test_best_variant_trades_and_rr():
    feats = _prep()
    spread = SPREADS["XAUUSD"]

    best_name, best_trades = None, []
    for name, fn in br.variants():
        trades = run_strategy("XAUUSD", feats, feats, spread=spread,
                              signal_fn=fn, pivot_lookback=40, min_rr=2.0)
        if len(trades) > len(best_trades):
            best_name, best_trades = name, trades

    assert len(best_trades) > 20, (
        f"best variant {best_name} produced only {len(best_trades)} trades")
    assert all(t.rr >= 2.0 for t in best_trades), \
        "all signalled trades must have rr >= 2.0"
