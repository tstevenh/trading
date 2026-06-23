# Exit-Policy Comparison (3 locked strategies)

_Entries fixed (volume identical across policies). IS-select exit, report OOS. Half-spread on entry + each exit leg. No-lookahead trailing._


## SPX500 — mean_reversion  (172 entries, identical across policies)

| exit policy | IS exp | OOS n | OOS win% | OOS avgWin | OOS exp | OOS PF | OOS maxDD | OOS net |
|---|---|---|---|---|---|---|---|---|
| fixed_2.0(base) | -0.027 | 84 | 38% | +1.96 | +0.101 | 1.16 | 9.7 | +8.5 |
| fixed_2.5 | +0.138 | 84 | 38% | +2.46 | +0.291 | 1.45 | 9.2 | +24.5 |
| fixed_3.0 | +0.257 | 84 | 35% | +2.96 | +0.339 | 1.50 | 12.5 | +28.5 |
| scaleout_2_.5_3 | +0.057 | 84 | 38% | +2.06 | +0.139 | 1.22 | 10.5 | +11.7 |
| scaleout_2_.7_2 | -0.029 | 84 | 38% | +2.01 | +0.122 | 1.19 | 10.1 | +10.2 |
| atrtrail_1.5_3 | +0.219 | 84 | 36% | +2.39 | +0.239 | 1.39 | 11.5 | +20.0 |
| atrtrail_1.0_2 | +0.005 | 84 | 42% | +1.41 | +0.027 | 1.05 | 10.4 | +2.3 |
| timestop_2_100 | -0.027 | 84 | 38% | +1.96 | +0.101 | 1.16 | 9.7 | +8.5 |

**IS-selected exit: `fixed_3.0`** → OOS exp +0.339R, win 35%, avgWin +2.96R, PF 1.50, net +28.5R  (baseline fixed_2.0 OOS exp = +0.101R)

## ETHUSD — trend_pullback_plus  (168 entries, identical across policies)

| exit policy | IS exp | OOS n | OOS win% | OOS avgWin | OOS exp | OOS PF | OOS maxDD | OOS net |
|---|---|---|---|---|---|---|---|---|
| fixed_2.0(base) | +0.235 | 99 | 39% | +1.95 | +0.132 | 1.21 | 11.6 | +13.1 |
| fixed_2.5 | +0.351 | 99 | 32% | +2.45 | +0.082 | 1.12 | 15.3 | +8.1 |
| fixed_3.0 | +0.322 | 99 | 30% | +2.95 | +0.163 | 1.22 | 13.4 | +16.1 |
| scaleout_2_.5_3 | +0.203 | 99 | 39% | +1.79 | +0.071 | 1.11 | 11.7 | +7.0 |
| scaleout_2_.7_2 | +0.221 | 99 | 39% | +1.91 | +0.116 | 1.18 | 11.6 | +11.4 |
| atrtrail_1.5_3 | +0.296 | 99 | 49% | +1.37 | +0.149 | 1.28 | 8.2 | +14.8 |
| atrtrail_1.0_2 | +0.311 | 99 | 60% | +1.05 | +0.210 | 1.51 | 6.4 | +20.8 |
| timestop_2_100 | +0.284 | 99 | 47% | +1.29 | +0.112 | 1.22 | 9.1 | +11.1 |

**IS-selected exit: `fixed_2.5`** → OOS exp +0.082R, win 32%, avgWin +2.45R, PF 1.12, net +8.1R  (baseline fixed_2.0 OOS exp = +0.132R)

## EURUSD — trend_pullback_plus  (193 entries, identical across policies)

| exit policy | IS exp | OOS n | OOS win% | OOS avgWin | OOS exp | OOS PF | OOS maxDD | OOS net |
|---|---|---|---|---|---|---|---|---|
| fixed_2.0(base) | +0.094 | 88 | 36% | +1.97 | +0.066 | 1.10 | 16.7 | +5.8 |
| fixed_2.5 | +0.113 | 88 | 27% | +2.47 | -0.070 | 0.91 | 23.8 | -6.2 |
| fixed_3.0 | +0.199 | 88 | 24% | +2.97 | -0.070 | 0.91 | 26.0 | -6.2 |
| scaleout_2_.5_3 | +0.098 | 88 | 36% | +1.92 | +0.046 | 1.07 | 18.9 | +4.0 |
| scaleout_2_.7_2 | +0.090 | 88 | 36% | +1.93 | +0.053 | 1.08 | 17.5 | +4.6 |
| atrtrail_1.5_3 | +0.047 | 88 | 42% | +1.51 | +0.054 | 1.09 | 16.5 | +4.8 |
| atrtrail_1.0_2 | -0.053 | 88 | 53% | +0.95 | +0.031 | 1.06 | 8.5 | +2.7 |
| timestop_2_100 | -0.014 | 88 | 41% | +1.53 | +0.043 | 1.07 | 14.3 | +3.8 |

**IS-selected exit: `fixed_3.0`** → OOS exp -0.070R, win 24%, avgWin +2.97R, PF 0.91, net -6.2R  (baseline fixed_2.0 OOS exp = +0.066R)
