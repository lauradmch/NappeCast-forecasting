"""
Pure computations on the standardised indices (SPLI and climate drivers).
No Streamlit here: importable from the app, notebooks and tests.
"""
import pandas as pd

from src.helper.constants import DATE_COL, DROUGHT_EVENT_THRESHOLD

EVENT_COLUMNS = ["start", "end", "duration_m", "peak", "severity"]


def to_datetime_index(df: pd.DataFrame, date_col: str = DATE_COL) -> pd.DataFrame:
    """Return a copy of df indexed by date_col (converted to datetime, column kept)."""
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    return out.set_index(date_col, drop=False)


def monthly(series: pd.Series) -> pd.Series:
    """Collapse a daily (forward-filled) index column to one value per month.
    The standardised indices are constant within a month, so the monthly
    mean recovers that month's value."""
    return series.resample("MS").mean().dropna()


def characterize_events(
    series: pd.Series,
    threshold: float = DROUGHT_EVENT_THRESHOLD,
    direction: str = "below",
    min_gap: int = 2,
    pooling: bool = True,
) -> pd.DataFrame:
    """Run-theory event detection with inter-event pooling.

    An event is a run of consecutive months beyond `threshold`.
    With pooling, events whose gap (start - previous end, in months) is
    <= `min_gap` are merged. Note: separate runs always have gap >= 2,
    so min_gap=1 never merges.
    Returns one row per event: start, end, duration_m, peak, severity
    (severity = cumulative deficit beyond the threshold).
    """
    if direction not in ("below", "above"):
        raise ValueError(f"direction must be 'below' or 'above', got {direction!r}")
    below = direction == "below"

    s = series.dropna()
    hit = (s < threshold) if below else (s > threshold)
    prev = hit.shift(fill_value=False)
    nxt = hit.shift(-1, fill_value=False)
    starts = list(s.index[hit & ~prev])
    ends = list(s.index[hit & ~nxt])
    if not starts:
        return pd.DataFrame(columns=EVENT_COLUMNS)

    if pooling and len(starts) > 1:
        merged = [[starts[0], ends[0]]]
        for stt, en in zip(starts[1:], ends[1:]):
            gap = (stt.to_period("M") - merged[-1][1].to_period("M")).n
            if gap <= min_gap:
                merged[-1][1] = en
            else:
                merged.append([stt, en])
        starts, ends = zip(*merged)

    rows = []
    for stt, en in zip(starts, ends):
        w = s.loc[stt:en]
        peak = w.min() if below else w.max()
        excess = (threshold - w) if below else (w - threshold)
        rows.append({
            "start": stt,
            "end": en,
            "duration_m": len(w),
            "peak": round(float(peak), 2),
            "severity": round(float(excess.clip(lower=0).sum()), 2),
        })
    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


def longest_and_most_intense(events: pd.DataFrame) -> tuple[pd.Series | None, pd.Series | None]:
    """Longest event (max duration) and most intense drought (min peak)."""
    if events.empty:
        return None, None
    return events.loc[events["duration_m"].idxmax()], events.loc[events["peak"].idxmin()]


def cross_corr(driver: pd.Series, response: pd.Series, maxlag: int = 12) -> dict[int, float]:
    """Pearson correlation of driver(t) vs response(t + L) for L = 0..maxlag."""
    common = driver.dropna().index.intersection(response.dropna().index)
    a, b = driver.loc[common], response.loc[common]
    return {lag: a.corr(b.shift(-lag)) for lag in range(maxlag + 1)}