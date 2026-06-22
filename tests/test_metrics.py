# tests/test_metrics.py
import pytest
from swingbot.metrics import summarize
from swingbot.backtest import Trade


def _t(r):
    return Trade("X", 1, None, 0, 0, 0, None, 0, 2.0, r, 1, "tp")


def test_summarize_basic():
    trades = [_t(2.0), _t(-1.0), _t(2.0), _t(-1.0)]  # 50% win, 2:1
    s = summarize(trades, risk_pct=1.0)
    assert s["n"] == 4
    assert s["win_rate"] == pytest.approx(0.5)
    assert s["avg_r"] == pytest.approx(0.5)
    assert s["expectancy_r"] == pytest.approx(0.5)
    # gross win 4.0, gross loss 2.0 -> PF 2.0
    assert s["profit_factor"] == pytest.approx(2.0)


def test_max_drawdown_r():
    trades = [_t(2.0), _t(-1.0), _t(-1.0), _t(-1.0)]  # peak +2 then -3 -> DD 3
    s = summarize(trades)
    assert s["max_drawdown_r"] == pytest.approx(3.0)


def test_empty():
    s = summarize([])
    assert s["n"] == 0 and s["expectancy_r"] == 0
