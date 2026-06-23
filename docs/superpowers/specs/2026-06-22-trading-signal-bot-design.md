# Design Spec — Multi-Pair Trend-Pullback Signal Bot

**Date:** 2026-06-22
**Status:** Approved for planning
**Author:** thart@digirx.com + Claude

---

## 1. Goal & scope

Build a semi-automated trading system that scans a universe of FX majors + gold
24×5, detects high-quality ("S-tier") **trend-pullback** setups using deterministic
rules, and alerts the user with a full thesis + risk plan. The system progresses
in phases from backtest → live alerts → optional auto-execution, with a feedback
loop that improves the rules over time from logged trade outcomes.

**Design principles (non-negotiable):**
- **Signals come from deterministic code, never the LLM.** The LLM only explains
  signals and reviews performance. Every rule must be backtestable.
- **Validated over plausible.** No rule goes live until it survives out-of-sample /
  walk-forward backtesting. The backtest is the arbiter of every keep/drop decision.
- **Risk management lives in code, not discretion.**
- **Quality over forced frequency.** No trade is ever forced; some days = no trade.

**Realistic target (not a vanity win rate):** positive expectancy with controlled
drawdown — aim ~50–60% win rate at ≥2:1 reward:risk. We do NOT chase 80% win rate
(that incentivizes tiny TPs / no stops and blows up accounts).

## 2. Step 0 findings (data-grounded basis)

Full reports: `reports/step0_summary.md`, `step0_universe.md`, `step0_session.md`.
Data: Dukascopy bid — Daily 2010→2026 (~16yr), H1 2020→2026, M15 2024→2026.

- **Gold (XAU/USD) is the strongest trender** (60% above 200-SMA, +279%/16yr, highest
  volatility) → best trend-pullback candidate and likely the top setup source.
- **EUR/USD is range-biased** (−20%/16yr) — works but fires less; user-priority focus.
- **2:1 R:R is structurally realistic** — ~76–79% of swings ≥ 2× ATR across all pairs.
- **ATR-based stops mandatory** — gold has fat down-tails (skew −0.63, kurtosis 8.8).
- **London/NY overlap (12–16 UTC) is prime** — ~2.5× quiet-hours movement; peak 13–14 UTC.
- **Typical swing leg ≈ 5 days** → 2–3 day holds capture a solid chunk.

## 3. Instrument universe

Scan all 7, trade the best-graded setup(s) of the day (EUR/USD + gold prioritized
when grades tie):

`XAU/USD, USD/JPY, EUR/USD, USD/CHF, NZD/USD, GBP/USD, USD/CAD`

**AUD/USD dropped** (weakest trendiness, most ranging). The backtest may cut further
on profitability (e.g., USD/CAD's low volatility vs spread).

## 4. Strategy — trend-pullback

Two timeframe **profiles** sharing one engine. **Build & prove the SWING profile
first**; add INTRADAY later as a second config, independently validated.

| Profile | TFs | Hold | Build order |
|---|---|---|---|
| Swing | Daily (bias) → H1 (pullback) → M15 (trigger) | 2–3 days | FIRST |
| Intraday | H4 (bias) → H1 (pullback) → M15 (trigger) | intraday–1 day | LATER |

### Gates (long example; short is mirrored). A signal fires only if ALL pass.

| Gate | Rule | Initial params (to validate) |
|---|---|---|
| ① Trend/bias (HTF) | Aligned trend | Daily close > 200-SMA **and** 50-SMA > 200-SMA. *(EUR/USD: relax to 50>200.)* |
| ② Pullback zone (MTF) | Real pullback into value | Price tags H1 20–50 EMA zone; H1 RSI(14) dipped < 45 (long) |
| ③ Entry trigger (LTF) | Trend resumption | M15 closes back above 20-EMA at the zone, RSI turning up |
| ④ R:R ≥ 2:1, reachable TP | Fixed TP, no trailing | Stop = pullback swing low, floored at entry − 1.5×ATR. TP: prefer the nearest structural level ahead — if it gives ≥2R, use it; if it gives <2R, reject (overhead resistance caps the reachable target). If there is NO structural level ahead (price at new highs in a strong trend), project a fixed 2R target (reachable by construction). This avoids taking zero trades in the strongest uptrends. Projected-vs-structural targets are tagged and compared in the backtest. |
| ⑤ Session timing | Prime hours only | Enter 07:00–16:00 UTC (prime 12–16). No Asia/late illiquid. |
| ⑥ News blackout | Avoid high-impact | No new entry −30/+15 min around high-impact USD events (NFP/CPI/FOMC); wider for FOMC. Source: ForexFactory calendar. Fail-safe: block if calendar fetch fails. |
| ⑦ Risk limits | Portfolio guards | Max 2 concurrent positions; one per instrument; daily-loss stop. |

### Setup grading & tiered risk

An objective score grades each signal by **confluence**: trend strength (ADX),
depth into value zone, all-3-TF alignment, prime-session timing, available R:R,
and structure cleanliness. Higher confluence → higher tier → larger risk:

| Tier | Risk per trade |
|---|---|
| A | 0.5% |
| AA | 1.0% |
| SSS | 1.5% (**hard cap 2%**) |

**Tier risk must be earned by data:** start at the above; raise SSS toward the 2%
cap ONLY after the backtest proves higher tiers genuinely have higher expectancy.

### Indicator scope — lean core first, confluence added by evidence

The **v1 core** is 5 automatable tools: EMA/SMA (trend + pullback zone), ADX (trend
strength), RSI (pullback + trigger), ATR (stops/targets), swing pivots (structure =
automated S&R for stop/target placement). We prove the base edge with this core
ONLY — adding tools = adding parameters = overfitting risk.

**Confluence boosters** (S&R refinements) are then tested **in the grading layer**,
NOT as hard gates: horizontal S&R levels (clustered prior swings), round/psychological
numbers (esp. gold, e.g. 4000/4100), Fibonacci 38–61% retracement, prior day/week
high-low, session highs/lows. A setup whose EMA pullback zone *also* aligns with these
scores higher → higher tier → bigger risk. Each booster is kept ONLY if the backtest
shows it lifts expectancy; the rest are discarded. The base edge must stand on the
lean core before any booster is trusted.

### Direction
Both long and short (gates mirrored).

### Frequency
~1 quality setup/day **on average** sourced from the 7-pair universe — never forced.

## 5. Architecture

```
Scheduler (24×5, wakes on candle close per profile)
   └─ Data layer ........ pull OHLC for all pairs/TFs from data provider
   └─ Indicator layer ... ATR, EMA/SMA, ADX, RSI, swing pivots (indicators.py)
   └─ Gate engine ....... ①..⑦ deterministic filters → setup or none
   └─ Grader ............ confluence score → tier → risk %
   └─ Thesis (LLM, opt) . Claude writes human-readable explanation
   └─ Notifier .......... Telegram message (entry/stop/TP/tier/R:R/why)
   └─ Journal DB ........ log every signal + features + outcome
   └─ [Phase 4] Executor  broker API order + hard risk checks
```

Units are independently testable; the gate engine + grader are pure functions over
indicator series so the SAME code runs in backtest and live (no divergence).

## 6. Data & messaging providers

- **Backtesting / Step 0:** Dukascopy (free, no key) — already downloaded.
- **Live data (Phase 2+):** Twelve Data or TraderMade (free tier) for live quotes;
  OANDA if account is restored.
- **Execution (Phase 4):** broker API — OANDA (if restored) or MetaTrader 5 via broker.
- **Alerts:** **Telegram** (easiest — BotFather token, one HTTP call). Discord = easy swap.
- **News calendar:** ForexFactory weekly JSON (high-impact USD events).

## 7. Self-learning / feedback loop (NOT a black-box retrainer)

With ~1 trade/day (~250/yr), data is far too sparse for ML retraining (overfits noise).
Instead, a disciplined cycle:
1. **Journal** every signal: features at entry, tier, decision, outcome (R-multiple,
   win/loss, MAE/MFE).
2. **Review** (weekly, Claude via subscription): generate hypotheses from the journal
   ("losses cluster in X session", "tier SSS underperforms on USD/CAD").
3. **Validate**: any proposed rule/param change is backtested + walk-forward tested
   before adoption. The LLM proposes; the backtest decides.
4. **Version** every rule change. Tune params within guardrails; never free-learn live.

## 8. Validation methodology

- **In-sample** (e.g. 2010–2022): design/tune rules.
- **Out-of-sample** (e.g. 2023–2026): untouched "exam"; edge must hold here.
- **Walk-forward**: rolling re-validation; check for overfitting.
- **Costs modeled**: spread + commission per trade (kills naive high-frequency edges).
- **Metrics**: expectancy, win rate, avg R, profit factor, Sharpe, Calmar, max drawdown,
  trade count. A rule is kept only on out-of-sample positive expectancy + acceptable DD.

## 9. Phased delivery

| Phase | Deliverable | Money at risk |
|---|---|---|
| 0 ✅ | Data + instrument characterization | none |
| 1 | Backtest engine + swing strategy + validation report | none |
| 2 | Live data + Telegram alerts (paper) | none |
| 3 | Journal DB + weekly learning review | none |
| 4 | Broker auto-execution + hard risk limits (start tiny) | real |

Each phase is gated on the prior proving out. Intraday profile = optional add-on
after the swing profile is proven.

## 10. Non-goals / explicit caveats

- Not an "80% win rate" or guaranteed-profit system. No such thing exists.
- The LLM never decides entries.
- No live execution until months of proven paper/forward results.
- Unofficial/free data is fine for research; live/execution needs broker-grade data.
- Past backtest performance does not guarantee future results.
