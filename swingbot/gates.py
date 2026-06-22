# swingbot/gates.py
SESSION_START_H, SESSION_END_H = 7, 16
PULLBACK_RSI_LONG, PULLBACK_RSI_SHORT = 45, 55


def trend_bias(row, relaxed: bool = False) -> int:
    c, s50, s200 = row["d1_close"], row["d1_sma50"], row["d1_sma200"]
    if any(v != v for v in (c, s50, s200)):  # NaN guard
        return 0
    if relaxed:
        return 1 if s50 > s200 else (-1 if s50 < s200 else 0)
    if c > s200 and s50 > s200:
        return 1
    if c < s200 and s50 < s200:
        return -1
    return 0


def _zone(row):
    lo = min(row["h1_ema20"], row["h1_ema50"])
    hi = max(row["h1_ema20"], row["h1_ema50"])
    return lo, hi


def pullback_ok(row, bias: int) -> bool:
    lo, hi = _zone(row)
    if bias == 1:
        return (row["low"] <= hi) and (row["h1_rsi"] < PULLBACK_RSI_LONG)
    if bias == -1:
        return (row["high"] >= lo) and (row["h1_rsi"] > PULLBACK_RSI_SHORT)
    return False


def trigger_ok(row, bias: int) -> bool:
    if bias == 1:
        return (row["close"] > row["m15_ema20"]) and (row["m15_rsi"] > row["m15_rsi_prev"])
    if bias == -1:
        return (row["close"] < row["m15_ema20"]) and (row["m15_rsi"] < row["m15_rsi_prev"])
    return False


def session_ok(ts) -> bool:
    return SESSION_START_H <= ts.hour < SESSION_END_H
