# Step 0 — Daily Instrument Characterization

_Exploratory analysis to ground the strategy hypothesis. Data: Dukascopy bid, daily._

## XAU/USD (Gold)

- **Span:** 2010-01-01 → 2026-06-19  (5125 daily bars)
- **Price range:** 1052.799 → 5512.255  (start 1095.997, end 4154.335)
- **Buy & hold total return:** 279.0%
- **Daily return:** mean 0.0%, std 0.9%, skew -0.63, kurtosis 8.8

**Trend vs range character**
- ADX>25 (trending): 44.6% of days | ADX<20 (ranging): 34.6% of days
- Days above 200-SMA: 60.4%  → directional bias
- Mean efficiency ratio (10d): 0.35  (closer to 1 = cleaner trends)
- Daily log-return autocorrelation: lag1=-0.003, lag2=-0.022, lag3=-0.015, lag5=+0.006, lag10=+0.011
  → note: near-zero 1-day autocorrelation is NORMAL for liquid markets and does
    NOT mean trend-following fails. The trend lives in the multi-day swing/200-SMA
    structure below, not in predicting tomorrow from today.
  → macro trend regime (50-SMA > 200-SMA): 61.1% of days

**Volatility (stop/target sizing)**
- ATR(14) now: 104.462  (2.5% of price)
- ATR% percentiles: p10=0.8%, median=1.2%, p90=1.8%
- Daily range %: median 1.1%, p90 2.2%

**Swing structure (k=3 fractal pivots)**
- Avg swing duration: 6.9 bars (median 5), so a 2-3 day hold captures a typical leg: YES
- Avg swing amplitude: 3.5× ATR (median 2.8×)
- Swings ≥ 2× ATR: 76.2%  → these offer room for ≥2:1 R:R targets

## EUR/USD

- **Span:** 2010-01-01 → 2026-06-19  (5151 daily bars)
- **Price range:** 0.960 → 1.484  (start 1.433, end 1.147)
- **Buy & hold total return:** -20.0%
- **Daily return:** mean -0.0%, std 0.5%, skew 0.07, kurtosis 3.0

**Trend vs range character**
- ADX>25 (trending): 42.6% of days | ADX<20 (ranging): 36.5% of days
- Days above 200-SMA: 46.7%  → directional bias
- Mean efficiency ratio (10d): 0.33  (closer to 1 = cleaner trends)
- Daily log-return autocorrelation: lag1=-0.014, lag2=+0.009, lag3=-0.025, lag5=-0.009, lag10=+0.008
  → note: near-zero 1-day autocorrelation is NORMAL for liquid markets and does
    NOT mean trend-following fails. The trend lives in the multi-day swing/200-SMA
    structure below, not in predicting tomorrow from today.
  → macro trend regime (50-SMA > 200-SMA): 45.3% of days

**Volatility (stop/target sizing)**
- ATR(14) now: 0.006  (0.5% of price)
- ATR% percentiles: p10=0.4%, median=0.6%, p90=1.0%
- Daily range %: median 0.6%, p90 1.2%

**Swing structure (k=3 fractal pivots)**
- Avg swing duration: 6.4 bars (median 5), so a 2-3 day hold captures a typical leg: YES
- Avg swing amplitude: 3.3× ATR (median 2.8×)
- Swings ≥ 2× ATR: 77.3%  → these offer room for ≥2:1 R:R targets
