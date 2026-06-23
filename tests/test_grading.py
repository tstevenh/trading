# tests/test_grading.py
from swingbot.grading import confluence_score, tier_of


def test_tier_thresholds():
    assert tier_of(0) == "A"
    assert tier_of(2) == "AA"
    assert tier_of(4) == "SSS"


def test_score_rewards_prime_session_and_high_rr():
    import pandas as pd
    from swingbot.strategy import Signal
    ts = pd.Timestamp("2024-03-04 13:00", tz="UTC")  # prime overlap
    sig = Signal(ts=ts, side=1, entry=2000.0, stop=1980.0, tp=2065.0, rr=3.25, atr=10)
    row = {"h1_rsi": 30}
    score = confluence_score(row, sig, recent_pivots=[("L", 1999.0)])
    assert score >= 2  # prime session (+1) and rr>=3 (+1) at least
