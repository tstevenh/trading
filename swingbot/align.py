# swingbot/align.py
import pandas as pd

FREQ = {"m15": "15min", "h1": "1h", "d1": "1D"}


def tf_close_index(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Reindex a timeframe frame by bar CLOSE time (= open timestamp + 1 period).
    Dukascopy timestamps are bar OPEN times; a bar's data is only known at close."""
    out = df.copy()
    orig_dtype = out.index.dtype
    out.index = out.index + pd.Timedelta(FREQ.get(freq, freq))
    # Preserve original datetime resolution (e.g. ms) to avoid merge key mismatch.
    out.index = out.index.astype(orig_dtype)
    out.index.name = "close_time"
    return out


def align_htf(base: pd.DataFrame, htf: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Attach higher-timeframe columns to `base` rows using only CLOSED htf bars.

    If `htf` is not already indexed by close time (index.name != 'close_time'),
    the shift is applied automatically using the frame's inferred period frequency.
    """
    # Ensure htf is indexed by bar CLOSE time (open + 1 period) for no-lookahead.
    if htf.index.name != "close_time":
        freq = htf.index.freq
        if freq is None:
            raise ValueError(
                "align_htf: htf.index.freq is None (likely loaded from CSV with gaps). "
                "Call tf_close_index(htf, freq) explicitly before align_htf."
            )
        htf = htf.copy()
        htf.index = htf.index + freq
        htf.index.name = "close_time"

    left = base.sort_index().reset_index()
    left_time = left.columns[0]
    right = htf.sort_index().reset_index().rename(
        columns={"close_time": "_c"})
    if prefix:
        right = right.rename(columns={c: f"{prefix}_{c}" for c in htf.columns})
    merged = pd.merge_asof(
        left, right, left_on=left_time, right_on="_c", direction="backward")
    merged = merged.set_index(left_time)
    merged = merged.drop(columns=["_c"])
    return merged
