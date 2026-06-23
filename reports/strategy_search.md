# Multi-Archetype Strategy Search — Results

_Select variant on IN-SAMPLE (pre-2023) expectancy; report OUT-OF-SAMPLE (2023+). All 7 pairs pooled, flat 1% risk, spread modeled._


## trend_pullback_plus  (6 variants tried)

| variant | IS n | IS exp | IS PF | OOS n | OOS exp | OOS PF | OOS win% | OOS/day |
|---|---|---|---|---|---|---|---|---|
| tpp_adx18_rsi42 | 203 | -0.052 | 0.92 | 235 | +0.009 | 1.01 | 35% | 0.26 |
| tpp_adx18_rsi48 | 795 | -0.014 | 0.98 | 1093 | -0.083 | 0.88 | 32% | 1.21 |
| tpp_adx25_rsi42 | 158 | -0.086 | 0.88 | 181 | -0.042 | 0.94 | 34% | 0.20 |
| tpp_adx25_rsi48 ⭐ | 519 | -0.006 | 0.99 | 708 | -0.132 | 0.82 | 30% | 0.78 |
| tpp_adx18_rsi45_relaxed | 583 | -0.034 | 0.95 | 767 | -0.080 | 0.89 | 32% | 0.85 |
| tpp_adx25_rsi45_relaxed | 405 | -0.034 | 0.95 | 519 | -0.102 | 0.85 | 31% | 0.58 |

**IS-selected ⭐ `tpp_adx25_rsi48` walk-forward (OOS by year):** 2023: n=199 exp=-0.100, 2024: n=219 exp=-0.105, 2025: n=202 exp=-0.184, 2026: n=88 exp=-0.153

## breakout_retest  (6 variants tried)

| variant | IS n | IS exp | IS PF | OOS n | OOS exp | OOS PF | OOS win% | OOS/day |
|---|---|---|---|---|---|---|---|---|
| breakout_retest_lb20_tol0.5_sm1.0 | 13344 | -0.163 | 0.78 | 18816 | -0.107 | 0.85 | 33% | 20.79 |
| breakout_retest_lb20_tol0.25_sm1.0 | 13343 | -0.163 | 0.78 | 18813 | -0.107 | 0.85 | 33% | 20.79 |
| breakout_retest_lb20_tol0.5_sm1.5 | 10654 | -0.117 | 0.84 | 15030 | -0.078 | 0.89 | 34% | 16.61 |
| breakout_retest_lb50_tol0.5_sm1.0 | 8461 | -0.145 | 0.80 | 12226 | -0.093 | 0.87 | 34% | 13.51 |
| breakout_retest_lb50_tol0.25_sm1.5 | 6962 | -0.085 | 0.88 | 10097 | -0.067 | 0.90 | 34% | 11.16 |
| breakout_retest_lb50_tol0.5_sm1.5 ⭐ | 6961 | -0.084 | 0.88 | 10098 | -0.067 | 0.90 | 34% | 11.16 |

**IS-selected ⭐ `breakout_retest_lb50_tol0.5_sm1.5` walk-forward (OOS by year):** 2023: n=2508 exp=-0.128, 2024: n=3188 exp=-0.069, 2025: n=3062 exp=-0.051, 2026: n=1340 exp=+0.012

## mean_reversion  (6 variants tried)

| variant | IS n | IS exp | IS PF | OOS n | OOS exp | OOS PF | OOS win% | OOS/day |
|---|---|---|---|---|---|---|---|---|
| mr_adx18_rsi25_sm10 | 266 | -0.171 | 0.80 | 354 | -0.114 | 0.87 | 21% | 0.39 |
| mr_adx18_rsi25_sm15 ⭐ | 251 | -0.166 | 0.79 | 330 | -0.100 | 0.87 | 27% | 0.37 |
| mr_adx22_rsi30_sm10 | 3791 | -0.239 | 0.72 | 4392 | -0.184 | 0.78 | 24% | 4.85 |
| mr_adx22_rsi30_sm15 | 2335 | -0.172 | 0.77 | 2909 | -0.144 | 0.81 | 29% | 3.21 |
| mr_adx18_rsi30_sm15 | 839 | -0.181 | 0.76 | 998 | -0.143 | 0.81 | 29% | 1.10 |
| mr_adx22_rsi25_sm10 | 946 | -0.233 | 0.74 | 1242 | -0.082 | 0.90 | 22% | 1.38 |

**IS-selected ⭐ `mr_adx18_rsi25_sm15` walk-forward (OOS by year):** 2023: n=95 exp=-0.300, 2024: n=99 exp=-0.119, 2025: n=90 exp=+0.122, 2026: n=46 exp=-0.077

## momentum  (6 variants tried)

| variant | IS n | IS exp | IS PF | OOS n | OOS exp | OOS PF | OOS win% | OOS/day |
|---|---|---|---|---|---|---|---|---|
| mom_adx30_b20_s15_rr2.0 | 3768 | -0.101 | 0.86 | 5354 | -0.078 | 0.89 | 34% | 5.92 |
| mom_adx25_b20_s15_rr2.0 | 5367 | -0.099 | 0.86 | 7681 | -0.085 | 0.88 | 34% | 8.49 |
| mom_adx30_b50_s15_rr2.0 | 3620 | -0.104 | 0.85 | 5121 | -0.070 | 0.90 | 34% | 5.66 |
| mom_adx30_b20_s10_rr2.0 | 4597 | -0.195 | 0.73 | 6571 | -0.129 | 0.82 | 34% | 7.26 |
| mom_adx30_b20_s15_rr2.5 ⭐ | 3534 | -0.096 | 0.87 | 5023 | -0.065 | 0.91 | 30% | 5.55 |
| mom_adx25_b50_s10_rr2.5 | 5852 | -0.174 | 0.78 | 8409 | -0.126 | 0.83 | 29% | 9.29 |

**IS-selected ⭐ `mom_adx30_b20_s15_rr2.5` walk-forward (OOS by year):** 2023: n=1289 exp=-0.134, 2024: n=1474 exp=-0.022, 2025: n=1504 exp=-0.066, 2026: n=756 exp=-0.028

## Combined portfolio (IS-selected variants with OOS expectancy > 0)

- ❌ trend_pullback_plus `tpp_adx25_rsi48`: OOS exp -0.132R (dropped)
- ❌ breakout_retest `breakout_retest_lb50_tol0.5_sm1.5`: OOS exp -0.067R (dropped)
- ❌ mean_reversion `mr_adx18_rsi25_sm15`: OOS exp -0.100R (dropped)
- ❌ momentum `mom_adx30_b20_s15_rr2.5`: OOS exp -0.065R (dropped)

**No archetype survived OOS with positive expectancy.**

## Multiple-testing note
Total variants evaluated: **24**. With this many tries, treat any single positive OOS result skeptically — demand consistency across walk-forward years and a skeptic review before trust.
