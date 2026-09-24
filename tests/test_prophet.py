# tests/test_prophet.py

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

from src.models.prophet import (
    build_daily,
    build_train_frame,
    build_future_frame,
    plot_forecast,
    DAILY_FEATURES,
    TARGET,
)


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

def _make_daily(n_days: int = 200, seed: int = 42) -> pd.DataFrame:
    """DataFrame avec DatetimeIndex et toutes les colonnes requises."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n_days, freq="D")
    data = {TARGET: rng.normal(5, 1, n_days)}
    for col in DAILY_FEATURES:
        data[col] = rng.uniform(0, 10, n_days)
    df = pd.DataFrame(data, index=dates)
    df.index.name = "date_index"
    return df


def _make_raw_df(n_days: int = 200, seed: int = 42) -> pd.DataFrame:
    """DataFrame brut avec colonne date_index (avant set_index), pour build_daily."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n_days, freq="D")
    data = {"date_index": dates, TARGET: rng.normal(5, 1, n_days)}
    for col in DAILY_FEATURES:
        data[col] = rng.uniform(0, 10, n_days)
    return pd.DataFrame(data)


@pytest.fixture
def daily() -> pd.DataFrame:
    return _make_daily()


# ─────────────────────────────────────────────
# build_daily
# ─────────────────────────────────────────────

class TestBuildDaily:

    def test_returns_dataframe(self):
        result = build_daily(_make_raw_df())
        assert isinstance(result, pd.DataFrame)

    def test_index_is_datetime(self):
        result = build_daily(_make_raw_df())
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_expected_columns(self):
        result = build_daily(_make_raw_df())
        assert TARGET in result.columns
        for col in DAILY_FEATURES:
            assert col in result.columns

    def test_no_extra_columns(self):
        result = build_daily(_make_raw_df())
        assert set(result.columns) == set([TARGET] + DAILY_FEATURES)

    def test_deduplicates_same_day(self):
        """Deux lignes le même jour → une seule ligne (mean)."""
        df = _make_raw_df(n_days=10)
        df_dup = pd.concat([df, df], ignore_index=True)
        result = build_daily(df_dup)
        assert not result.index.duplicated().any()
        assert len(result) == 10

    def test_missing_column_raises(self):
        df = _make_raw_df()
        df = df.drop(columns=[DAILY_FEATURES[0]])
        with pytest.raises(KeyError, match="Missing columns"):
            build_daily(df)

    def test_missing_target_raises(self):
        df = _make_raw_df()
        df = df.drop(columns=[TARGET])
        with pytest.raises(KeyError, match="Missing columns"):
            build_daily(df)

    def test_does_not_mutate_input(self):
        df = _make_raw_df()
        original_cols = df.columns.tolist()
        build_daily(df)
        assert df.columns.tolist() == original_cols


# ─────────────────────────────────────────────
# build_train_frame
# ─────────────────────────────────────────────

class TestBuildTrainFrame:

    def test_returns_tuple(self, daily):
        result = build_train_frame(daily, H=14)
        assert isinstance(result, tuple) and len(result) == 2

    def test_df_has_ds_y_and_regressors(self, daily):
        df, reg_cols = build_train_frame(daily, H=14)
        assert "date_index" in df.columns
        assert "y" in df.columns
        for col in reg_cols:
            assert col in df.columns

    def test_regressor_cols_named_with_lag(self, daily):
        _, reg_cols = build_train_frame(daily, H=14)
        for col in reg_cols:
            assert col.endswith("_lag14")

    def test_no_nan_in_output(self, daily):
        df, reg_cols = build_train_frame(daily, H=14)
        assert df[["y"] + reg_cols].isna().sum().sum() == 0

    def test_train_shorter_than_input(self, daily):
        """Le lag H supprime les H premières lignes sans régresseur connu."""
        df, _ = build_train_frame(daily, H=14)
        assert len(df) < len(daily)

    def test_horizon_affects_row_count(self, daily):
        df14, _ = build_train_frame(daily, H=14)
        df30, _ = build_train_frame(daily, H=30)
        assert len(df14) > len(df30)

    def test_ds_is_datetime(self, daily):
        df, _ = build_train_frame(daily, H=14)
        assert pd.api.types.is_datetime64_any_dtype(df["date_index"])

    def test_index_reset(self, daily):
        df, _ = build_train_frame(daily, H=14)
        assert list(df.index[:3]) == [0, 1, 2]


# ─────────────────────────────────────────────
# build_future_frame
# ─────────────────────────────────────────────

class TestBuildFutureFrame:

    def test_returns_tuple(self, daily):
        result = build_future_frame(daily, H=14)
        assert isinstance(result, tuple) and len(result) == 2

    def test_future_extends_beyond_train(self, daily):
        """future.ds doit contenir des dates au-delà de la dernière date d'entraînement."""
        df_train, _ = build_train_frame(daily, H=14)
        df_future, _ = build_future_frame(daily, H=14)
        last_train = df_train["date_index"].max()
        assert df_future["date_index"].max() > last_train

    def test_future_longer_than_train(self, daily):
        df_train, _ = build_train_frame(daily, H=14)
        df_future, _ = build_future_frame(daily, H=14)
        assert len(df_future) > len(df_train)

    def test_future_h14_vs_h30(self, daily):
        df14, _ = build_future_frame(daily, H=14)
        df30, _ = build_future_frame(daily, H=30)
        assert df30["date_index"].max() > df14["date_index"].max()

    def test_no_nan_in_regressors(self, daily):
        df, reg_cols = build_future_frame(daily, H=14)
        assert df[reg_cols].isna().sum().sum() == 0

    def test_same_regressor_cols_as_train(self, daily):
        _, train_regs = build_train_frame(daily, H=14)
        _, future_regs = build_future_frame(daily, H=14)
        assert train_regs == future_regs


# ─────────────────────────────────────────────
# plot_forecast
# ─────────────────────────────────────────────

class TestPlotForecast:

    def _make_prophet_df(self, n: int = 200) -> pd.DataFrame:
        dates = pd.date_range("2020-01-01", periods=n, freq="D")
        rng = np.random.default_rng(0)
        return pd.DataFrame({"date_index": dates, "y": rng.normal(5, 1, n)})

    def _make_forecast(self, df_prophet: pd.DataFrame, H: int = 14) -> pd.DataFrame:
        last = df_prophet["date_index"].max()
        future_dates = pd.date_range(last + pd.Timedelta(days=1), periods=H, freq="D")
        all_dates = pd.concat([df_prophet["date_index"],
                                pd.Series(future_dates)]).reset_index(drop=True)
        n = len(all_dates)
        rng = np.random.default_rng(1)
        return pd.DataFrame({
            "date_index":         all_dates,
            "yhat":       rng.normal(5, 1, n),
            "yhat_lower": rng.normal(4, 1, n),
            "yhat_upper": rng.normal(6, 1, n),
        })

    def test_returns_figure(self):
        import plotly.graph_objects as go
        df_p = self._make_prophet_df()
        fc   = self._make_forecast(df_p)
        fig  = plot_forecast(df_p, fc, H=14)
        assert isinstance(fig, go.Figure)

    def test_figure_has_traces(self):
        df_p = self._make_prophet_df()
        fc   = self._make_forecast(df_p)
        fig  = plot_forecast(df_p, fc, H=14)
        assert len(fig.data) > 0

    def test_title_contains_horizon(self):
        df_p = self._make_prophet_df()
        fc   = self._make_forecast(df_p)
        fig  = plot_forecast(df_p, fc, H=14)
        assert "14" in fig.layout.title.text

    def test_different_horizons_different_titles(self):
        df_p = self._make_prophet_df()
        fc14 = self._make_forecast(df_p, H=14)
        fc30 = self._make_forecast(df_p, H=30)
        fig14 = plot_forecast(df_p, fc14, H=14)
        fig30 = plot_forecast(df_p, fc30, H=30)
        assert fig14.layout.title.text != fig30.layout.title.text