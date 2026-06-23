#!/usr/bin/env python3
"""Fetch clean M15 history for all 7 pairs from HistData.com (free, no key, no limits).

HistData provides 1-minute bars in US-Eastern time. We download per-year M1 zips,
convert ET->UTC, resample to M15, and write data/raw/{pair}_m15.csv in our standard
format (timestamp ms UTC, open, high, low, close, volume) — a drop-in replacement
for the unreliable Dukascopy M15 files.
"""
from __future__ import annotations
import os, zipfile
import pandas as pd
from histdata import download_hist_data as dl
from histdata.api import Platform as P, TimeFrame as TF

PAIRS = ["eurusd", "gbpusd", "usdjpy", "usdchf", "usdcad", "nzdusd", "xauusd"]
YEARS_FULL = ["2020", "2021", "2022", "2023", "2024", "2025"]
CUR_YEAR, CUR_MONTHS = "2026", [str(m) for m in range(1, 7)]   # Jan–Jun 2026
WORK = os.path.abspath("data/histdata_raw")
os.makedirs(WORK, exist_ok=True)
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


def load_zip(zippath: str) -> pd.DataFrame:
    with zipfile.ZipFile(zippath) as z:
        name = [n for n in z.namelist() if n.lower().endswith(".csv")][0]
        df = pd.read_csv(z.open(name), sep=";", header=None,
                         names=["dt", "open", "high", "low", "close", "volume"])
    df["dt"] = pd.to_datetime(df["dt"], format="%Y%m%d %H%M%S")
    return df


def fetch(pair: str, year: str, month):
    cwd = os.getcwd()
    try:
        os.chdir(WORK)
        fn = dl(year=year, month=month, pair=pair,
                platform=P.GENERIC_ASCII, time_frame=TF.ONE_MINUTE)
        return os.path.join(WORK, fn)
    finally:
        os.chdir(cwd)


for pair in PAIRS:
    frames, failed = [], []
    for y in YEARS_FULL:
        try:
            frames.append(load_zip(fetch(pair, y, None)))
        except Exception as e:
            failed.append(f"{y}:{str(e)[:60]}")
    for m in CUR_MONTHS:
        try:
            frames.append(load_zip(fetch(pair, CUR_YEAR, m)))
        except Exception as e:
            failed.append(f"{CUR_YEAR}-{m}:{str(e)[:60]}")
    if not frames:
        print(f"{pair}: NO DATA — failed={failed}", flush=True)
        continue
    m1 = (pd.concat(frames).drop_duplicates("dt").sort_values("dt")
          .set_index("dt"))
    # ET -> UTC (America/New_York handles DST)
    m1.index = m1.index.tz_localize("America/New_York", ambiguous="NaT",
                                    nonexistent="shift_forward")
    m1 = m1[m1.index.notna()].tz_convert("UTC")
    m15 = (m1.resample("15min")
           .agg({"open": "first", "high": "max", "low": "min",
                 "close": "last", "volume": "sum"}).dropna())
    out = m15.reset_index()
    out["timestamp"] = ((out["dt"] - EPOCH) // pd.Timedelta(milliseconds=1)).astype("int64")
    out = out[["timestamp", "open", "high", "low", "close", "volume"]]
    out.to_csv(f"data/raw/{pair}_m15.csv", index=False)
    print(f"{pair}: {len(out)} M15 bars  {m15.index[0].date()} -> {m15.index[-1].date()}"
          f"  failed={failed}", flush=True)

print("HISTDATA M15 DONE", flush=True)
