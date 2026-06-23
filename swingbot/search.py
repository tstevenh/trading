# swingbot/search.py
"""Pluggable strategy-search harness.

Two building blocks for exploring multiple strategy archetypes against the
SAME reviewed event-driven engine semantics:

  * ``build_features_rich`` -- an M15-indexed, no-lookahead feature *superset*
    that any archetype may draw from (entry TF = M15, pullback TF = H4,
    bias TF = Daily). It reuses the exact alignment approach from
    ``swingbot/features.py`` (resample h1->h4 for the mid/pullback timeframe,
    daily for bias; HTF columns attached only via tf_close_index + align_htf).

  * ``run_strategy`` -- a faithful copy of ``swingbot.backtest.run_backtest``'s
    loop whose ONLY change is that the hardcoded gate + ``build_signal`` block
    is replaced by a single call to a pluggable ``signal_fn``. Every other
    detail (entry next-bar-open + half-spread, stop-checked-before-tp,
    half-spread against you on exits, one position per instrument, ``i = j+1``
    after a trade, EOD exit at last close, ``outcome_r = pnl / risk``) is
    identical, and confluence ``score`` / ``tier`` are still attached.

SignalFn interface
------------------
    def signal_fn(row: dict, piv: list[tuple[str, float]], ts) -> Signal | None

The archetype puts ALL of its logic -- entry conditions plus stop / tp / rr
construction -- inside this function. It may read any feature column present in
``row`` (the dict for bar ``i``) plus ``piv`` (recent ``('H'|'L', price)``
fractal pivots from ``_recent_pivots``) and ``ts`` (``feats.index[i]``). It
returns a fully-formed ``swingbot.strategy.Signal`` or ``None`` to skip the bar.
"""
from swingbot import indicators as ind
from swingbot.align import tf_close_index, align_htf
from swingbot.backtest import Trade, _recent_pivots
from swingbot.grading import confluence_score, tier_of


def build_features_rich(m15, h1, d1):
    """M15-indexed, no-lookahead feature superset for archetype search.

    Entry TF (M15), pullback TF (H4, resampled from H1), bias TF (Daily).
    HTF columns are attached only through tf_close_index + align_htf so a bar
    sees a higher-timeframe value only after that HTF bar has CLOSED.
    """
    # --- Entry timeframe: M15 ------------------------------------------------
    m = m15.copy()
    m["atr"] = ind.atr(m, 14)
    m["m15_ema20"] = ind.ema(m["close"], 20)
    m["m15_ema50"] = ind.ema(m["close"], 50)
    m["m15_ema200"] = ind.ema(m["close"], 200)
    m["m15_rsi"] = ind.rsi(m["close"], 14)
    m["m15_rsi_prev"] = m["m15_rsi"].shift(1)
    m["m15_adx"] = ind.adx(m, 14)["adx"]

    # Bollinger bands: 20-SMA close +/- 2 * rolling std.
    bb_mid = ind.sma(m["close"], 20)
    bb_std = m["close"].rolling(20).std()
    m["bb_mid"] = bb_mid
    m["bb_up"] = bb_mid + 2.0 * bb_std
    m["bb_lo"] = bb_mid - 2.0 * bb_std

    # Rolling breakout levels -- SHIFTED by 1 bar so the current bar is
    # excluded (no lookahead: a breakout level is a prior-bars-only extreme).
    m["roll_high_20"] = m["high"].rolling(20).max().shift(1)
    m["roll_low_20"] = m["low"].rolling(20).min().shift(1)
    m["roll_high_50"] = m["high"].rolling(50).max().shift(1)
    m["roll_low_50"] = m["low"].rolling(50).min().shift(1)

    # --- Pullback timeframe: H4 (resampled from H1) --------------------------
    h4 = h1.resample("4h").agg({"open": "first", "high": "max", "low": "min",
                                "close": "last", "volume": "sum"}).dropna()
    h4["h1_ema20"] = ind.ema(h4["close"], 20)
    h4["h1_ema50"] = ind.ema(h4["close"], 50)
    h4["h1_rsi"] = ind.rsi(h4["close"], 14)
    h4_feat = tf_close_index(h4[["h1_ema20", "h1_ema50", "h1_rsi"]], "4h")

    # --- Bias timeframe: Daily ----------------------------------------------
    d = d1.copy()
    d["d1_close"] = d["close"]
    d["d1_sma50"] = ind.sma(d["close"], 50)
    d["d1_sma200"] = ind.sma(d["close"], 200)
    d_feat = tf_close_index(d[["d1_close", "d1_sma50", "d1_sma200"]], "d1")

    out = align_htf(m, h4_feat, prefix="")          # h1_* already prefixed
    out = align_htf(out, d_feat, prefix="")          # d1_* already prefixed
    return out


def run_strategy(instrument, feats, raw, spread, signal_fn,
                 pivot_lookback=40, min_rr=2.0):
    """Event-driven backtest with a pluggable ``signal_fn``.

    Faithful copy of ``swingbot.backtest.run_backtest``'s loop; the sole
    difference is that the hardcoded gate + ``build_signal`` block is replaced
    by ``signal_fn(row, piv, ts)`` returning a ``Signal`` or ``None``.
    """
    f = feats.copy()
    ts = f.index.to_numpy()
    highs, lows = f["high"].to_numpy(), f["low"].to_numpy()
    opens, closes = f["open"].to_numpy(), f["close"].to_numpy()
    rows = f.to_dict("records")
    half = spread / 2.0
    trades, i, n = [], 1, len(f)

    while i < n - 1:
        row, t = rows[i], f.index[i]
        piv = _recent_pivots(highs, lows, i, pivot_lookback)
        sig = signal_fn(row, piv, t)
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
