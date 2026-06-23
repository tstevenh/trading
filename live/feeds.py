"""Live OHLC feeds for the paper-trading layer.
ETHUSD -> Binance (free, UTC ms). EURUSD + SPX500(via SPY) -> Twelve Data (timezone=UTC).
All return a UTC-indexed DataFrame [open,high,low,close,volume], ascending, with the
most recent (possibly in-progress) bar DROPPED so we only act on CLOSED bars."""
from __future__ import annotations
import urllib.request, urllib.parse, json, pathlib, time
import pandas as pd

_ENV = {}
for _l in pathlib.Path(".env").read_text().splitlines():
    _l = _l.strip()
    if _l and not _l.startswith("#") and "=" in _l:
        _k, _v = _l.split("=", 1)
        _ENV[_k.strip()] = _v.split("#")[0].strip()
TD_KEY = _ENV.get("TWELVEDATA_API_KEY", "")

# instrument -> (source, vendor_symbol)
FEEDS = {
    "ETHUSD": ("binance", "ETHUSDT"),
    "EURUSD": ("twelvedata", "EUR/USD"),
    "SPX500": ("twelvedata", "SPY"),       # SPY ETF as the live S&P 500 proxy
}
BINANCE_IV = {"m15": "15m", "h1": "1h", "d1": "1d"}
TD_IV = {"m15": "15min", "h1": "1h", "d1": "1day"}


def _get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return json.load(urllib.request.urlopen(req, timeout=25))
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(1.5)


def _binance(sym, tf, n):
    url = (f"https://api.binance.com/api/v3/klines?symbol={sym}"
           f"&interval={BINANCE_IV[tf]}&limit={n}")
    rows = _get(url)
    df = pd.DataFrame(rows, columns=["t", "open", "high", "low", "close", "volume",
                                     "ct", "qv", "nt", "tb", "tq", "ig"])
    df = df[["t", "open", "high", "low", "close", "volume"]].astype(
        {"open": float, "high": float, "low": float, "close": float, "volume": float})
    df["dt"] = pd.to_datetime(df["t"], unit="ms", utc=True)
    return df.set_index("dt")[["open", "high", "low", "close", "volume"]].sort_index()


def _twelvedata(sym, tf, n):
    url = (f"https://api.twelvedata.com/time_series?symbol={urllib.parse.quote(sym)}"
           f"&interval={TD_IV[tf]}&outputsize={n}&timezone=UTC&apikey={TD_KEY}")
    js = _get(url)
    if js.get("status") != "ok" or "values" not in js:
        raise RuntimeError(f"twelvedata {sym} {tf}: {str(js)[:120]}")
    df = pd.DataFrame(js["values"])
    for c in ["open", "high", "low", "close"]:
        df[c] = df[c].astype(float)
    df["volume"] = df.get("volume", 0)
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
    df["dt"] = pd.to_datetime(df["datetime"], utc=True)
    return df.set_index("dt")[["open", "high", "low", "close", "volume"]].sort_index()


def fetch(instrument: str, tf: str, n: int, drop_forming: bool = True) -> pd.DataFrame:
    src, sym = FEEDS[instrument]
    df = _binance(sym, tf, n) if src == "binance" else _twelvedata(sym, tf, n)
    if drop_forming and len(df) > 1:
        df = df.iloc[:-1]          # drop the most recent (still-forming) bar
    return df
