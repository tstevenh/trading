# swingbot/archetypes/trend_pullback_plus.py
"""Refined trend-pullback archetype ("trend_pullback_plus").

Improves on the negative-edge baseline trend-pullback by adding a trend
*strength* gate (ADX) so only strong, well-established trends are traded.
All other logic mirrors the reviewed gate semantics (daily bias, two-sided
H4 pullback zone tag, M15 momentum trigger), and stop/TP/RR construction is
delegated to ``swingbot.strategy.build_signal``.

Long logic (short mirrors):
  * Bias:     d1_close > d1_sma200 AND d1_sma50 > d1_sma200
              (relaxed variant: d1_sma50 > d1_sma200 only)
  * Strength: m15_adx > adx_min          <-- the key refinement
  * Pullback: H4 zone tagged two-sided
              min(h1_ema20,h1_ema50) <= low <= max(h1_ema20,h1_ema50)
              AND h1_rsi < rsi_pull
  * Trigger:  close > m15_ema20 AND m15_rsi > m15_rsi_prev
  * Build the Signal via build_signal(row, bias, piv, ts=ts).
"""
from swingbot.strategy import build_signal

# Every feature column read by the signal functions below.
REQUIRED_COLS = [
    "open", "high", "low", "close", "atr",
    "m15_ema20", "m15_rsi", "m15_rsi_prev", "m15_adx",
    "h1_ema20", "h1_ema50", "h1_rsi",
    "d1_close", "d1_sma50", "d1_sma200",
]


def _bias(row, relaxed):
    c, s50, s200 = row["d1_close"], row["d1_sma50"], row["d1_sma200"]
    if any(v != v for v in (c, s50, s200)):      # NaN guard
        return 0
    if relaxed:
        return 1 if s50 > s200 else (-1 if s50 < s200 else 0)
    if c > s200 and s50 > s200:
        return 1
    if c < s200 and s50 < s200:
        return -1
    return 0


def make_signal_fn(adx_min=18.0, rsi_pull=45.0, relaxed=False, min_rr=2.0):
    """Build a ``signal_fn(row, piv, ts) -> Signal | None`` for this archetype."""

    def signal_fn(row, piv, ts):
        bias = _bias(row, relaxed)
        if bias == 0:
            return None

        adx = row["m15_adx"]
        if adx != adx or adx <= adx_min:          # NaN guard + strength gate
            return None

        lo_z = min(row["h1_ema20"], row["h1_ema50"])
        hi_z = max(row["h1_ema20"], row["h1_ema50"])

        if bias == 1:
            # Pullback: low dipped into the H4 zone, H4 RSI showing pullback.
            if not (lo_z <= row["low"] <= hi_z and row["h1_rsi"] < rsi_pull):
                return None
            # Trigger: reclaim above M15 EMA20 with rising RSI.
            if not (row["close"] > row["m15_ema20"]
                    and row["m15_rsi"] > row["m15_rsi_prev"]):
                return None
        else:
            if not (lo_z <= row["high"] <= hi_z and row["h1_rsi"] > (100.0 - rsi_pull)):
                return None
            if not (row["close"] < row["m15_ema20"]
                    and row["m15_rsi"] < row["m15_rsi_prev"]):
                return None

        return build_signal(row, bias, piv, min_rr=min_rr, ts=ts)

    return signal_fn


def variants():
    """Named variants over adx_min, rsi_pull, relaxed (4-6 combos)."""
    out = []
    for adx_min in (18.0, 25.0):
        for rsi_pull in (42.0, 48.0):
            name = f"tpp_adx{int(adx_min)}_rsi{int(rsi_pull)}"
            out.append((name, make_signal_fn(adx_min=adx_min, rsi_pull=rsi_pull,
                                             relaxed=False)))
    # Relaxed-bias variants (sma-cross only) at the two ADX thresholds.
    out.append(("tpp_adx18_rsi45_relaxed",
                make_signal_fn(adx_min=18.0, rsi_pull=45.0, relaxed=True)))
    out.append(("tpp_adx25_rsi45_relaxed",
                make_signal_fn(adx_min=25.0, rsi_pull=45.0, relaxed=True)))
    return out
