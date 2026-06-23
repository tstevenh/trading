# swingbot/archetypes/mean_reversion.py
"""Mean-reversion (range-fade) archetype.

Fade overstretched moves ONLY in a ranging regime. The cardinal rule of this
archetype is: *never fight a strong trend*. A Bollinger-band excursion in a
trending market is continuation, not exhaustion -- so every fade is gated by a
low-ADX (non-trending) regime filter.

Logic (long; short is the mirror):
  * Regime filter : m15_adx < adx_max          (only trade when NOT trending)
  * Entry (long)  : close < bb_lo AND m15_rsi < rsi_lo   (oversold extreme)
  * Stop          : entry - stop_mult * atr     (just below the extreme)
  * Target        : bb_mid                       (revert to the mean)
  * rr            : (bb_mid - entry) / (entry - stop); REQUIRE rr >= 2.0

The mean is frequently *closer* than 2R from a band-touch entry, so a large
fraction of raw setups are honestly rejected for failing rr >= 2.0. That is
expected: this archetype trades rarely. We never relax rr to manufacture
trades.
"""
from swingbot.strategy import Signal

# Feature columns this archetype reads. Callers drop NaNs on these before
# running so every consumed bar has a fully-formed value.
REQUIRED_COLS = [
    "open", "high", "low", "close", "atr",
    "m15_rsi", "m15_adx",
    "bb_mid", "bb_up", "bb_lo",
]

MIN_RR = 2.0


def make_signal_fn(adx_max=20.0, rsi_lo=25.0, rsi_hi=75.0, stop_mult=1.5,
                   min_rr=MIN_RR):
    """Build a ``signal_fn(row, piv, ts) -> Signal | None`` for range-fades.

    Parameters
    ----------
    adx_max   : only trade when m15_adx < adx_max (ranging regime gate).
    rsi_lo    : long entry requires m15_rsi < rsi_lo (oversold).
    rsi_hi    : short entry requires m15_rsi > rsi_hi (overbought).
    stop_mult : ATR multiple for the protective stop beyond the extreme.
    min_rr    : minimum reward/risk; setups below this are rejected (honest).
    """
    def signal_fn(row, piv, ts):
        adx = row["m15_adx"]
        # Regime filter -- NEVER fade a trending market.
        if not (adx < adx_max):
            return None

        close = row["close"]
        atr = row["atr"]
        rsi = row["m15_rsi"]
        bb_mid = row["bb_mid"]
        bb_up = row["bb_up"]
        bb_lo = row["bb_lo"]
        if atr <= 0:
            return None

        # --- Long: oversold excursion below the lower band ------------------
        if close < bb_lo and rsi < rsi_lo:
            entry = close
            stop = entry - stop_mult * atr
            tp = bb_mid                              # revert to the mean
            risk = entry - stop
            reward = tp - entry
            if risk <= 0 or reward <= 0:
                return None
            rr = reward / risk
            if rr < min_rr:
                return None
            return Signal(ts=ts, side=1, entry=entry, stop=stop, tp=tp,
                          rr=rr, atr=atr)

        # --- Short: overbought excursion above the upper band ---------------
        if close > bb_up and rsi > rsi_hi:
            entry = close
            stop = entry + stop_mult * atr
            tp = bb_mid                              # revert to the mean
            risk = stop - entry
            reward = entry - tp
            if risk <= 0 or reward <= 0:
                return None
            rr = reward / risk
            if rr < min_rr:
                return None
            return Signal(ts=ts, side=-1, entry=entry, stop=stop, tp=tp,
                          rr=rr, atr=atr)

        return None

    return signal_fn


def variants():
    """4-6 named variants over adx_max, rsi thresholds, and stop_mult.

    Returns a list of ``(name, signal_fn)`` tuples.
    """
    specs = [
        # name,                       adx_max, rsi_lo, rsi_hi, stop_mult
        ("mr_adx18_rsi25_sm10",       18,      25,     75,     1.0),
        ("mr_adx18_rsi25_sm15",       18,      25,     75,     1.5),
        ("mr_adx22_rsi30_sm10",       22,      30,     70,     1.0),
        ("mr_adx22_rsi30_sm15",       22,      30,     70,     1.5),
        ("mr_adx18_rsi30_sm15",       18,      30,     70,     1.5),
        ("mr_adx22_rsi25_sm10",       22,      25,     75,     1.0),
    ]
    return [
        (name, make_signal_fn(adx_max=adx_max, rsi_lo=rsi_lo, rsi_hi=rsi_hi,
                              stop_mult=stop_mult))
        for name, adx_max, rsi_lo, rsi_hi, stop_mult in specs
    ]
