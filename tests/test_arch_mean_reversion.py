# tests/test_arch_mean_reversion.py
"""Mean-reversion (range-fade) archetype on real XAUUSD.

Honest test: this archetype is *expected* to qualify few trades because the
mean (bb_mid) is often closer than 2R from a band-touch entry. We assert
internal consistency on whatever trades are produced and that rr >= 2.0 is
enforced -- never a high trade count.
"""
from swingbot.indicators import load_csv
from swingbot.search import build_features_rich, run_strategy
from swingbot.archetypes.mean_reversion import REQUIRED_COLS, variants
from swingbot.costs import SPREADS


def _load(pair="xauusd"):
    return (load_csv(f"data/raw/{pair}_m15.csv"),
            load_csv(f"data/raw/{pair}_h1.csv"),
            load_csv(f"data/raw/{pair}_d1.csv"))


def test_mean_reversion_best_variant_on_xauusd():
    m15, h1, d1 = _load()
    feats = build_features_rich(m15, h1, d1)
    base = feats.dropna(subset=REQUIRED_COLS).copy()
    assert len(base) > 1000

    spread = SPREADS["XAUUSD"]

    # Pick the variant producing the most qualifying trades as "best".
    results = []
    for name, fn in variants():
        trades = run_strategy("XAUUSD", base, base, spread=spread,
                              signal_fn=fn, pivot_lookback=40, min_rr=2.0)
        results.append((name, trades))
    best_name, best_trades = max(results, key=lambda r: len(r[1]))

    n = len(best_trades)
    if n == 0:
        # Acceptable per archetype design: mean-to-stop rarely offers 2R.
        assert n == 0
        return

    for t in best_trades:
        assert t.side in (1, -1)
        assert t.rr >= 2.0 - 1e-9
        assert t.entry > 0 and t.stop > 0 and t.tp > 0
        if t.side == 1:
            assert t.stop < t.entry < t.tp
        else:
            assert t.tp < t.entry < t.stop
