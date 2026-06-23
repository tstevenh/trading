# swingbot/grading.py
def _round_number_proximity(price: float) -> bool:
    """Within ~0.1% of a 'round' level (…00 for FX, …0/…00 for gold)."""
    # gold: multiples of 50; fx: multiples of 0.01 (…00 pips) scaled
    if price > 100:                      # gold-like
        nearest = round(price / 50) * 50
    else:                                # fx
        nearest = round(price * 100) / 100
    return abs(price - nearest) / price < 0.001


def confluence_score(row, sig, recent_pivots) -> int:
    score = 0
    # deep pullback (RSI extreme in the pullback direction)
    rsi = row.get("h1_rsi", 50)
    if (sig.side == 1 and rsi < 35) or (sig.side == -1 and rsi > 65):
        score += 1
    # prime London/NY overlap 12-16 UTC
    if sig.ts is not None and 12 <= sig.ts.hour < 16:
        score += 1
    # strong reward
    if sig.rr >= 3.0:
        score += 1
    # round-number confluence near entry
    if _round_number_proximity(sig.entry):
        score += 1
    # structural-level confluence: a pivot near the entry zone
    if any(abs(p - sig.entry) / sig.entry < 0.001 for _, p in recent_pivots):
        score += 1
    return score


def tier_of(score: int) -> str:
    if score >= 4:
        return "SSS"
    if score >= 2:
        return "AA"
    return "A"
