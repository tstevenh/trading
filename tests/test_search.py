# tests/test_search.py
import pandas as pd

from swingbot import gates
from swingbot.indicators import load_csv
from swingbot.features import build_features
from swingbot.strategy import build_signal
from swingbot.backtest import run_backtest, _recent_pivots
from swingbot.search import build_features_rich, run_strategy
from swingbot.costs import SPREADS

RICH_COLS = [
    "open", "high", "low", "close", "atr",
    "m15_ema20", "m15_ema50", "m15_ema200",
    "m15_rsi", "m15_rsi_prev", "m15_adx",
    "bb_mid", "bb_up", "bb_lo",
    "roll_high_20", "roll_low_20", "roll_high_50", "roll_low_50",
    "h1_ema20", "h1_ema50", "h1_rsi",
    "d1_close", "d1_sma50", "d1_sma200",
]

# Subset that the legacy gates + build_signal actually consume.
GATE_COLS = ["atr", "m15_ema20", "m15_rsi", "m15_rsi_prev",
             "h1_ema20", "h1_ema50", "h1_rsi",
             "d1_close", "d1_sma50", "d1_sma200"]


def _load(pair="xauusd"):
    return (load_csv(f"data/raw/{pair}_m15.csv"),
            load_csv(f"data/raw/{pair}_h1.csv"),
            load_csv(f"data/raw/{pair}_d1.csv"))


def test_build_features_rich_columns_and_density():
    m15, h1, d1 = _load()
    feats = build_features_rich(m15, h1, d1)
    assert set(RICH_COLS).issubset(feats.columns)
    full = feats.dropna(subset=RICH_COLS)
    assert len(full) > 1000


def _make_trend_pullback_signal_fn(relaxed=False, min_rr=2.0):
    """Wrap the EXISTING strategy (gates + build_signal) as a signal_fn."""
    def signal_fn(row, piv, ts):
        bias = gates.trend_bias(row, relaxed=relaxed)
        if bias == 0:
            return None
        if not (gates.session_ok(ts)
                and gates.pullback_ok(row, bias)
                and gates.trigger_ok(row, bias)):
            return None
        return build_signal(row, bias, piv, min_rr=min_rr, ts=ts)
    return signal_fn


def _trade_key(t):
    return (t.side, t.entry_ts, round(t.entry, 8), round(t.stop, 8),
            round(t.tp, 8), t.exit_ts, round(t.exit, 8),
            round(t.outcome_r, 8), t.reason)


def test_run_strategy_equivalent_to_run_backtest():
    """run_strategy + a trend-pullback wrapper == legacy run_backtest."""
    m15, h1, d1 = _load("xauusd")
    # Bounded slice keeps the test fast but covers many trades.
    feats_legacy = build_features(m15, h1, d1)

    # Legacy engine prepares its frame by dropping warmup NaNs; replicate the
    # exact same frame so pivot indices and i=j+1 progression line up.
    base = feats_legacy.dropna(subset=GATE_COLS).copy()
    base = base.iloc[:6000]

    spread = SPREADS["XAUUSD"]
    legacy = run_backtest("XAUUSD", base, base, spread=spread,
                          pivot_lookback=20, min_rr=2.0)

    signal_fn = _make_trend_pullback_signal_fn(min_rr=2.0)
    pluggable = run_strategy("XAUUSD", base, base, spread=spread,
                             signal_fn=signal_fn, pivot_lookback=20,
                             min_rr=2.0)

    assert len(pluggable) == len(legacy)
    assert len(legacy) > 0
    for a, b in zip(legacy, pluggable):
        assert _trade_key(a) == _trade_key(b)
        assert a.score == b.score
        assert a.tier == b.tier
