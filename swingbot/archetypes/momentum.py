# swingbot/archetypes/momentum.py
"""Momentum / continuation archetype.

Ride strong directional thrusts: a fresh breakout of the prior N-bar high/low
that occurs *with* momentum already in progress (strong ADX, aligned EMAs).
There is no pullback / retest -- we enter the breakout bar's continuation.

Because new-high (resp. new-low) breakouts often have no overhead (resp. below)
structural target, the take-profit is a pure ATR-risk projection (rr_target *
risk), and rr is enforced >= min_rr by ``run_strategy``-level construction here.

Each variant returns a ``signal_fn(row, piv, ts) -> Signal | None`` compatible
with ``swingbot.search.run_strategy``.
"""
from swingbot.strategy import Signal

# Columns this archetype reads from a feature row. Callers should
# ``dropna(subset=REQUIRED_COLS)`` before running.
REQUIRED_COLS = [
    "open", "high", "low", "close", "atr",
    "m15_ema20", "m15_ema50",
    "m15_adx",
    "roll_high_20", "roll_low_20", "roll_high_50", "roll_low_50",
    "d1_close", "d1_sma200",
]


def _make_signal_fn(adx_min, breakout, stop_mult, rr_target, min_rr=2.0):
    """Build a momentum/continuation signal_fn.

    Parameters
    ----------
    adx_min : float        minimum m15_adx for a "strong momentum" gate.
    breakout : str         'roll_high_20' or 'roll_high_50' (long breakout
                           level column; short uses the matching roll_low_*).
    stop_mult : float      ATR multiple for the stop distance.
    rr_target : float      reward-to-risk multiple for the TP projection.
    min_rr : float         minimum rr enforced (default 2.0).
    """
    low_col = breakout.replace("high", "low")

    def signal_fn(row, piv, ts):
        close = row["close"]
        atr = row["atr"]
        if atr <= 0:
            return None
        ema20, ema50 = row["m15_ema20"], row["m15_ema50"]
        adx = row["m15_adx"]
        d1_close, d1_sma200 = row["d1_close"], row["d1_sma200"]

        # Strong-momentum gate -- a trend must already be in progress.
        if not (adx > adx_min):
            return None

        bull_bias = d1_close > d1_sma200
        bear_bias = d1_close < d1_sma200

        # --- Long: bias up, aligned EMAs, fresh breakout of prior high -------
        if bull_bias and (close > ema20 > ema50) and close > row[breakout]:
            side = 1
            entry = close
            stop = entry - stop_mult * atr
            risk = entry - stop
            if risk <= 0:
                return None
            tp = entry + rr_target * risk
            rr = (tp - entry) / risk
            if rr < min_rr:
                return None
            return Signal(ts=ts, side=side, entry=entry, stop=stop, tp=tp,
                          rr=rr, atr=atr)

        # --- Short: bias down, aligned EMAs, fresh breakout of prior low -----
        if bear_bias and (close < ema20 < ema50) and close < row[low_col]:
            side = -1
            entry = close
            stop = entry + stop_mult * atr
            risk = stop - entry
            if risk <= 0:
                return None
            tp = entry - rr_target * risk
            rr = (entry - tp) / risk
            if rr < min_rr:
                return None
            return Signal(ts=ts, side=side, entry=entry, stop=stop, tp=tp,
                          rr=rr, atr=atr)

        return None

    return signal_fn


def variants():
    """Return a dict of named momentum/continuation signal_fns.

    Sweeps adx_min in {25, 30}, breakout in {roll_high_20, roll_high_50},
    stop_mult in {1.0, 1.5}, rr_target in {2.0, 2.5} -- 6 representative combos.
    """
    specs = [
        # name,                          adx, breakout,        stop, rr
        ("mom_adx30_b20_s15_rr2.0",      30,  "roll_high_20",  1.5,  2.0),
        ("mom_adx25_b20_s15_rr2.0",      25,  "roll_high_20",  1.5,  2.0),
        ("mom_adx30_b50_s15_rr2.0",      30,  "roll_high_50",  1.5,  2.0),
        ("mom_adx30_b20_s10_rr2.0",      30,  "roll_high_20",  1.0,  2.0),
        ("mom_adx30_b20_s15_rr2.5",      30,  "roll_high_20",  1.5,  2.5),
        ("mom_adx25_b50_s10_rr2.5",      25,  "roll_high_50",  1.0,  2.5),
    ]
    out = {}
    for name, adx, breakout, stop, rr in specs:
        out[name] = _make_signal_fn(adx_min=adx, breakout=breakout,
                                    stop_mult=stop, rr_target=rr)
    return out
