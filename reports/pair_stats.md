# Per-Instrument Strategy Stats (candidates)

_M15 entries, 2020–2026. OOS = 2023+. Flat 1% risk, spread modeled. Verdict from robustness gauntlet (neighborhood + cost + sub-period)._

## OOS summary table

| Instrument | Strategy | Verdict | OOS n | /day | win% | avg R:R | exp(R) | avgWin | avgLoss | PF | maxDD | net R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SPX500 | mean reversion | ROBUST | 84 | 0.09 | 38% | 2.41 | +0.216 | +2.26 | -1.04 | 1.34 | 9.2 | +18.2 |
| ETHUSD | trend pullback plus | ROBUST | 99 | 0.11 | 40% | 2.08 | +0.149 | +1.91 | -1.05 | 1.24 | 11.8 | +14.7 |
| EURUSD | trend pullback plus | ROBUST | 88 | 0.10 | 38% | 2.02 | +0.074 | +1.90 | -1.02 | 1.12 | 13.9 | +6.5 |
| GER40 | momentum | ROBUST (marginal) | 432 | 0.48 | 37% | 2.00 | +0.057 | +1.91 | -1.02 | 1.09 | 17.5 | +24.5 |
| NAS100 | momentum | fragile-decay | 508 | 0.57 | 33% | 2.50 | +0.097 | +2.38 | -1.02 | 1.14 | 21.5 | +49.4 |
| JPN225 | breakout retest | fragile-cost | 938 | 1.06 | 37% | 2.00 | +0.037 | +1.84 | -1.03 | 1.06 | 44.4 | +34.7 |

## Detail

### SPX500 — mean_reversion (ROBUST)
- M15 window 2020–2026 | IS=pre-2023, OOS=2023+
- **OOS:** n=84, 0.09/day, win 38.1%, avg planned R:R 2.41, expectancy +0.216R, avg win +2.26R / avg loss -1.04R, PF 1.34, maxDD 9.2R, net +18.2R, avg hold 7 bars
- **IS:** n=88, win 35.2%, expectancy +0.044R, PF 1.07
- **Walk-forward OOS by year:** 2023: n=27 exp=+0.293, 2024: n=26 exp=+0.203, 2025: n=17 exp=+0.535, 2026: n=14 exp=-0.297
### ETHUSD — trend_pullback_plus (ROBUST)
- M15 window 2020–2026 | IS=pre-2023, OOS=2023+
- **OOS:** n=99, 0.11/day, win 40.4%, avg planned R:R 2.08, expectancy +0.149R, avg win +1.91R / avg loss -1.05R, PF 1.24, maxDD 11.8R, net +14.7R, avg hold 101 bars
- **IS:** n=69, win 46.4%, expectancy +0.243R, PF 1.43
- **Walk-forward OOS by year:** 2023: n=27 exp=+0.118, 2024: n=27 exp=+0.234, 2025: n=33 exp=+0.095, 2026: n=12 exp=+0.173
### EURUSD — trend_pullback_plus (ROBUST)
- M15 window 2020–2026 | IS=pre-2023, OOS=2023+
- **OOS:** n=88, 0.10/day, win 37.5%, avg planned R:R 2.02, expectancy +0.074R, avg win +1.90R / avg loss -1.02R, PF 1.12, maxDD 13.9R, net +6.5R, avg hold 98 bars
- **IS:** n=105, win 37.1%, expectancy +0.100R, PF 1.16
- **Walk-forward OOS by year:** 2023: n=34 exp=+0.011, 2024: n=22 exp=+0.168, 2025: n=27 exp=+0.060, 2026: n=5 exp=+0.155
### GER40 — momentum (ROBUST (marginal))
- M15 window 2020–2026 | IS=pre-2023, OOS=2023+
- **OOS:** n=432, 0.48/day, win 36.8%, avg planned R:R 2.00, expectancy +0.057R, avg win +1.91R / avg loss -1.02R, PF 1.09, maxDD 17.5R, net +24.5R, avg hold 13 bars
- **IS:** n=213, win 39.0%, expectancy +0.016R, PF 1.02
- **Walk-forward OOS by year:** 2023: n=65 exp=+0.032, 2024: n=148 exp=+0.117, 2025: n=149 exp=+0.051, 2026: n=70 exp=-0.037
### NAS100 — momentum (fragile-decay)
- M15 window 2020–2026 | IS=pre-2023, OOS=2023+
- **OOS:** n=508, 0.57/day, win 32.9%, avg planned R:R 2.50, expectancy +0.097R, avg win +2.38R / avg loss -1.02R, PF 1.14, maxDD 21.5R, net +49.4R, avg hold 19 bars
- **IS:** n=362, win 34.0%, expectancy +0.139R, PF 1.21
- **Walk-forward OOS by year:** 2023: n=150 exp=-0.019, 2024: n=140 exp=+0.392, 2025: n=148 exp=+0.006, 2026: n=70 exp=-0.051
### JPN225 — breakout_retest (fragile-cost)
- M15 window 2020–2026 | IS=pre-2023, OOS=2023+
- **OOS:** n=938, 1.06/day, win 37.2%, avg planned R:R 2.00, expectancy +0.037R, avg win +1.84R / avg loss -1.03R, PF 1.06, maxDD 44.4R, net +34.7R, avg hold 22 bars
- **IS:** n=575, win 37.4%, expectancy +0.004R, PF 1.01
- **Walk-forward OOS by year:** 2023: n=239 exp=+0.078, 2024: n=270 exp=-0.002, 2025: n=301 exp=-0.038, 2026: n=128 exp=+0.220
