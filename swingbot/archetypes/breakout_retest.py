"""Breakout-retest archetype.

Trade a breakout of a prior N-bar range, entered on the *retest* of the broken
level, in the direction of the daily bias (d1_close vs d1_sma200).

Long logic (short is mirrored):
  * Bias: only go long when d1_close > d1_sma200.
  * Breakout reference: the prior-N-bar high ``roll_high_N`` (excludes the
    current bar). A breakout has occurred when price recently traded above it.
  * Retest entry: price has pulled back to within ``tol * atr`` of the broken
    level from ABOVE and is HOLDING it -- i.e. the bar's low dipped to/under the
    level + tol band (the retest touch) while the close is back >= level. Enter
    long at the close.
  * Stop: ``level - stop_mult * atr`` (just under the retested level).
  * TP: the nearest structural pivot high above from ``piv`` if it yields
    >= rr_target R; otherwise project ``entry + rr_target * risk``. The chosen
    target must be reachable (>= rr_target R). Enforce rr >= 2.

The ``roll_high_N`` level already excludes the current bar, so requiring the
bar to dip to the level (low <= level + tol*atr) and close back above it
(close >= level) captures a pullback-and-hold against the broken resistance
which has now flipped to support.
"""
from swingbot.strategy import Signal

REQUIRED_COLS = [
    "open", "high", "low", "close", "atr",
    "roll_high_20", "roll_low_20", "roll_high_50", "roll_low_50",
    "d1_close", "d1_sma200",
]


def _signal(row, piv, ts, lookback, tol, stop_mult, rr_target, min_rr):
    close = row["close"]
    low = row["low"]
    high = row["high"]
    atr = row["atr"]
    if atr is None or atr <= 0:
        return None

    d1_close = row["d1_close"]
    d1_sma200 = row["d1_sma200"]

    hi_level = row[f"roll_high_{lookback}"]
    lo_level = row[f"roll_low_{lookback}"]
    band = tol * atr

    # --- LONG: bias up, retest of broken resistance (now support) -----------
    if d1_close > d1_sma200:
        level = hi_level
        # Pullback touched the level band from above, and bar closes holding it.
        # close >= level confirms we are still above the broken level.
        # low <= level + band confirms price pulled back into the retest zone.
        # high >= level keeps us at/above the level (genuine support test).
        if (close >= level and low <= level + band and high >= level):
            side = 1
            entry = close
            stop = level - stop_mult * atr
            risk = entry - stop
            if risk <= 0:
                return None
            # Structural target: nearest pivot HIGH above entry, if reachable.
            highs = [p for t, p in piv if t == "H" and p > entry]
            tp = None
            if highs:
                cand = min(highs)               # nearest structural high above
                if (cand - entry) / risk >= rr_target:
                    tp = cand
            if tp is None:
                tp = entry + rr_target * risk    # ATR/R projection fallback
            rr = (tp - entry) / risk
            if rr < min_rr:
                return None
            return Signal(ts=ts, side=side, entry=entry, stop=stop, tp=tp,
                          rr=rr, atr=atr)

    # --- SHORT: bias down, retest of broken support (now resistance) --------
    elif d1_close < d1_sma200:
        level = lo_level
        if (close <= level and high >= level - band and low <= level):
            side = -1
            entry = close
            stop = level + stop_mult * atr
            risk = stop - entry
            if risk <= 0:
                return None
            lows = [p for t, p in piv if t == "L" and p < entry]
            tp = None
            if lows:
                cand = max(lows)                # nearest structural low below
                if (entry - cand) / risk >= rr_target:
                    tp = cand
            if tp is None:
                tp = entry - rr_target * risk
            rr = (entry - tp) / risk
            if rr < min_rr:
                return None
            return Signal(ts=ts, side=side, entry=entry, stop=stop, tp=tp,
                          rr=rr, atr=atr)

    return None


def make_signal_fn(lookback=20, tol=0.5, stop_mult=1.0, rr_target=2.0,
                   min_rr=2.0):
    """Build a ``signal_fn(row, piv, ts) -> Signal | None`` for one variant."""
    def signal_fn(row, piv, ts):
        return _signal(row, piv, ts, lookback=lookback, tol=tol,
                       stop_mult=stop_mult, rr_target=rr_target,
                       min_rr=min_rr)
    return signal_fn


def variants():
    """Return a list of ``(name, signal_fn)`` parameter variants.

    Sweeps lookback in {20, 50}, tol in {0.25, 0.5} ATR, stop_mult in
    {1.0, 1.5} ATR. rr_target fixed at 2.0 (min_rr enforced at 2.0).
    """
    specs = [
        dict(lookback=20, tol=0.50, stop_mult=1.0),
        dict(lookback=20, tol=0.25, stop_mult=1.0),
        dict(lookback=20, tol=0.50, stop_mult=1.5),
        dict(lookback=50, tol=0.50, stop_mult=1.0),
        dict(lookback=50, tol=0.25, stop_mult=1.5),
        dict(lookback=50, tol=0.50, stop_mult=1.5),
    ]
    out = []
    for s in specs:
        name = (f"breakout_retest_lb{s['lookback']}"
                f"_tol{s['tol']}_sm{s['stop_mult']}")
        out.append((name, make_signal_fn(rr_target=2.0, min_rr=2.0, **s)))
    return out
