# Exit-Policy Comparison (3 locked strategies)

_Entries fixed (volume identical across policies). IS-select exit, report OOS. Half-spread on entry + each exit leg. No-lookahead trailing._


## SPX500 — mean_reversion  (172 entries, identical across policies)

| exit policy | IS exp | OOS n | OOS win% | OOS avgWin | OOS exp | OOS PF | OOS maxDD | OOS net |
|---|---|---|---|---|---|---|---|---|
| fixed_2.0(base) | -0.027 | 84 | 38% | +1.96 | +0.101 | 1.16 | 9.7 | +8.5 |
| fixed_3.0 | +0.257 | 84 | 35% | +2.96 | +0.339 | 1.50 | 12.5 | +28.5 |
| breakeven@1R_t2 | +0.007 | 84 | 33% | +1.96 | +0.101 | 1.18 | 8.5 | +8.5 |
| breakeven@1R_t3 | +0.121 | 84 | 29% | +2.96 | +0.291 | 1.53 | 10.5 | +24.5 |
| breakeven@1.5_t3 | +0.076 | 84 | 31% | +2.96 | +0.327 | 1.56 | 11.5 | +27.5 |
| partial.5@1R_run3 | -0.112 | 84 | 48% | +1.13 | -0.006 | 0.99 | 10.0 | -0.5 |
| partial.5@2R_run4 | +0.007 | 84 | 38% | +2.33 | +0.244 | 1.38 | 10.5 | +20.5 |
| partial.7@1.5_run3 | -0.062 | 84 | 44% | +1.57 | +0.107 | 1.18 | 10.5 | +9.0 |
| atrtrail_1.0_2 | +0.005 | 84 | 42% | +1.41 | +0.027 | 1.05 | 10.4 | +2.3 |

**IS-selected exit: `fixed_3.0`** → OOS exp +0.339R, win 35%, avgWin +2.96R, PF 1.50, net +28.5R  (baseline fixed_2.0 OOS exp = +0.101R)

## ETHUSD — trend_pullback_plus  (168 entries, identical across policies)

| exit policy | IS exp | OOS n | OOS win% | OOS avgWin | OOS exp | OOS PF | OOS maxDD | OOS net |
|---|---|---|---|---|---|---|---|---|
| fixed_2.0(base) | +0.235 | 99 | 39% | +1.95 | +0.132 | 1.21 | 11.6 | +13.1 |
| fixed_3.0 | +0.322 | 99 | 30% | +2.95 | +0.163 | 1.22 | 13.4 | +16.1 |
| breakeven@1R_t2 | +0.293 | 99 | 31% | +1.95 | +0.183 | 1.43 | 8.8 | +18.1 |
| breakeven@1R_t3 | +0.394 | 99 | 22% | +2.95 | +0.223 | 1.52 | 8.4 | +22.1 |
| breakeven@1.5_t3 | +0.423 | 99 | 25% | +2.95 | +0.203 | 1.37 | 10.7 | +20.1 |
| partial.5@1R_run3 | +0.278 | 99 | 61% | +0.98 | +0.178 | 1.43 | 6.8 | +17.6 |
| partial.5@2R_run4 | +0.293 | 99 | 39% | +1.62 | +0.001 | 1.00 | 16.3 | +0.1 |
| partial.7@1.5_run3 | +0.304 | 99 | 49% | +1.44 | +0.183 | 1.35 | 7.2 | +18.1 |
| atrtrail_1.0_2 | +0.311 | 99 | 60% | +1.05 | +0.210 | 1.51 | 6.4 | +20.8 |

**IS-selected exit: `breakeven@1.5_t3`** → OOS exp +0.203R, win 25%, avgWin +2.95R, PF 1.37, net +20.1R  (baseline fixed_2.0 OOS exp = +0.132R)

## EURUSD — trend_pullback_plus  (193 entries, identical across policies)

| exit policy | IS exp | OOS n | OOS win% | OOS avgWin | OOS exp | OOS PF | OOS maxDD | OOS net |
|---|---|---|---|---|---|---|---|---|
| fixed_2.0(base) | +0.094 | 88 | 36% | +1.97 | +0.066 | 1.10 | 16.7 | +5.8 |
| fixed_3.0 | +0.199 | 88 | 24% | +2.97 | -0.070 | 0.91 | 26.0 | -6.2 |
| breakeven@1R_t2 | -0.049 | 88 | 25% | +1.97 | +0.009 | 1.02 | 14.5 | +0.8 |
| breakeven@1R_t3 | +0.047 | 88 | 14% | +2.97 | -0.082 | 0.83 | 20.5 | -7.2 |
| breakeven@1.5_t3 | +0.142 | 88 | 16% | +2.97 | -0.104 | 0.82 | 21.4 | -9.2 |
| partial.5@1R_run3 | -0.034 | 88 | 53% | +0.76 | -0.070 | 0.85 | 14.3 | -6.2 |
| partial.5@2R_run4 | +0.085 | 88 | 36% | +1.78 | -0.002 | 1.00 | 19.4 | -0.2 |
| partial.7@1.5_run3 | +0.053 | 88 | 44% | +1.32 | +0.017 | 1.03 | 11.4 | +1.5 |
| atrtrail_1.0_2 | -0.053 | 88 | 53% | +0.95 | +0.031 | 1.06 | 8.5 | +2.7 |

**IS-selected exit: `fixed_3.0`** → OOS exp -0.070R, win 24%, avgWin +2.97R, PF 0.91, net -6.2R  (baseline fixed_2.0 OOS exp = +0.066R)
