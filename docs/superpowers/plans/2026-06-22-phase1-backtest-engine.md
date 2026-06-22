# Phase 1 — Backtest Engine + Swing Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, no-lookahead backtest engine that runs the trend-pullback swing strategy over 7 instruments of historical data and produces a validation report (expectancy, win rate, R:R, drawdown) splitting in-sample vs out-of-sample — proving whether the edge is real before any live work.

**Architecture:** A Python package `swingbot/` of pure, independently-testable units: indicators → multi-timeframe as-of alignment (the no-lookahead core) → deterministic gates → signal builder → event-driven backtest with cost model → metrics → grading analysis. A runner CLI ties them together over the universe and emits a markdown report. The same gate/strategy code is designed to later run live unchanged.

**Tech Stack:** Python 3.14, pandas 3.0.3, numpy 2.5.0, pytest. Env via `uv` (`.venv` already exists). Data already downloaded to `data/raw/*.csv` (Dukascopy bid, epoch-ms timestamps = bar OPEN times, columns `timestamp,open,high,low,close,volume`).

## Global Constraints

- **No lookahead, ever.** At entry-timeframe (M15) bar time `t`, higher-timeframe (H1, Daily) features may reference ONLY bars that have fully CLOSED at or before `t`. This is enforced via close-time alignment + `merge_asof(direction="backward")`. Every signal must be reproducible bar-for-bar.
- **Signals are deterministic code.** No LLM, no randomness in signal logic.
- **Universe (7):** `XAUUSD, USDJPY, EURUSD, USDCHF, NZDUSD, GBPUSD, USDCAD` (AUD/USD dropped).
- **Timeframes (swing profile):** Daily = bias, H1 = pullback zone, M15 = entry trigger.
- **R:R:** stop = pullback swing low (long) / high (short), floored at `entry ∓ 1.5×ATR`; TP at next structural level only if it yields ≥ 2.0R, else reject. No trailing — fixed TP.
- **Risk for base backtest:** flat 1% per trade (tiered risk is analyzed, not applied, until tiers prove out — Task 9).
- **Costs modeled:** per-instrument spread applied on entry AND exit. Conservative spreads (price units): XAUUSD 0.30, USDJPY 0.012, EURUSD 0.00008, GBPUSD 0.00012, USDCHF 0.00010, USDCAD 0.00012, NZDUSD 0.00012.
- **Split:** in-sample = bars before 2023-01-01; out-of-sample = 2023-01-01 onward.
- **Session gate:** entries only 07:00–16:00 UTC. **News gate:** out of scope for Phase 1 backtest (no historical calendar) — implemented as an injectable hook defaulting to allow; its effect is evaluated in a later phase. Documented, not silently skipped.
- All indicators Wilder-smoothed where applicable; reuse the math already in `scripts/indicators.py`.

---

### Task 1: Project scaffold + indicators module

**Files:**
- Create: `swingbot/__init__.py` (empty)
- Create: `swingbot/indicators.py`
- Create: `tests/test_indicators.py`
- Create: `conftest.py` (repo root — puts repo root on sys.path)
- Create: `.gitignore`

**Interfaces:**
- Produces: `load_csv(path, weekdays_only=False) -> pd.DataFrame`; `ema(s, n)`, `sma(s, n)`, `rsi(close, n=14)`, `atr(df, n=14)`, `adx(df, n=14) -> DataFrame[plus_di,minus_di,adx]`, `true_range(df)`, `rma(s, n)`, `swing_pivots(df, k=3) -> list[(idx,'H'|'L',price)]`. All operate on a DataFrame indexed by UTC datetime with columns `open,high,low,close,volume`.

- [ ] **Step 1: Init project + deps** (git repo, branch, and .gitignore already set up by the controller)

```bash
cd /Users/tsth/Coding/trading
uv pip install --python .venv pytest
mkdir -p swingbot tests
: > swingbot/__init__.py
```

- [ ] **Step 2: conftest.py so `import swingbot` works from tests**

```python
# conftest.py
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
```

- [ ] **Step 3: Write failing tests for indicators**

```python
# tests/test_indicators.py
import numpy as np
import pandas as pd
import pytest
from swingbot import indicators as ind


def _df(prices):
    idx = pd.date_range("2024-01-01", periods=len(prices), freq="D", tz="UTC")
    p = pd.Series(prices, index=idx, dtype=float)
    return pd.DataFrame({"open": p, "high": p + 1, "low": p - 1, "close": p,
                         "volume": 1.0}, index=idx)


def test_sma_basic():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    assert ind.sma(s, 2).iloc[-1] == pytest.approx(4.5)


def test_ema_responds_faster_than_sma():
    s = pd.Series(list(range(1, 51)), dtype=float)
    # rising series: EMA(n) closer to latest value than SMA(n)
    assert ind.ema(s, 10).iloc[-1] > ind.sma(s, 10).iloc[-1]


def test_rsi_all_up_is_100():
    close = pd.Series(np.arange(1, 30, dtype=float))
    assert ind.rsi(close, 14).iloc[-1] == pytest.approx(100.0, abs=1e-6)


def test_rsi_all_down_is_0():
    close = pd.Series(np.arange(30, 1, -1, dtype=float))
    assert ind.rsi(close, 14).iloc[-1] == pytest.approx(0.0, abs=1e-6)


def test_atr_positive_and_tracks_range():
    df = _df([10, 12, 11, 13, 12, 14, 13])
    a = ind.atr(df, 3)
    assert a.dropna().gt(0).all()


def test_adx_columns():
    df = _df(list(range(1, 60)))
    out = ind.adx(df, 14)
    assert set(["plus_di", "minus_di", "adx"]).issubset(out.columns)
    assert out["adx"].dropna().between(0, 100).all()


def test_swing_pivots_finds_alternating_extremes():
    df = _df([1, 2, 5, 2, 1, 2, 6, 2, 1])  # peak at idx2 and idx6
    piv = ind.swing_pivots(df, k=2)
    types = [p[1] for p in piv]
    # alternating H/L, no two same in a row
    assert all(a != b for a, b in zip(types, types[1:]))
```

- [ ] **Step 4: Run tests, verify they fail**

Run: `.venv/bin/pytest tests/test_indicators.py -v`
Expected: FAIL (`ModuleNotFoundError` / functions missing).

- [ ] **Step 5: Implement `swingbot/indicators.py`**

Port the existing functions from `scripts/indicators.py` (load_csv, rma, true_range, atr, adx, swing_pivots) verbatim, and ADD `sma`, `ema`, `rsi`:

```python
# swingbot/indicators.py  — append these to the ported functions
def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = rma(gain, n)
    avg_loss = rma(loss, n)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    out = out.where(avg_loss != 0, 100.0)   # all-up → 100
    out = out.where(avg_gain != 0, 0.0)      # all-down → 0
    return out
```

(Copy `load_csv, rma, true_range, atr, adx, swing_pivots` from `scripts/indicators.py` into this file so `swingbot` is self-contained — do not import from `scripts/`.)

- [ ] **Step 6: Run tests, verify pass**

Run: `.venv/bin/pytest tests/test_indicators.py -v`
Expected: PASS (7 passed).

- [ ] **Step 7: Commit**

```bash
git add swingbot/ tests/test_indicators.py conftest.py .gitignore
git commit -m "feat: swingbot indicators module (ema/sma/rsi/atr/adx/swings)"
```

---

### Task 2: Multi-timeframe as-of alignment (no-lookahead core)

**Files:**
- Create: `swingbot/align.py`
- Create: `tests/test_align.py`

**Interfaces:**
- Consumes: indicators from Task 1.
- Produces: `tf_close_index(df, freq) -> pd.DataFrame` (reindexes a TF frame by bar CLOSE time = open + freq); `align_htf(base: pd.DataFrame, htf: pd.DataFrame, prefix: str) -> pd.DataFrame` (adds htf columns to `base`'s index via `merge_asof` backward on close times, so each base row sees only CLOSED htf bars). `FREQ = {"m15": "15min", "h1": "1h", "d1": "1D"}`.

- [ ] **Step 1: Write the failing no-lookahead test**

```python
# tests/test_align.py
import pandas as pd
from swingbot.align import tf_close_index, align_htf


def _frame(start, periods, freq, val0):
    idx = pd.date_range(start, periods=periods, freq=freq, tz="UTC")
    v = pd.Series(range(val0, val0 + periods), index=idx, dtype=float)
    return pd.DataFrame({"open": v, "high": v, "low": v, "close": v, "volume": 1.0},
                        index=idx)


def test_close_index_shifts_by_one_freq():
    d = _frame("2024-01-01", 3, "1D", 0)
    c = tf_close_index(d, "1D")
    # daily bar opened 2024-01-01 closes 2024-01-02 00:00
    assert c.index[0] == pd.Timestamp("2024-01-02", tz="UTC")


def test_no_lookahead_daily_into_m15():
    # daily closes (open+1D): Jan1 bar -> close Jan2 00:00, Jan2 bar -> close Jan3 00:00
    d = _frame("2024-01-01", 3, "1D", 100)   # closes: 100,101,102 for Jan1,2,3 bars
    m = _frame("2024-01-02 00:00", 96, "15min", 0)  # all of Jan 2 (and into Jan 3)
    out = align_htf(m, d, prefix="d1")
    # During Jan 2 session, the only CLOSED daily bar is Jan 1's (close value 100).
    jan2 = out.loc["2024-01-02 00:00":"2024-01-02 23:45"]
    assert (jan2["d1_close"] == 100).all(), "must use prior completed daily, not today's"
    # Once Jan 3 starts, Jan 2's bar (101) has closed.
    assert out.loc["2024-01-03 00:00"]["d1_close"] == 101
```

- [ ] **Step 2: Run test, verify it fails**

Run: `.venv/bin/pytest tests/test_align.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement `swingbot/align.py`**

```python
# swingbot/align.py
import pandas as pd

FREQ = {"m15": "15min", "h1": "1h", "d1": "1D"}


def tf_close_index(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Reindex a timeframe frame by bar CLOSE time (= open timestamp + 1 period).
    Dukascopy timestamps are bar OPEN times; a bar's data is only known at close."""
    out = df.copy()
    out.index = out.index + pd.Timedelta(FREQ.get(freq, freq))
    out.index.name = "close_time"
    return out


def align_htf(base: pd.DataFrame, htf: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Attach higher-timeframe columns to `base` rows using only CLOSED htf bars.
    `htf` must already be indexed by CLOSE time (via tf_close_index)."""
    left = base.sort_index().reset_index()
    left_time = left.columns[0]
    right = htf.sort_index().reset_index().rename(
        columns={"close_time": "_c", "dt": "_c", "index": "_c"})
    right = right.rename(columns={c: f"{prefix}_{c}" for c in htf.columns})
    merged = pd.merge_asof(
        left, right, left_on=left_time, right_on="_c", direction="backward")
    merged = merged.set_index(left_time)
    merged = merged.drop(columns=["_c"])
    return merged
```

- [ ] **Step 4: Run test, verify pass**

Run: `.venv/bin/pytest tests/test_align.py -v`
Expected: PASS (3 passed). The `test_no_lookahead_daily_into_m15` passing is the critical correctness guarantee.

- [ ] **Step 5: Commit**

```bash
git add swingbot/align.py tests/test_align.py
git commit -m "feat: no-lookahead multi-timeframe as-of alignment"
```

---

### Task 3: Strategy gates

**Files:**
- Create: `swingbot/gates.py`
- Create: `tests/test_gates.py`

**Interfaces:**
- Consumes: aligned per-bar row with columns: `close,high,low` (M15) plus `d1_close,d1_sma200,d1_sma50` (daily bias), `h1_ema20,h1_ema50,h1_rsi` (pullback), `m15_ema20,m15_rsi,m15_rsi_prev` (trigger), `atr` (M15 ATR), and index timestamp.
- Produces: pure boolean functions `trend_bias(row, relaxed=False) -> int` (+1 long / -1 short / 0 none); `pullback_ok(row, bias) -> bool`; `trigger_ok(row, bias) -> bool`; `session_ok(ts) -> bool`. `SESSION_START_H, SESSION_END_H = 7, 16`.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_gates.py
import pandas as pd
from swingbot import gates


def test_trend_bias_long_short_none():
    long_row = {"d1_close": 110, "d1_sma200": 100, "d1_sma50": 105}
    short_row = {"d1_close": 90, "d1_sma200": 100, "d1_sma50": 95}
    none_row = {"d1_close": 101, "d1_sma200": 100, "d1_sma50": 99}  # close>200 but 50<200
    assert gates.trend_bias(long_row) == 1
    assert gates.trend_bias(short_row) == -1
    assert gates.trend_bias(none_row) == 0


def test_trend_bias_relaxed_uses_only_50_vs_200():
    row = {"d1_close": 99, "d1_sma200": 100, "d1_sma50": 101}  # 50>200
    assert gates.trend_bias(row, relaxed=True) == 1


def test_pullback_long_requires_zone_and_low_rsi():
    bias = 1
    in_zone = {"h1_ema20": 100, "h1_ema50": 102, "low": 101, "h1_rsi": 40}
    assert gates.pullback_ok(in_zone, bias) is True
    high_rsi = {"h1_ema20": 100, "h1_ema50": 102, "low": 101, "h1_rsi": 60}
    assert gates.pullback_ok(high_rsi, bias) is False


def test_trigger_long_requires_close_above_ema_and_rsi_turning_up():
    bias = 1
    good = {"close": 101, "m15_ema20": 100, "m15_rsi": 48, "m15_rsi_prev": 44}
    assert gates.trigger_ok(good, bias) is True
    no_turn = {"close": 101, "m15_ema20": 100, "m15_rsi": 42, "m15_rsi_prev": 44}
    assert gates.trigger_ok(no_turn, bias) is False


def test_session_ok():
    assert gates.session_ok(pd.Timestamp("2024-01-02 13:00", tz="UTC")) is True
    assert gates.session_ok(pd.Timestamp("2024-01-02 03:00", tz="UTC")) is False
```

- [ ] **Step 2: Run tests, verify fail**

Run: `.venv/bin/pytest tests/test_gates.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement `swingbot/gates.py`**

```python
# swingbot/gates.py
SESSION_START_H, SESSION_END_H = 7, 16
PULLBACK_RSI_LONG, PULLBACK_RSI_SHORT = 45, 55


def trend_bias(row, relaxed: bool = False) -> int:
    c, s50, s200 = row["d1_close"], row["d1_sma50"], row["d1_sma200"]
    if any(v != v for v in (c, s50, s200)):  # NaN guard
        return 0
    if relaxed:
        return 1 if s50 > s200 else (-1 if s50 < s200 else 0)
    if c > s200 and s50 > s200:
        return 1
    if c < s200 and s50 < s200:
        return -1
    return 0


def _zone(row):
    lo = min(row["h1_ema20"], row["h1_ema50"])
    hi = max(row["h1_ema20"], row["h1_ema50"])
    return lo, hi


def pullback_ok(row, bias: int) -> bool:
    lo, hi = _zone(row)
    if bias == 1:
        return (row["low"] <= hi) and (row["h1_rsi"] < PULLBACK_RSI_LONG)
    if bias == -1:
        return (row["high"] >= lo) and (row["h1_rsi"] > PULLBACK_RSI_SHORT)
    return False


def trigger_ok(row, bias: int) -> bool:
    if bias == 1:
        return (row["close"] > row["m15_ema20"]) and (row["m15_rsi"] > row["m15_rsi_prev"])
    if bias == -1:
        return (row["close"] < row["m15_ema20"]) and (row["m15_rsi"] < row["m15_rsi_prev"])
    return False


def session_ok(ts) -> bool:
    return SESSION_START_H <= ts.hour < SESSION_END_H
```

- [ ] **Step 4: Run tests, verify pass**

Run: `.venv/bin/pytest tests/test_gates.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add swingbot/gates.py tests/test_gates.py
git commit -m "feat: deterministic strategy gates (trend/pullback/trigger/session)"
```

---

### Task 4: Signal builder (R:R, stop, reachable TP)

**Files:**
- Create: `swingbot/strategy.py`
- Create: `tests/test_strategy.py`

**Interfaces:**
- Consumes: gates (Task 3), `swing_pivots` (Task 1).
- Produces: `@dataclass Signal(ts, side:int, entry:float, stop:float, tp:float, rr:float, atr:float)`; `build_signal(row, bias, recent_pivots, atr_floor_mult=1.5, min_rr=2.0) -> Signal | None`. Stop = nearest opposite swing pivot beyond entry, floored at `entry ∓ atr_floor_mult*atr`. TP = next structural pivot in trade direction; signal returned only if `rr >= min_rr`, else None.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_strategy.py
from swingbot.strategy import build_signal, Signal


def test_long_signal_meets_2to1():
    row = {"close": 100.0, "atr": 1.0}
    # nearest swing low below = 98 (risk 2), next swing high above = 105 (reward 5) -> rr 2.5
    sig = build_signal(row, bias=1, recent_pivots=[("L", 98.0), ("H", 105.0)])
    assert isinstance(sig, Signal)
    assert sig.side == 1 and sig.entry == 100.0
    assert sig.stop == 98.0 and sig.tp == 105.0
    assert round(sig.rr, 2) == 2.5


def test_long_rejected_when_rr_below_min():
    row = {"close": 100.0, "atr": 1.0}
    # swing low 98 (risk 2), swing high 103 (reward 3) -> rr 1.5 < 2.0
    sig = build_signal(row, bias=1, recent_pivots=[("L", 98.0), ("H", 103.0)])
    assert sig is None


def test_atr_floor_widens_too_tight_stop():
    row = {"close": 100.0, "atr": 2.0}
    # swing low 99.5 is only 0.5 away; floor = 100 - 1.5*2 = 97 -> risk 3
    sig = build_signal(row, bias=1, recent_pivots=[("L", 99.5), ("H", 110.0)])
    assert sig.stop == 97.0
```

- [ ] **Step 2: Run tests, verify fail**

Run: `.venv/bin/pytest tests/test_strategy.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement `swingbot/strategy.py`**

```python
# swingbot/strategy.py
from dataclasses import dataclass


@dataclass
class Signal:
    ts: object
    side: int
    entry: float
    stop: float
    tp: float
    rr: float
    atr: float


def build_signal(row, bias, recent_pivots, atr_floor_mult=1.5, min_rr=2.0,
                 ts=None):
    entry, atr = row["close"], row["atr"]
    lows = [p for t, p in recent_pivots if t == "L"]
    highs = [p for t, p in recent_pivots if t == "H"]
    if bias == 1:
        cand = [p for p in lows if p < entry]
        if not cand:
            return None
        struct_stop = max(cand)                      # nearest swing low below
        stop = min(struct_stop, entry - atr_floor_mult * atr)
        tps = [p for p in highs if p > entry]
        if not tps:
            return None
        tp = min(tps)                                # nearest structural high
        risk, reward = entry - stop, tp - entry
    elif bias == -1:
        cand = [p for p in highs if p > entry]
        if not cand:
            return None
        struct_stop = min(cand)
        stop = max(struct_stop, entry + atr_floor_mult * atr)
        tps = [p for p in lows if p < entry]
        if not tps:
            return None
        tp = max(tps)
        risk, reward = stop - entry, entry - tp
    else:
        return None
    if risk <= 0:
        return None
    rr = reward / risk
    if rr < min_rr:
        return None
    return Signal(ts=ts, side=bias, entry=entry, stop=stop, tp=tp, rr=rr, atr=atr)
```

- [ ] **Step 4: Run tests, verify pass**

Run: `.venv/bin/pytest tests/test_strategy.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add swingbot/strategy.py tests/test_strategy.py
git commit -m "feat: signal builder with ATR-floored stop and reachable >=2R TP"
```

---

### Task 5: Feature assembly per instrument

**Files:**
- Create: `swingbot/features.py`
- Create: `tests/test_features.py`

**Interfaces:**
- Consumes: indicators (T1), align (T2).
- Produces: `build_features(m15, h1, d1) -> pd.DataFrame` — an M15-indexed frame with every column the gates/strategy need: `open,high,low,close,atr,m15_ema20,m15_rsi,m15_rsi_prev,h1_ema20,h1_ema50,h1_rsi,d1_close,d1_sma50,d1_sma200`. All HTF columns are no-lookahead (close-time aligned). Indicators computed on each TF natively, THEN aligned.

- [ ] **Step 1: Write failing test (smoke + no-NaN-after-warmup + column presence)**

```python
# tests/test_features.py
import pandas as pd
from swingbot.indicators import load_csv
from swingbot.features import build_features


def test_features_have_required_columns_and_align():
    m15 = load_csv("data/raw/xauusd_m15.csv")
    h1 = load_csv("data/raw/xauusd_h1.csv")
    d1 = load_csv("data/raw/xauusd_d1.csv")
    feats = build_features(m15, h1, d1)
    needed = {"open", "high", "low", "close", "atr", "m15_ema20", "m15_rsi",
              "m15_rsi_prev", "h1_ema20", "h1_ema50", "h1_rsi",
              "d1_close", "d1_sma50", "d1_sma200"}
    assert needed.issubset(feats.columns)
    # after warmup there should be fully-populated rows
    tail = feats.dropna(subset=list(needed))
    assert len(tail) > 1000
```

- [ ] **Step 2: Run test, verify fails**

Run: `.venv/bin/pytest tests/test_features.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement `swingbot/features.py`**

```python
# swingbot/features.py
from swingbot import indicators as ind
from swingbot.align import tf_close_index, align_htf


def build_features(m15, h1, d1):
    m = m15.copy()
    m["atr"] = ind.atr(m, 14)
    m["m15_ema20"] = ind.ema(m["close"], 20)
    m["m15_rsi"] = ind.rsi(m["close"], 14)
    m["m15_rsi_prev"] = m["m15_rsi"].shift(1)

    h = h1.copy()
    h["h1_ema20"] = ind.ema(h["close"], 20)
    h["h1_ema50"] = ind.ema(h["close"], 50)
    h["h1_rsi"] = ind.rsi(h["close"], 14)
    h_feat = tf_close_index(h[["h1_ema20", "h1_ema50", "h1_rsi"]], "h1")

    d = d1.copy()
    d["d1_close"] = d["close"]
    d["d1_sma50"] = ind.sma(d["close"], 50)
    d["d1_sma200"] = ind.sma(d["close"], 200)
    d_feat = tf_close_index(d[["d1_close", "d1_sma50", "d1_sma200"]], "d1")

    out = align_htf(m, h_feat, prefix="")          # h1_* already prefixed
    out = align_htf(out, d_feat, prefix="")         # d1_* already prefixed
    return out
```

Note: because the H1/D1 helper columns are already named `h1_*`/`d1_*`, pass `prefix=""` and strip the leading underscore the aligner would add by ensuring `align_htf` joins on already-prefixed names. If `align_htf`'s prefixing double-prefixes, adjust `align_htf` to skip prefixing when `prefix==""`. Add this guard to `align.py`:

```python
# in align_htf, replace the rename line with:
if prefix:
    right = right.rename(columns={c: f"{prefix}_{c}" for c in htf.columns})
```

- [ ] **Step 4: Run test, verify pass**

Run: `.venv/bin/pytest tests/test_features.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add swingbot/features.py tests/test_features.py swingbot/align.py
git commit -m "feat: per-instrument feature assembly (no-lookahead aligned)"
```

---

### Task 6: Cost model + event-driven backtest engine

**Files:**
- Create: `swingbot/costs.py`
- Create: `swingbot/backtest.py`
- Create: `tests/test_backtest.py`

**Interfaces:**
- Consumes: features (T5), gates (T3), strategy (T4), `swing_pivots` (T1).
- Produces: `SPREADS: dict[str,float]`; `@dataclass Trade(instrument, side, entry_ts, entry, stop, tp, exit_ts, exit, rr, outcome_r, bars_held, reason)`; `run_backtest(instrument, feats, m15_raw, spread, relaxed_trend=False, pivot_lookback=20, risk_pct=1.0) -> list[Trade]`. Engine iterates M15 bars: evaluate gates on completed bar `i`; if a signal builds, enter at bar `i+1` open (plus half-spread); then walk forward bar-by-bar applying stop/TP (stop checked first = conservative; exit price includes spread). One open position per instrument. `outcome_r` = realized R multiple net of costs.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_backtest.py
import numpy as np
import pandas as pd
from swingbot.backtest import run_backtest, Trade


def _synth_uptrend_pullback():
    """Construct a tiny M15 frame that forces exactly one long setup then a win."""
    idx = pd.date_range("2024-03-04 12:00", periods=40, freq="15min", tz="UTC")
    # price: dip then rally; columns pre-baked so gates fire on the dip-recovery bar
    close = np.concatenate([np.linspace(100, 98, 10),   # pullback
                            np.linspace(98.1, 110, 30)])  # resume up
    df = pd.DataFrame(index=idx)
    df["open"] = close
    df["high"] = close + 0.2
    df["low"] = close - 0.2
    df["close"] = close
    df["atr"] = 1.0
    df["m15_ema20"] = pd.Series(close, index=idx).ewm(span=20, adjust=False).mean()
    df["m15_rsi"] = 50.0
    df["m15_rsi_prev"] = 49.0
    df["h1_ema20"] = 99.0
    df["h1_ema50"] = 101.0
    df["h1_rsi"] = 40.0          # pullback condition satisfied
    df["d1_close"] = 110.0
    df["d1_sma50"] = 105.0
    df["d1_sma200"] = 100.0      # long bias
    return df


def test_engine_produces_a_trade_with_R_outcome():
    feats = _synth_uptrend_pullback()
    trades = run_backtest("XAUUSD", feats, feats, spread=0.30,
                          pivot_lookback=10, risk_pct=1.0)
    assert len(trades) >= 1
    t = trades[0]
    assert isinstance(t, Trade)
    assert t.side == 1
    assert t.reason in ("tp", "stop", "eod")
    # win target was reachable in the rally -> expect positive R (net of spread)
    assert t.outcome_r > 0


def test_no_two_open_positions_same_instrument():
    feats = _synth_uptrend_pullback()
    trades = run_backtest("XAUUSD", feats, feats, spread=0.30, pivot_lookback=10)
    # entries must not overlap in time
    for a, b in zip(trades, trades[1:]):
        assert a.exit_ts <= b.entry_ts
```

- [ ] **Step 2: Run tests, verify fail**

Run: `.venv/bin/pytest tests/test_backtest.py -v`
Expected: FAIL (modules missing).

- [ ] **Step 3: Implement `swingbot/costs.py`**

```python
# swingbot/costs.py
SPREADS = {            # conservative spread in PRICE units (round-turn applied half each side)
    "XAUUSD": 0.30, "USDJPY": 0.012, "EURUSD": 0.00008, "GBPUSD": 0.00012,
    "USDCHF": 0.00010, "USDCAD": 0.00012, "NZDUSD": 0.00012,
}
```

- [ ] **Step 4: Implement `swingbot/backtest.py`**

```python
# swingbot/backtest.py
from dataclasses import dataclass
import numpy as np
from swingbot import gates
from swingbot.strategy import build_signal


@dataclass
class Trade:
    instrument: str
    side: int
    entry_ts: object
    entry: float
    stop: float
    tp: float
    exit_ts: object
    exit: float
    rr: float
    outcome_r: float
    bars_held: int
    reason: str


def _recent_pivots(highs, lows, i, lookback, k=2):
    """Fractal pivots within [i-lookback, i] on the entry TF (completed bars only)."""
    piv = []
    lo_i = max(k, i - lookback)
    for j in range(lo_i, i - k + 1):
        wh, wl = highs[j - k:j + k + 1], lows[j - k:j + k + 1]
        if highs[j] == wh.max() and wh.argmax() == k:
            piv.append(("H", highs[j]))
        elif lows[j] == wl.min() and wl.argmin() == k:
            piv.append(("L", lows[j]))
    return piv


def run_backtest(instrument, feats, m15_raw, spread, relaxed_trend=False,
                 pivot_lookback=20, risk_pct=1.0, min_rr=2.0):
    f = feats.dropna(subset=["atr", "m15_ema20", "m15_rsi", "m15_rsi_prev",
                             "h1_ema20", "h1_ema50", "h1_rsi",
                             "d1_close", "d1_sma50", "d1_sma200"]).copy()
    ts = f.index.to_numpy()
    highs, lows = f["high"].to_numpy(), f["low"].to_numpy()
    opens, closes = f["open"].to_numpy(), f["close"].to_numpy()
    rows = f.to_dict("records")
    half = spread / 2.0
    trades, i, n = [], 1, len(f)

    while i < n - 1:
        row, t = rows[i], f.index[i]
        bias = gates.trend_bias(row, relaxed=relaxed_trend)
        if (bias != 0 and gates.session_ok(t)
                and gates.pullback_ok(row, bias)
                and gates.trigger_ok(row, bias)):
            piv = _recent_pivots(highs, lows, i, pivot_lookback)
            sig = build_signal(row, bias, piv, min_rr=min_rr, ts=t)
            if sig is not None:
                # enter next bar open + half-spread against us
                entry = opens[i + 1] + half * sig.side
                stop, tp, side = sig.stop, sig.tp, sig.side
                risk = abs(entry - stop)
                exit_px, reason, j = None, None, i + 1
                while j < n:
                    hi, lo = highs[j], lows[j]
                    if side == 1:
                        if lo <= stop:               # stop checked first (conservative)
                            exit_px, reason = stop - half, "stop"; break
                        if hi >= tp:
                            exit_px, reason = tp - half, "tp"; break
                    else:
                        if hi >= stop:
                            exit_px, reason = stop + half, "stop"; break
                        if lo <= tp:
                            exit_px, reason = tp + half, "tp"; break
                    j += 1
                if exit_px is None:
                    exit_px, reason, j = closes[n - 1], "eod", n - 1
                pnl = (exit_px - entry) * side
                outcome_r = pnl / risk if risk > 0 else 0.0
                trades.append(Trade(instrument, side, t, entry, stop, tp,
                                    f.index[j], exit_px, sig.rr, outcome_r,
                                    j - (i + 1), reason))
                i = j + 1                            # no overlapping positions
                continue
        i += 1
    return trades
```

- [ ] **Step 5: Run tests, verify pass**

Run: `.venv/bin/pytest tests/test_backtest.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add swingbot/costs.py swingbot/backtest.py tests/test_backtest.py
git commit -m "feat: event-driven backtest engine with spread costs, no overlap"
```

---

### Task 7: Performance metrics

**Files:**
- Create: `swingbot/metrics.py`
- Create: `tests/test_metrics.py`

**Interfaces:**
- Consumes: `Trade` list (T6).
- Produces: `summarize(trades, risk_pct=1.0) -> dict` with keys `n, win_rate, avg_r, expectancy_r, profit_factor, max_drawdown_r, sharpe, equity_final_r`. Equity is built in R-multiples (each trade risks `risk_pct`, contributes `outcome_r*risk_pct`); drawdown and Sharpe computed on the R-equity curve.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_metrics.py
import pytest
from swingbot.metrics import summarize
from swingbot.backtest import Trade


def _t(r):
    return Trade("X", 1, None, 0, 0, 0, None, 0, 2.0, r, 1, "tp")


def test_summarize_basic():
    trades = [_t(2.0), _t(-1.0), _t(2.0), _t(-1.0)]  # 50% win, 2:1
    s = summarize(trades, risk_pct=1.0)
    assert s["n"] == 4
    assert s["win_rate"] == pytest.approx(0.5)
    assert s["avg_r"] == pytest.approx(0.5)
    assert s["expectancy_r"] == pytest.approx(0.5)
    # gross win 4.0, gross loss 2.0 -> PF 2.0
    assert s["profit_factor"] == pytest.approx(2.0)


def test_max_drawdown_r():
    trades = [_t(2.0), _t(-1.0), _t(-1.0), _t(-1.0)]  # peak +2 then -3 -> DD 3
    s = summarize(trades)
    assert s["max_drawdown_r"] == pytest.approx(3.0)


def test_empty():
    s = summarize([])
    assert s["n"] == 0 and s["expectancy_r"] == 0
```

- [ ] **Step 2: Run tests, verify fail**

Run: `.venv/bin/pytest tests/test_metrics.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement `swingbot/metrics.py`**

```python
# swingbot/metrics.py
import numpy as np


def summarize(trades, risk_pct: float = 1.0) -> dict:
    if not trades:
        return {"n": 0, "win_rate": 0.0, "avg_r": 0.0, "expectancy_r": 0.0,
                "profit_factor": 0.0, "max_drawdown_r": 0.0, "sharpe": 0.0,
                "equity_final_r": 0.0}
    r = np.array([t.outcome_r for t in trades], dtype=float)
    wins = r[r > 0]
    losses = r[r < 0]
    equity = np.cumsum(r * risk_pct)
    peak = np.maximum.accumulate(equity)
    dd = (peak - equity).max()
    sharpe = (r.mean() / r.std() * np.sqrt(len(r))) if r.std() > 0 else 0.0
    gross_win = wins.sum()
    gross_loss = -losses.sum()
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    return {
        "n": len(r),
        "win_rate": float((r > 0).mean()),
        "avg_r": float(r.mean()),
        "expectancy_r": float(r.mean()),
        "profit_factor": float(pf),
        "max_drawdown_r": float(dd),
        "sharpe": float(sharpe),
        "equity_final_r": float(equity[-1]),
    }
```

- [ ] **Step 4: Run tests, verify pass**

Run: `.venv/bin/pytest tests/test_metrics.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add swingbot/metrics.py tests/test_metrics.py
git commit -m "feat: R-multiple performance metrics (expectancy/PF/DD/Sharpe)"
```

---

### Task 8: Backtest runner + in-sample/out-of-sample report

**Files:**
- Create: `swingbot/run_backtest.py`
- Create: `tests/test_runner.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `load_instrument(sym) -> (m15,h1,d1)`; `split(feats, cutoff="2023-01-01")`; `run_all(symbols=UNIVERSE, cutoff=...) -> dict[sym -> {"is":summary,"oos":summary,"trades":[...]}]`; `render_report(results) -> str`. `UNIVERSE` and per-symbol relaxed-trend flag (EUR/USD relaxed) defined here. `__main__` runs `run_all`, prints + writes `reports/phase1_backtest.md`. Uses M15 file span (2024+) for entry, full H1/D1 for context.

- [ ] **Step 1: Write failing test (runner executes end-to-end on real data)**

```python
# tests/test_runner.py
from swingbot.run_backtest import load_instrument, run_one


def test_run_one_xauusd_executes():
    res = run_one("XAUUSD")
    assert "is" in res and "oos" in res and "trades" in res
    assert res["is"]["n"] + res["oos"]["n"] == len(res["trades"])
```

- [ ] **Step 2: Run test, verify fails**

Run: `.venv/bin/pytest tests/test_runner.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement `swingbot/run_backtest.py`**

```python
# swingbot/run_backtest.py
import pandas as pd
from swingbot.indicators import load_csv
from swingbot.features import build_features
from swingbot.backtest import run_backtest
from swingbot.costs import SPREADS
from swingbot.metrics import summarize

UNIVERSE = ["XAUUSD", "USDJPY", "EURUSD", "USDCHF", "NZDUSD", "GBPUSD", "USDCAD"]
RELAXED = {"EURUSD": True}
CUTOFF = pd.Timestamp("2023-01-01", tz="UTC")


def load_instrument(sym):
    s = sym.lower()
    return (load_csv(f"data/raw/{s}_m15.csv"),
            load_csv(f"data/raw/{s}_h1.csv"),
            load_csv(f"data/raw/{s}_d1.csv"))


def run_one(sym):
    m15, h1, d1 = load_instrument(sym)
    feats = build_features(m15, h1, d1)
    trades = run_backtest(sym, feats, m15, SPREADS[sym],
                          relaxed_trend=RELAXED.get(sym, False))
    is_t = [t for t in trades if t.entry_ts < CUTOFF]
    oos_t = [t for t in trades if t.entry_ts >= CUTOFF]
    return {"is": summarize(is_t), "oos": summarize(oos_t), "trades": trades}


def run_all(symbols=UNIVERSE):
    return {sym: run_one(sym) for sym in symbols}


def render_report(results) -> str:
    lines = ["# Phase 1 — Backtest Validation Report\n",
             "_Trend-pullback swing profile. IS = pre-2023, OOS = 2023+. "
             "R-multiples net of spread. Flat 1% risk._\n",
             "| Sym | IS n | IS win% | IS exp(R) | IS PF | OOS n | OOS win% | "
             "OOS exp(R) | OOS PF | OOS maxDD(R) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for sym, r in results.items():
        a, b = r["is"], r["oos"]
        lines.append(
            f"| {sym} | {a['n']} | {a['win_rate']*100:.0f}% | {a['expectancy_r']:+.2f} "
            f"| {a['profit_factor']:.2f} | {b['n']} | {b['win_rate']*100:.0f}% | "
            f"{b['expectancy_r']:+.2f} | {b['profit_factor']:.2f} | {b['max_drawdown_r']:.1f} |")
    return "\n".join(lines)


if __name__ == "__main__":
    results = run_all()
    report = render_report(results)
    print(report)
    with open("reports/phase1_backtest.md", "w") as f:
        f.write(report + "\n")
```

- [ ] **Step 4: Run test, verify pass**

Run: `.venv/bin/pytest tests/test_runner.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Run the full backtest and inspect**

Run: `.venv/bin/python -m swingbot.run_backtest`
Expected: prints the per-instrument IS/OOS table and writes `reports/phase1_backtest.md`.

- [ ] **Step 6: Commit**

```bash
git add swingbot/run_backtest.py tests/test_runner.py reports/phase1_backtest.md
git commit -m "feat: backtest runner with IS/OOS split and validation report"
```

---

### Task 9: Confluence grading + tier-expectancy analysis

**Files:**
- Create: `swingbot/grading.py`
- Create: `tests/test_grading.py`
- Modify: `swingbot/backtest.py` (attach `score` + `tier` to each `Trade`; add `score` field)
- Modify: `swingbot/run_backtest.py` (add a tier-vs-expectancy table to the report)

**Interfaces:**
- Consumes: signal row + Signal.
- Produces: `confluence_score(row, sig, recent_pivots) -> int` (0–5: +1 strong ADX bias not required here since ADX optional — use: deep pullback (RSI extreme), prime session 12–16 UTC, rr≥3, round-number proximity, structural-level confluence); `tier_of(score) -> str` ("A"/"AA"/"SSS"); analysis groups OOS trades by tier and reports expectancy per tier (proves whether higher tiers win more — the gate for raising SSS risk).

- [ ] **Step 1: Write failing tests**

```python
# tests/test_grading.py
from swingbot.grading import confluence_score, tier_of


def test_tier_thresholds():
    assert tier_of(0) == "A"
    assert tier_of(2) == "AA"
    assert tier_of(4) == "SSS"


def test_score_rewards_prime_session_and_high_rr():
    import pandas as pd
    from swingbot.strategy import Signal
    ts = pd.Timestamp("2024-03-04 13:00", tz="UTC")  # prime overlap
    sig = Signal(ts=ts, side=1, entry=2000.0, stop=1980.0, tp=2065.0, rr=3.25, atr=10)
    row = {"h1_rsi": 30}
    score = confluence_score(row, sig, recent_pivots=[("L", 1999.0)])
    assert score >= 2  # prime session (+1) and rr>=3 (+1) at least
```

- [ ] **Step 2: Run tests, verify fail**

Run: `.venv/bin/pytest tests/test_grading.py -v`
Expected: FAIL (module missing).

- [ ] **Step 3: Implement `swingbot/grading.py`**

```python
# swingbot/grading.py
def _round_number_proximity(price: float) -> bool:
    """Within ~0.1% of a 'round' level (…00 for FX, …0/…00 for gold)."""
    for step in (price * 0, ):  # placeholder to keep structure; real steps below
        pass
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
```

- [ ] **Step 4: Wire score+tier into `backtest.py`**

Add `score: int = 0` and `tier: str = "A"` fields to `Trade` (with defaults). In `run_backtest`, after building `sig` and before/at append, compute:

```python
from swingbot.grading import confluence_score, tier_of   # top of backtest.py
# ... where the Trade is appended, compute:
score = confluence_score(row, sig, piv)
# add score=score, tier=tier_of(score) to the Trade(...) call
```

- [ ] **Step 5: Add tier analysis to the report in `run_backtest.py`**

```python
# append to render_report(), after the per-symbol table:
def _tier_table(results):
    from collections import defaultdict
    buckets = defaultdict(list)
    for r in results.values():
        for t in r["trades"]:
            if t.entry_ts >= CUTOFF:           # OOS only
                buckets[t.tier].append(t.outcome_r)
    out = ["\n## OOS expectancy by tier (does higher tier win more?)\n",
           "| Tier | n | win% | expectancy(R) |", "|---|---|---|---|"]
    for tier in ("A", "AA", "SSS"):
        rs = buckets.get(tier, [])
        if rs:
            wr = sum(1 for x in rs if x > 0) / len(rs)
            out.append(f"| {tier} | {len(rs)} | {wr*100:.0f}% | {sum(rs)/len(rs):+.2f} |")
        else:
            out.append(f"| {tier} | 0 | – | – |")
    return "\n".join(out)
# and in render_report: return "\n".join(lines) + "\n" + _tier_table(results)
```

- [ ] **Step 6: Run tests + regenerate report**

Run: `.venv/bin/pytest tests/test_grading.py -v && .venv/bin/python -m swingbot.run_backtest`
Expected: grading tests PASS; report now includes the tier-expectancy table.

- [ ] **Step 7: Commit**

```bash
git add swingbot/grading.py tests/test_grading.py swingbot/backtest.py swingbot/run_backtest.py reports/phase1_backtest.md
git commit -m "feat: confluence grading + OOS tier-expectancy analysis"
```

---

### Task 10: Validation interpretation + per-pair profitability cut

**Files:**
- Create: `reports/phase1_findings.md` (written by hand from the data, with Claude's interpretation)
- Modify: `docs/superpowers/specs/2026-06-22-trading-signal-bot-design.md` (record which pairs survived OOS, any param notes)

**Interfaces:** none (analysis/decision task).

- [ ] **Step 1: Read the generated report**

Run: `cat reports/phase1_backtest.md`

- [ ] **Step 2: Apply the keep/drop rule and write findings**

Write `reports/phase1_findings.md` capturing, for each instrument: IS vs OOS expectancy, win rate, profit factor, max drawdown, and a KEEP/DROP verdict. Decision rule (state it explicitly in the file):
- **KEEP** if OOS expectancy > 0, OOS profit factor ≥ 1.2, and OOS behavior is consistent with IS (no severe degradation).
- **DROP** otherwise (record the reason — e.g. "USDCAD OOS expectancy −0.05R, PF 0.9 → costs exceed edge").
- Note whether the tier table shows SSS > AA > A expectancy (decides whether tiered risk is justified or stays flat).

- [ ] **Step 3: Record decisions in the spec**

Update the spec's §3 (universe) with the surviving pairs and add a short "Phase 1 results" note (date, headline expectancy, pairs kept). This closes the loop: the backtest, not opinion, set the final universe.

- [ ] **Step 4: Commit**

```bash
git add reports/phase1_findings.md docs/superpowers/specs/2026-06-22-trading-signal-bot-design.md
git commit -m "docs: Phase 1 validation findings and final universe cut"
```

---

## Self-Review

**Spec coverage:**
- Trend-pullback gates (spec §4) → Tasks 3–4. ✅
- No-lookahead / backtestable (spec §1) → Task 2 (critical test) + Task 5. ✅
- 7-pair universe, EUR/USD relaxed (spec §3) → Task 8 (`UNIVERSE`, `RELAXED`). ✅
- R:R ≥2 reachable TP, ATR-floored stop, no trailing (spec §4) → Task 4. ✅
- Session gate (spec §4 ⑤) → Task 3; News gate out-of-scope, documented (Global Constraints). ✅
- Costs modeled (spec §8) → Task 6 (`costs.py`, half-spread each side). ✅
- IS/OOS validation, metrics expectancy/PF/Sharpe/Calmar/DD (spec §8) → Tasks 7–8. (Calmar = expectancy_r/maxDD derivable; note: only Sharpe+maxDD computed directly — acceptable for Phase 1; Calmar can be read as equity_final_r / max_drawdown_r.) ✅
- Lean-core-first, confluence boosters tested in grading (spec §4) → Task 9 (round-number, structural, session, rr, deep-pullback as score, NOT hard gates). ✅
- Per-pair profitability cut by data (spec §3) → Task 10. ✅
- Tiered risk earned by data (spec §4) → Task 9 tier-expectancy table + Task 10 decision. ✅

**Placeholder scan:** `_round_number_proximity` had a no-op loop stub — it's harmless but should be removed at implementation; the real logic (gold→nearest 50, fx→nearest 0.01) is present below it. No "TBD"/"implement later" remain. Out-of-scope news gate is explicitly documented, not silently skipped.

**Type consistency:** `Trade` gains `score:int=0, tier:str="A"` in Task 9 with defaults so Task 6 tests still construct it positionally up to `reason` (the new fields are keyword/default at the end — verify they are appended AFTER `reason` in the dataclass). `summarize` keys used in `render_report` match Task 7. `build_signal(...ts=...)` signature matches its call in `backtest.py`. `align_htf(prefix="")` guard added in Task 5 matches Task 2's implementation.

> ⚠️ Implementer note: when adding `score`/`tier` to `Trade` in Task 9, append them as the **last** fields with defaults so the positional construction in `backtest.py` (Task 6) and `tests/test_backtest.py` remains valid.
