# swingbot/strategy.py
from dataclasses import dataclass


@dataclass
class Signal:
    ts: object
    side: int
    entry: float
    stop: float
    tp: float
    rr: float
    atr: float


def build_signal(row, bias, recent_pivots, atr_floor_mult=1.5, min_rr=2.0,
                 ts=None):
    entry, atr = row["close"], row["atr"]
    lows = [p for t, p in recent_pivots if t == "L"]
    highs = [p for t, p in recent_pivots if t == "H"]
    if bias == 1:
        cand = [p for p in lows if p < entry]
        if not cand:
            return None
        struct_stop = max(cand)                      # nearest swing low below
        stop = min(struct_stop, entry - atr_floor_mult * atr)
        risk = entry - stop
        tps = [p for p in highs if p > entry]
        tp = min(tps) if tps else entry + min_rr * risk   # fallback: ATR projection
        reward = tp - entry
    elif bias == -1:
        cand = [p for p in highs if p > entry]
        if not cand:
            return None
        struct_stop = min(cand)
        stop = max(struct_stop, entry + atr_floor_mult * atr)
        risk = stop - entry
        tps = [p for p in lows if p < entry]
        tp = max(tps) if tps else entry - min_rr * risk   # fallback: ATR projection
        reward = entry - tp
    else:
        return None
    if risk <= 0:
        return None
    rr = reward / risk
    if rr < min_rr:
        return None
    return Signal(ts=ts, side=bias, entry=entry, stop=stop, tp=tp, rr=rr, atr=atr)
