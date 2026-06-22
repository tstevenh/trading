# tests/test_gates.py
import pandas as pd
from swingbot import gates


def test_trend_bias_long_short_none():
    long_row = {"d1_close": 110, "d1_sma200": 100, "d1_sma50": 105}
    short_row = {"d1_close": 90, "d1_sma200": 100, "d1_sma50": 95}
    none_row = {"d1_close": 101, "d1_sma200": 100, "d1_sma50": 99}  # close>200 but 50<200
    assert gates.trend_bias(long_row) == 1
    assert gates.trend_bias(short_row) == -1
    assert gates.trend_bias(none_row) == 0


def test_trend_bias_relaxed_uses_only_50_vs_200():
    row = {"d1_close": 99, "d1_sma200": 100, "d1_sma50": 101}  # 50>200
    assert gates.trend_bias(row, relaxed=True) == 1


def test_pullback_long_requires_zone_and_low_rsi():
    bias = 1
    in_zone = {"h1_ema20": 100, "h1_ema50": 102, "low": 101, "h1_rsi": 40}
    assert gates.pullback_ok(in_zone, bias) is True
    high_rsi = {"h1_ema20": 100, "h1_ema50": 102, "low": 101, "h1_rsi": 60}
    assert gates.pullback_ok(high_rsi, bias) is False


def test_trigger_long_requires_close_above_ema_and_rsi_turning_up():
    bias = 1
    good = {"close": 101, "m15_ema20": 100, "m15_rsi": 48, "m15_rsi_prev": 44}
    assert gates.trigger_ok(good, bias) is True
    no_turn = {"close": 101, "m15_ema20": 100, "m15_rsi": 42, "m15_rsi_prev": 44}
    assert gates.trigger_ok(no_turn, bias) is False


def test_session_ok():
    assert gates.session_ok(pd.Timestamp("2024-01-02 13:00", tz="UTC")) is True
    assert gates.session_ok(pd.Timestamp("2024-01-02 03:00", tz="UTC")) is False
