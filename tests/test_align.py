# tests/test_align.py
import pandas as pd
from swingbot.align import tf_close_index, align_htf


def _frame(start, periods, freq, val0):
    idx = pd.date_range(start, periods=periods, freq=freq, tz="UTC")
    v = pd.Series(range(val0, val0 + periods), index=idx, dtype=float)
    return pd.DataFrame({"open": v, "high": v, "low": v, "close": v, "volume": 1.0},
                        index=idx)


def test_close_index_shifts_by_one_freq():
    d = _frame("2024-01-01", 3, "1D", 0)
    c = tf_close_index(d, "1D")
    # daily bar opened 2024-01-01 closes 2024-01-02 00:00
    assert c.index[0] == pd.Timestamp("2024-01-02", tz="UTC")


def test_no_lookahead_daily_into_m15():
    # daily closes (open+1D): Jan1 bar -> close Jan2 00:00, Jan2 bar -> close Jan3 00:00
    d = _frame("2024-01-01", 3, "1D", 100)   # closes: 100,101,102 for Jan1,2,3 bars
    m = _frame("2024-01-02 00:00", 97, "15min", 0)  # all of Jan 2 (and into Jan 3)
    out = align_htf(m, d, prefix="d1")
    # During Jan 2 session, the only CLOSED daily bar is Jan 1's (close value 100).
    jan2 = out.loc["2024-01-02 00:00":"2024-01-02 23:45"]
    assert (jan2["d1_close"] == 100).all(), "must use prior completed daily, not today's"
    # Once Jan 3 starts, Jan 2's bar (101) has closed.
    assert out.loc["2024-01-03 00:00"]["d1_close"] == 101


def test_pattern_b_no_double_shift():
    """Pre-close-indexed HTF frame must NOT be shifted again by align_htf."""
    d = _frame("2024-01-01", 3, "1D", 100)
    d_ci = tf_close_index(d, "1D")          # index.name == "close_time"
    m = _frame("2024-01-02 00:00", 97, "15min", 0)
    out = align_htf(m, d_ci, prefix="d1")
    # Same expectations as test_no_lookahead_daily_into_m15
    jan2 = out.loc["2024-01-02 00:00":"2024-01-02 23:45"]
    assert (jan2["d1_close"] == 100).all(), "pre-indexed frame: must use prior bar, not today's"
    assert out.loc["2024-01-03 00:00"]["d1_close"] == 101


def test_align_htf_raises_on_none_freq():
    """align_htf must raise ValueError when index.freq is None and not close-indexed."""
    import pytest
    # Irregular gaps => freq is None
    idx = pd.DatetimeIndex(
        ["2024-01-01", "2024-01-02", "2024-01-04", "2024-01-07"],  # skips weekends
        tz="UTC",
    )
    df = pd.DataFrame(
        {"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0},
        index=idx,
    )
    assert df.index.freq is None  # confirm the fixture is irregular
    base = _frame("2024-01-01", 10, "15min", 0)
    with pytest.raises(ValueError, match="htf.index.freq is None"):
        align_htf(base, df, prefix="d1")
