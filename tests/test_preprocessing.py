# tests/test_preprocessing.py

import pytest
import pandas as pd
import numpy as np

from src.models.preprocessing import preprocessing


# ─────────────────────────────────────────────
# FIXTURE
# ─────────────────────────────────────────────

def _make_preprocessed_df(n_days: int = 100, seed: int = 42) -> pd.DataFrame:
    """DataFrame synthétique avec toutes les colonnes requises par preprocessing()."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-01", periods=n_days, freq="D")

    return pd.DataFrame({
        "date_index":                        dates,
        "shortwave_radiation_sum":           rng.uniform(0, 30, n_days),
        "et0_fao_evapotranspiration":        rng.uniform(0, 8, n_days),
        "soil_temperature_0_to_100cm_mean":  rng.normal(12, 5, n_days),
        "p_cum_90d":                         rng.uniform(0, 300, n_days),
        "peff_cum_90d":                      rng.uniform(-100, 200, n_days),
        "temperature_mean_90d":              rng.normal(12, 3, n_days),
        "niveau_nappe_eau":                  rng.normal(5, 1, n_days),
    })



@pytest.fixture
def df() -> pd.DataFrame:
    return _make_preprocessed_df()


# ─────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────

class TestPreprocessing:

    def test_returns_four_objects(self, df):
        result = preprocessing(df)
        assert len(result) == 4

    def test_split_sizes_default(self, df):
        """Avec test_size=30 (défaut), test = 30 lignes, train = n - 30."""
        X_train, X_test, y_train, y_test = preprocessing(df)
        assert len(X_test) == 30
        assert len(X_train) == len(df) - 30

    def test_split_sizes_custom(self, df):
        X_train, X_test, y_train, y_test = preprocessing(df, test_size=10)
        assert len(X_test) == 10
        assert len(X_train) == len(df) - 10

    def test_feature_columns(self, df):
        expected = [
            "shortwave_radiation_sum",
            "et0_fao_evapotranspiration",
            "soil_temperature_0_to_100cm_mean",
            "P_cum_90d",
            "Peff_cum_90d",
            "Temperature_mean_90d",
        ]
        X_train, X_test, _, _ = preprocessing(df)
        assert list(X_train.columns) == expected
        assert list(X_test.columns) == expected

    def test_target_is_series(self, df):
        _, _, y_train, y_test = preprocessing(df)
        assert isinstance(y_train, pd.Series)
        assert isinstance(y_test, pd.Series)
        assert y_train.name == "niveau_nappe_eau"
        assert y_test.name == "niveau_nappe_eau"

    def test_index_is_datetime(self, df):
        X_train, X_test, y_train, y_test = preprocessing(df)
        for obj in [X_train, X_test, y_train, y_test]:
            assert isinstance(obj.index, pd.DatetimeIndex)

    def test_train_before_test_temporally(self, df):
        """Toutes les dates du train sont antérieures à toutes celles du test."""
        X_train, X_test, _, _ = preprocessing(df)
        assert X_train.index.max() < X_test.index.min()

    def test_no_nan_in_output(self, df):
        X_train, X_test, y_train, y_test = preprocessing(df)
        for obj in [X_train, X_test, y_train, y_test]:
            assert obj.isna().sum().sum() == 0 if isinstance(obj, pd.DataFrame) else obj.isna().sum() == 0

    def test_does_not_mutate_input(self, df):
        original = df.copy()
        preprocessing(df)
        pd.testing.assert_frame_equal(df, original)

    def test_missing_feature_col_raises(self):
        """Un DataFrame sans une colonne requise doit lever une KeyError."""
        df_bad = _make_preprocessed_df()
        df_bad = df_bad.drop(columns=["P_cum_90d"])
        with pytest.raises(KeyError):
            preprocessing(df_bad)

    def test_missing_target_col_raises(self):
        """Un DataFrame sans la colonne cible doit lever une KeyError."""
        df_bad = _make_preprocessed_df()
        df_bad = df_bad.drop(columns=["niveau_nappe_eau"])
        with pytest.raises(KeyError):
            preprocessing(df_bad)