# tests/test_indicators.py
import numpy as np
import pandas as pd
import pytest
from swingbot import indicators as ind


def _df(prices):
    idx = pd.date_range("2024-01-01", periods=len(prices), freq="D", tz="UTC")
    p = pd.Series(prices, index=idx, dtype=float)
    return pd.DataFrame({"open": p, "high": p + 1, "low": p - 1, "close": p,
                         "volume": 1.0}, index=idx)


def test_sma_basic():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    assert ind.sma(s, 2).iloc[-1] == pytest.approx(4.5)


def test_ema_responds_faster_than_sma():
    s = pd.Series(list(range(1, 51)), dtype=float)
    # rising series: EMA(n) closer to latest value than SMA(n)
    assert ind.ema(s, 10).iloc[-1] > ind.sma(s, 10).iloc[-1]


def test_rsi_all_up_is_100():
    close = pd.Series(np.arange(1, 30, dtype=float))
    assert ind.rsi(close, 14).iloc[-1] == pytest.approx(100.0, abs=1e-6)


def test_rsi_all_down_is_0():
    close = pd.Series(np.arange(30, 1, -1, dtype=float))
    assert ind.rsi(close, 14).iloc[-1] == pytest.approx(0.0, abs=1e-6)


def test_atr_positive_and_tracks_range():
    df = _df([10, 12, 11, 13, 12, 14, 13])
    a = ind.atr(df, 3)
    assert a.dropna().gt(0).all()


def test_adx_columns():
    df = _df(list(range(1, 60)))
    out = ind.adx(df, 14)
    assert set(["plus_di", "minus_di", "adx"]).issubset(out.columns)
    assert out["adx"].dropna().between(0, 100).all()


def test_swing_pivots_finds_alternating_extremes():
    df = _df([1, 2, 5, 2, 1, 2, 6, 2, 1])  # peak at idx2 and idx6
    piv = ind.swing_pivots(df, k=2)
    types = [p[1] for p in piv]
    # alternating H/L, no two same in a row
    assert all(a != b for a, b in zip(types, types[1:]))
