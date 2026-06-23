#!/usr/bin/env python3
"""Fetch expanded universe: indices + silver (HistData) and crypto (Binance).
Saves m15/h1/d1 CSVs (UTC, standard format) per instrument; H1/D1 resampled from M15."""
from __future__ import annotations
import os, zipfile, urllib.request, json, time
import pandas as pd
from histdata import download_hist_data as dl
from histdata.api import Platform as P, TimeFrame as TF

YEARS = ["2020", "2021", "2022", "2023", "2024", "2025"]
CUR_Y, CUR_M = "2026", [str(m) for m in range(1, 7)]
WORK = os.path.abspath("data/expanded_raw"); os.makedirs(WORK, exist_ok=True)
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")

# HistData code -> our clean ticker
HISTDATA = {"XAGUSD": "xagusd", "SPXUSD": "spx500", "NSXUSD": "nas100",
            "GRXEUR": "ger40", "JPXJPY": "jpn225", "UKXGBP": "uk100"}
BINANCE = {"BTCUSDT": "btcusd", "ETHUSDT": "ethusd"}


def save_std(m15: pd.DataFrame, ticker: str):
    """m15 indexed by UTC datetime with ohlcv; write m15/h1/d1 standard CSVs."""
    for rule, suf in [("15min", "m15"), ("1h", "h1"), ("1D", "d1")]:
        df = (m15.resample(rule).agg({"open": "first", "high": "max", "low": "min",
                                      "close": "last", "volume": "sum"}).dropna()
              if suf != "m15" else m15)
        out = df.reset_index()
        tcol = out.columns[0]
        out["timestamp"] = ((out[tcol] - EPOCH) // pd.Timedelta(milliseconds=1)).astype("int64")
        out[["timestamp", "open", "high", "low", "close", "volume"]].to_csv(
            f"data/raw/{ticker}_{suf}.csv", index=False)


def histdata_m15(code: str) -> pd.DataFrame:
    frames = []
    def grab(y, m):
        cwd = os.getcwd()
        try:
            os.chdir(WORK)
            fn = dl(year=y, month=m, pair=code.lower(), platform=P.GENERIC_ASCII,
                    time_frame=TF.ONE_MINUTE)
            return os.path.join(WORK, fn)
        finally:
            os.chdir(cwd)
    specs = [(y, None) for y in YEARS] + [(CUR_Y, m) for m in CUR_M]
    for y, m in specs:
        try:
            with zipfile.ZipFile(grab(y, m)) as z:
                name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
                d = pd.read_csv(z.open(name), sep=";", header=None,
                                names=["dt", "open", "high", "low", "close", "volume"])
            d["dt"] = pd.to_datetime(d["dt"], format="%Y%m%d %H%M%S")
            frames.append(d)
        except Exception as e:
            print(f"    {code} {y}-{m}: {str(e)[:50]}", flush=True)
    m1 = pd.concat(frames).drop_duplicates("dt").sort_values("dt").set_index("dt")
    m1.index = m1.index.tz_localize("America/New_York", ambiguous="NaT",
                                    nonexistent="shift_forward")
    m1 = m1[m1.index.notna()].tz_convert("UTC")
    return m1.resample("15min").agg({"open": "first", "high": "max", "low": "min",
                                     "close": "last", "volume": "sum"}).dropna()


def binance_m15(symbol: str) -> pd.DataFrame:
    cur, rows = 1577836800000, []          # 2020-01-01 UTC
    while True:
        url = (f"https://api.binance.com/api/v3/klines?symbol={symbol}"
               f"&interval=15m&startTime={cur}&limit=1000")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            data = json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as e:
            print(f"    {symbol} page @ {cur}: {str(e)[:50]}", flush=True); time.sleep(2); continue
        if not data:
            break
        rows += data
        cur = data[-1][0] + 1
        if len(data) < 1000:
            break
        time.sleep(0.15)
    df = pd.DataFrame(rows, columns=["t", "open", "high", "low", "close", "volume",
                                     "ct", "qv", "n", "tb", "tq", "ig"])
    df = df[["t", "open", "high", "low", "close", "volume"]].astype(
        {"open": float, "high": float, "low": float, "close": float, "volume": float})
    df["dt"] = pd.to_datetime(df["t"], unit="ms", utc=True)
    return df.set_index("dt")[["open", "high", "low", "close", "volume"]].sort_index()


for code, ticker in HISTDATA.items():
    print(f"HistData {code} -> {ticker}", flush=True)
    try:
        m15 = histdata_m15(code); save_std(m15, ticker)
        print(f"  {ticker}: {len(m15)} M15 bars {m15.index[0].date()}->{m15.index[-1].date()}", flush=True)
    except Exception as e:
        print(f"  {ticker}: FAILED {str(e)[:80]}", flush=True)

for symbol, ticker in BINANCE.items():
    print(f"Binance {symbol} -> {ticker}", flush=True)
    try:
        m15 = binance_m15(symbol); save_std(m15, ticker)
        print(f"  {ticker}: {len(m15)} M15 bars {m15.index[0].date()}->{m15.index[-1].date()}", flush=True)
    except Exception as e:
        print(f"  {ticker}: FAILED {str(e)[:80]}", flush=True)

print("EXPANDED FETCH DONE", flush=True)
