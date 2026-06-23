# Final Validated Portfolio (Phase 1 complete)

_Date: 2026-06-23. M15 entries, 2020–2026 (HistData/Binance). IS = pre-2023 (tuning),
OOS = 2023+ (the honest test). Flat 1% risk, spread modeled. All survived the robustness
gauntlet (parameter-neighborhood + cost-sensitivity + sub-period) and exit optimization._

## The 3 strategies

| # | Instrument | Archetype | Entry variant | Exit policy |
|---|---|---|---|---|
| 1 | **SPX500** (S&P 500) | mean-reversion | `mr_adx18_rsi30_sm15` (fade RSI<30 only when ADX<18; stop 1.5×ATR) | **fixed 3R target** |
| 2 | **ETHUSD** (Ethereum) | trend-pullback | `tpp_adx18_rsi45_relaxed` (50>200 SMA bias, ADX>18, pullback to H4 EMA zone, M15 trigger) | **partial 50% @ +1R → stop to breakeven → runner to +3R** |
| 3 | **EURUSD** | trend-pullback | `tpp_adx18_rsi48` (full trend bias, ADX>18, pullback, M15 trigger) | **fixed 2R target** |

## Out-of-sample performance (2023–2026, the validated numbers)

| Instrument | OOS trades | win% | expectancy | PF | maxDD | net R |
|---|---|---|---|---|---|---|
| SPX500 | 84 | 35% | **+0.339R** | 1.50 | 12.5 | +28.5 |
| ETHUSD | 99 | **61%** | +0.178R | 1.43 | 6.8 | +17.6 |
| EURUSD | 88 | 36% | +0.066R | 1.10 | 16.7 | +5.8 |
| **Portfolio** | **271 (~1.5/week)** | ~44% | **~+0.19R/trade** | — | — | **~+52R / 3.5yr** |

At 1% risk, ~+52R over 3.5 years ≈ ~+15%/yr uncompounded (rough), diversified across index / crypto / FX.

## Honest caveats (carry these into live trading)
- **Thin-to-moderate edge.** PF 1.1–1.5. Real and validated as far as history allows — not a money-printer. Execution quality matters.
- **EURUSD is the weakest link** (+0.066R, resists exit improvement) — kept for diversification; first candidate to cut if it underperforms live.
- **SPX 3R stretches the mean-reversion thesis** (holding past the mean) — data supports it but monitor for regime change (2026 was its weakest year).
- **Residual fluke risk** remains (selected from a large search; the gauntlet shrinks but can't eliminate it).
- **The only true proof is forward paper-trading** — everything above is historical.

## Risk & sizing (live)
- Risk per trade: start **0.5%** (conservative) until forward results confirm; scale toward 1% only with evidence.
- Max concurrent positions: 3 (one per strategy). One position per instrument.
- News blackout for EURUSD/SPX around high-impact USD events (to be added in the live layer).

## Next: Phase 2 — paper trading (forward out-of-sample test)
Wire these 3 to live data + Telegram alerts; forward-test for weeks/months before any real capital.
