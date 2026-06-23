# swingbot/backtest.py
from dataclasses import dataclass
import numpy as np
from swingbot import gates
from swingbot.strategy import build_signal
from swingbot.grading import confluence_score, tier_of


@dataclass
class Trade:
    instrument: str
    side: int
    entry_ts: object
    entry: float
    stop: float
    tp: float
    exit_ts: object
    exit: float
    rr: float
    outcome_r: float
    bars_held: int
    reason: str
    score: int = 0
    tier: str = "A"


def _recent_pivots(highs, lows, i, lookback, k=2):
    """Fractal pivots within [i-lookback, i] on the entry TF (completed bars only)."""
    piv = []
    lo_i = max(k, i - lookback)
    for j in range(lo_i, i - k + 1):
        wh, wl = highs[j - k:j + k + 1], lows[j - k:j + k + 1]
        if highs[j] == wh.max() and wh.argmax() == k:
            piv.append(("H", highs[j]))
        elif lows[j] == wl.min() and wl.argmin() == k:
            piv.append(("L", lows[j]))
    return piv


def run_backtest(instrument, feats, m15_raw, spread, relaxed_trend=False,
                 pivot_lookback=20, risk_pct=1.0, min_rr=2.0):
    f = feats.dropna(subset=["atr", "m15_ema20", "m15_rsi", "m15_rsi_prev",
                             "h1_ema20", "h1_ema50", "h1_rsi",
                             "d1_close", "d1_sma50", "d1_sma200"]).copy()
    ts = f.index.to_numpy()
    highs, lows = f["high"].to_numpy(), f["low"].to_numpy()
    opens, closes = f["open"].to_numpy(), f["close"].to_numpy()
    rows = f.to_dict("records")
    half = spread / 2.0
    trades, i, n = [], 1, len(f)

    while i < n - 1:
        row, t = rows[i], f.index[i]
        bias = gates.trend_bias(row, relaxed=relaxed_trend)
        if (bias != 0 and gates.session_ok(t)
                and gates.pullback_ok(row, bias)
                and gates.trigger_ok(row, bias)):
            piv = _recent_pivots(highs, lows, i, pivot_lookback)
            sig = build_signal(row, bias, piv, min_rr=min_rr, ts=t)
            if sig is not None:
                # enter next bar open + half-spread against us
                entry = opens[i + 1] + half * sig.side
                stop, tp, side = sig.stop, sig.tp, sig.side
                risk = abs(entry - stop)
                exit_px, reason, j = None, None, i + 1
                while j < n:
                    hi, lo = highs[j], lows[j]
                    if side == 1:
                        if lo <= stop:               # stop checked first (conservative)
                            exit_px, reason = stop - half, "stop"; break
                        if hi >= tp:
                            exit_px, reason = tp - half, "tp"; break
                    else:
                        if hi >= stop:
                            exit_px, reason = stop + half, "stop"; break
                        if lo <= tp:
                            exit_px, reason = tp + half, "tp"; break
                    j += 1
                if exit_px is None:
                    exit_px, reason, j = closes[n - 1], "eod", n - 1
                pnl = (exit_px - entry) * side
                outcome_r = pnl / risk if risk > 0 else 0.0
                score = confluence_score(row, sig, piv)
                trades.append(Trade(instrument, side, t, entry, stop, tp,
                                    f.index[j], exit_px, sig.rr, outcome_r,
                                    j - (i + 1), reason,
                                    score=score, tier=tier_of(score)))
                i = j + 1                            # no overlapping positions
                continue
        i += 1
    return trades
