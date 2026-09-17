import numpy as np
import pandas as pd
import pytest

from src.helper.indices import (
    characterize_events,
    cross_corr,
    longest_and_most_intense,
    monthly,
    to_datetime_index,
)


def _monthly_series(values):
    idx = pd.date_range("2000-01-01", periods=len(values), freq="MS")
    return pd.Series(values, index=idx, dtype=float)


def test_to_datetime_index_keeps_column_and_copies():
    df = pd.DataFrame({"date_index": ["2020-01-02", "2020-01-01"], "x": [1, 2]})
    out = to_datetime_index(df)
    assert isinstance(out.index, pd.DatetimeIndex)
    assert "date_index" in out.columns
    assert not pd.api.types.is_datetime64_any_dtype(df["date_index"])  # original untouched


def test_monthly_is_one_value_per_month():
    idx = pd.date_range("2020-01-01", "2020-03-31", freq="D")
    s = pd.Series(1.0, index=idx)
    assert len(monthly(s)) == 3


def test_no_event():
    ev = characterize_events(_monthly_series([0, 0.5, -1.0]))
    assert ev.empty
    assert longest_and_most_intense(ev) == (None, None)


def test_two_separate_events():
    #                    event 1 (2 months)  gap        event 2
    s = _monthly_series([0, -2.0, -1.6, 0, 0, 0, -3.0, 0])
    ev = characterize_events(s, threshold=-1.5)
    assert len(ev) == 2
    assert ev["duration_m"].tolist() == [2, 1]
    assert ev["peak"].tolist() == [-2.0, -3.0]
    assert ev["severity"].tolist() == pytest.approx([0.6, 1.5])


def test_pooling_merges_events_one_month_apart():
    # gap = months between the start of an event and the end of the previous one:
    # Jan -> Mar = 2, so min_gap=2 merges, min_gap=1 (the default) does not
    s = _monthly_series([-2.0, 0, -2.0])
    assert len(characterize_events(s, threshold=-1.5, min_gap=2)) == 1
    assert len(characterize_events(s, threshold=-1.5, min_gap=1)) == 2
    assert len(characterize_events(s, threshold=-1.5, pooling=False)) == 2


def test_longest_and_most_intense():
    s = _monthly_series([-1.6, -1.6, -1.6, 0, 0, 0, -3.0, 0])
    longest, intense = longest_and_most_intense(characterize_events(s, threshold=-1.5))
    assert longest["duration_m"] == 3
    assert intense["peak"] == -3.0


def test_invalid_direction():
    with pytest.raises(ValueError):
        characterize_events(_monthly_series([0]), direction="sideways")


def test_cross_corr_finds_known_lag():
    rng = np.random.default_rng(0)
    driver = _monthly_series(rng.normal(size=120))
    response = driver.shift(3)                    # response lags driver by 3 months
    corr = cross_corr(driver, response, maxlag=6)
    best = max(corr, key=lambda k: corr[k] if not np.isnan(corr[k]) else -1)
    assert best == 3
    assert corr[3] == pytest.approx(1.0)