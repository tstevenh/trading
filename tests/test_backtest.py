# tests/test_backtest.py
import numpy as np
import pandas as pd
from swingbot.backtest import run_backtest, Trade


def _synth_uptrend_pullback():
    """Construct a tiny M15 frame that forces exactly one long setup then a win."""
    idx = pd.date_range("2024-03-04 12:00", periods=40, freq="15min", tz="UTC")
    # price: dip then rally; columns pre-baked so gates fire on the dip-recovery bar
    close = np.concatenate([np.linspace(100, 98, 10),   # pullback
                            np.linspace(98.1, 110, 30)])  # resume up
    df = pd.DataFrame(index=idx)
    df["open"] = close
    df["high"] = close + 0.2
    df["low"] = close - 0.2
    df["close"] = close
    df["atr"] = 1.0
    df["m15_ema20"] = pd.Series(close, index=idx).ewm(span=20, adjust=False).mean()
    df["m15_rsi"] = 50.0
    df["m15_rsi_prev"] = 49.0
    df["h1_ema20"] = 99.0
    df["h1_ema50"] = 101.0
    df["h1_rsi"] = 40.0          # pullback condition satisfied
    df["d1_close"] = 110.0
    df["d1_sma50"] = 105.0
    df["d1_sma200"] = 100.0      # long bias
    return df


def test_engine_produces_a_trade_with_R_outcome():
    feats = _synth_uptrend_pullback()
    trades = run_backtest("XAUUSD", feats, feats, spread=0.30,
                          pivot_lookback=10, risk_pct=1.0)
    assert len(trades) >= 1
    t = trades[0]
    assert isinstance(t, Trade)
    assert t.side == 1
    assert t.reason in ("tp", "stop", "eod")
    # win target was reachable in the rally -> expect positive R (net of spread)
    assert t.outcome_r > 0


def test_no_two_open_positions_same_instrument():
    feats = _synth_uptrend_pullback()
    trades = run_backtest("XAUUSD", feats, feats, spread=0.30, pivot_lookback=10)
    # entries must not overlap in time
    for a, b in zip(trades, trades[1:]):
        assert a.exit_ts <= b.entry_ts
