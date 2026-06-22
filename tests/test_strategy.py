# tests/test_strategy.py
from swingbot.strategy import build_signal, Signal


def test_long_signal_meets_2to1():
    row = {"close": 100.0, "atr": 1.0}
    # nearest swing low below = 98 (risk 2), next swing high above = 105 (reward 5) -> rr 2.5
    sig = build_signal(row, bias=1, recent_pivots=[("L", 98.0), ("H", 105.0)])
    assert isinstance(sig, Signal)
    assert sig.side == 1 and sig.entry == 100.0
    assert sig.stop == 98.0 and sig.tp == 105.0
    assert round(sig.rr, 2) == 2.5


def test_long_rejected_when_rr_below_min():
    row = {"close": 100.0, "atr": 1.0}
    # swing low 98 (risk 2), swing high 103 (reward 3) -> rr 1.5 < 2.0
    sig = build_signal(row, bias=1, recent_pivots=[("L", 98.0), ("H", 103.0)])
    assert sig is None


def test_atr_floor_widens_too_tight_stop():
    row = {"close": 100.0, "atr": 2.0}
    # swing low 99.5 is only 0.5 away; floor = 100 - 1.5*2 = 97 -> risk 3
    sig = build_signal(row, bias=1, recent_pivots=[("L", 99.5), ("H", 110.0)])
    assert sig.stop == 97.0
