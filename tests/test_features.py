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
