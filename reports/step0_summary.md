# Step 0 — Instrument Characterization Summary

**Data source:** Dukascopy (bid). **Generated:** 2026-06-22.
**Spans:** Daily 2010-01→2026-06 (~16 yr, ~5,125 bars); H1 2020-01→2026-06 (~6.5 yr); M15 2024-01→2026-06 (~2.5 yr).
Both XAU/USD and EUR/USD. Purpose: ground the strategy hypothesis in how the markets actually behave — not to mine rules.

---

## Headline conclusions

1. **Gold (XAU/USD) is a strong macro-trender** — 60% of days above the 200-SMA, 61% of days in a bullish 50>200 regime, +279% over 16 years. Best trend-pullback candidate.
2. **EUR/USD is two-way / range-biased** — only 47% above 200-SMA, −20% over 16 years. Trend-pullback works but fires less often; expect fewer clean trends than gold.
3. **2:1 R:R is realistic on both** — ~76–77% of swings are ≥ 2× ATR, so targets at 2× risk have structural room.
4. **ATR-based stops are mandatory**, especially gold: negative skew (−0.63) + fat tails (kurtosis 8.8) = occasional violent down-spikes. Fixed-pip stops would get wicked out.
5. **Trade the London/NY overlap.** Both instruments move far more 12:00–16:00 UTC (gold ~2.5× quiet hours), peaking 13:00–14:00 UTC. Best entry-scan window ≈ 07:00–16:00 UTC; avoid Asia/late illiquid hours.
6. **Hold horizon fits.** Typical swing leg ≈ 5 days (median); a 2–3 day hold captures a solid chunk. May let winners trail to capture fuller legs.

---

## Detail: trend vs range

| Metric | Gold (XAU/USD) | EUR/USD |
|---|---|---|
| Days above 200-SMA | **60.4%** | 46.7% |
| Bullish regime (50>200 SMA) | **61.1%** | 45.3% |
| ADX>25 (trending) | 44.6% | 42.6% |
| ADX<20 (ranging) | 34.6% | 36.5% |
| Efficiency ratio (10d mean) | 0.35 | 0.33 |
| 16-yr buy & hold | **+279%** | −20% |

> Note: 1-day return autocorrelation is ~0 for both — that is normal for liquid
> markets and does NOT contradict trend-following. The edge is in the multi-day
> swing/200-SMA structure, not in predicting tomorrow from today.

## Detail: volatility (stop/target sizing)

| Metric | Gold | EUR/USD |
|---|---|---|
| ATR% median (daily) | 1.2% | 0.6% |
| ATR% p90 | 1.8% | 1.0% |
| ATR% now (Jun 2026) | **2.5% (elevated)** | 0.5% |
| Return skew / kurtosis | −0.63 / 8.8 | 0.07 / 3.0 |

Gold needs ~2× wider stops than EUR/USD in % terms, and is in a high-vol regime right now.

## Detail: swing structure

| Metric | Gold | EUR/USD |
|---|---|---|
| Median swing duration | ~5 days | ~5 days |
| Median swing amplitude | 2.8× ATR | 2.8× ATR |
| Swings ≥ 2× ATR | 76.2% | 77.3% |

## Detail: session activity (avg hourly range %, H1)

| Session (UTC) | Gold | EUR/USD |
|---|---|---|
| Asia 00–07 | 0.253% | 0.095% |
| London 07–12 | 0.284% | 0.158% |
| **London/NY overlap 12–16** | **0.475%** | **0.210%** |
| New York 16–21 | 0.263% | 0.116% |
| Late/illiquid 21–24 | 0.189% | 0.063% |

Peak hours: 13:00–14:00 UTC for both.

---

## Implications for the strategy (feeds Step 1)

- **Primary instrument: Gold.** Strongest, cleanest trend → highest-quality trend-pullback setups. EUR/USD as secondary, possibly with a more permissive/balanced trend filter.
- **Setup archetype: trend-pullback** (with-trend, buy dips in uptrend / sell rallies in downtrend) — directly supported by the trend stats.
- **Stops: ATR-based** (e.g. 1.5× ATR), sized to instrument; never fixed pips.
- **Targets: ≥ 2× risk**, justified by swing-amplitude data.
- **Timing gate: only scan/enter ~07:00–16:00 UTC**, prime 12:00–16:00; this doubles as part of the quality filter.
- **News gate: essential for gold** given its fat down-tails (NFP/CPI/FOMC blackout).
- **Timeframes: Daily (bias) → H1 (setup) → M15 (entry trigger)** as the swing profile, to be validated; test M15 vs H1 entry given gold's intraday noise.
