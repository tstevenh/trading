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
