# Phase 1 — Validation Findings (H1-entry profile)

**Date:** 2026-06-23. **Data:** clean H1 (2020+) + Daily for all 7 pairs (M15 bulk feed was unreliable — pivoted to H1 entries; logic identical, ladder shifted up one TF). **Risk:** flat 1%. **Costs:** spread modeled. IS = pre-2023, OOS = 2023+.

## Verdict: the lean v1 base strategy is NOT yet profitable — but the grading edge is REAL

**Portfolio (OOS, all pairs):** 220 trades, **26.4% win**, avg planned R:R 2.37, **expectancy −0.152R**, profit factor 0.80, max DD 46R. → **Do NOT trade this live as-is.**

The core problem: **win rate (26%) is below breakeven.** With 2.37:1 R:R, breakeven win rate ≈ 30%. The base trigger lets in too many setups that never reach target.

## The key discovery: confluence grading works (this is the path forward)

OOS expectancy by tier is cleanly **monotonic** — higher confluence genuinely predicts better outcomes:

| Tier | n | win% | expectancy(R) |
|---|---|---|---|
| **SSS** | 11 | 36% | **+0.552** ✅ strong |
| AA | 116 | 29% | −0.038 (~breakeven) |
| A | 93 | 22% | **−0.377** ❌ bleeds money |

The 93 A-tier trades are what sink the portfolio. **Selectivity is the edge:** trade only SSS (and possibly AA), skip A entirely. This validates the tiered design — the score earns its keep.

## Per-pair (OOS) — noisy, small samples, no stable per-pair winner

| Pair | OOS n | win% | exp(R) | PF | IS exp(R) | IS PF |
|---|---|---|---|---|---|---|
| XAUUSD | 27 | 37% | +0.092 | 1.14 | −0.264 | 0.65 |
| USDCAD | 26 | 31% | +0.033 | 1.05 | −0.594 | 0.32 |
| GBPUSD | 33 | 27% | −0.049 | 0.93 | −0.237 | 0.69 |
| NZDUSD | 19 | 26% | −0.158 | 0.79 | +0.400 | 1.66 |
| EURUSD | 57 | 25% | −0.177 | 0.77 | +0.019 | 1.03 |
| USDJPY | 23 | 22% | −0.358 | 0.55 | −0.143 | 0.80 |
| USDCHF | 35 | 20% | −0.395 | 0.52 | +0.017 | 1.03 |

Only XAU/USD and USD/CAD are OOS-positive, both marginally (PF <1.2). IS↔OOS flips wildly (e.g. NZD/USD great IS, poor OOS; USD/CAD opposite) → **per-pair signal is mostly noise at these sample sizes.** The reliable signal is by **tier**, not by pair.

## Trade frequency

~**0.25 trades/day across the whole universe** (220 over ~3.5 OOS years). Far below the "~1/day" goal — H1 + strict multi-TF gates are selective. Frequency and profitability pull in opposite directions here: the tier data says get MORE selective (fewer, better trades), not less.

## Honest conclusions

1. **No live trading.** The base edge is negative; this is exactly what Phase 1 exists to catch before risking money.
2. **The grading system is the discovery.** SSS = +0.55R is a real, exploitable edge. The next iteration should require high confluence as a *gate*, not just a label.
3. **Per-pair cuts are premature** — samples too small and unstable. Don't drop pairs yet; the tier filter matters more than the pair.

## Recommended next steps (Phase 1b — tuning, still no live money)

1. **Make confluence a gate:** only emit SSS/AA setups; re-run and measure portfolio expectancy when A-tier is excluded.
2. **Raise win rate:** test trigger refinements (e.g., two-sided pullback-zone check; require trend strength via ADX in the score-as-gate; regime filter).
3. **Get clean M15 data** (different source — Twelve Data / HistData) and test whether M15 entries lift win rate (tighter stops, more setups) — this is also the route to ~1 trade/day.
4. **Walk-forward** the SSS/AA-only variant before trusting it.

---
## M15-entry baseline on CLEAN HistData (added 2026-06-23)
Frequency SOLVED (~1.5 trades/day across universe, ~1,350 OOS trades). But edge still absent:
trend-pullback OOS expectancy negative on 5/7 pairs (only XAUUSD +0.09, GBPUSD +0.03 positive).
Tier signal holds (SSS +0.20 > AA -0.08 > A -0.17) but SSS rare (n=12).
=> trend-pullback alone is NOT the edge. Proceed to multi-archetype search on clean M15.
