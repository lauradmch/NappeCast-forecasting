# tests/unit/test_features_engineering.py

import pytest
import pandas as pd
import numpy as np
from datetime import date
from unittest.mock import patch, MagicMock

from src.features.features_engineering import (
    standardize_index,
    add_standardized_features,
    featuring_dataset,
    feature_engineering,
)


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

def _make_daily_df(n_years: int = 5, seed: int = 42) -> pd.DataFrame:
    """DataFrame journalier synthétique couvrant toutes les colonnes requises."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2018-01-01", periods=n_years * 365, freq="D")
    n = len(dates)

    df = pd.DataFrame(
        {
            "date_index": dates,
            "niveau_nappe_eau":                  rng.normal(5.0, 1.0, n),
            "precipitation_sum":                 rng.uniform(0, 15, n),
            "et0_fao_evapotranspiration":        rng.uniform(0, 8, n),
            "soil_temperature_0_to_100cm_mean":  rng.normal(12, 5, n),
            "shortwave_radiation_sum":           rng.uniform(0, 30, n),
            "wind_speed_10m_mean":               rng.uniform(0, 10, n),
            "cloud_cover_mean":                  rng.uniform(0, 100, n),
            "pressure_msl_mean":                 rng.normal(1013, 10, n),
            "soil_moisture_0_to_100cm_mean":     rng.uniform(0.1, 0.5, n),
        }
    )
    return df


@pytest.fixture
def daily_df() -> pd.DataFrame:
    return _make_daily_df()


@pytest.fixture
def daily_series(daily_df) -> pd.Series:
    """Série journalière avec DatetimeIndex, pour tester standardize_index."""
    s = daily_df.set_index("date_index")["precipitation_sum"]
    s.name = "precipitation_sum"
    return s


# ─────────────────────────────────────────────
# standardize_index
# ─────────────────────────────────────────────

class TestStandardizeIndex:

    def test_output_is_series(self, daily_series):
        result = standardize_index(daily_series)
        assert isinstance(result, pd.Series)

    def test_monthly_frequency(self, daily_series):
        result = standardize_index(daily_series, freq="MS")
        assert result.index.freqstr in ("MS", "ME", "M")

    def test_approximately_standard_normal(self, daily_series):
        """Sur une longue série, mean ≈ 0 et std ≈ 1."""
        result = standardize_index(daily_series, scale=1)
        result_clean = result.dropna()
        assert abs(result_clean.mean()) < 0.2
        assert abs(result_clean.std() - 1.0) < 0.25

    def test_scale_introduces_leading_nans(self, daily_series):
        """Un scale > 1 produit des NaN au début (rolling window)."""
        result = standardize_index(daily_series, scale=3)
        assert result.isna().sum() > 0

    def test_scale_1_no_extra_nans(self, daily_series):
        """scale=1 ne doit introduire aucun NaN supplémentaire."""
        result = standardize_index(daily_series, scale=1)
        assert result.isna().sum() == 0

    def test_output_name(self, daily_series):
        result = standardize_index(daily_series, scale=3)
        assert result.name == "precipitation_sum_s3"

    def test_agg_sum_produces_monthly_series(self, daily_series):
        """agg='sum' produit une série mensuelle valide sans NaN."""
        result = standardize_index(daily_series, agg="sum")
        assert result.isna().sum() == 0
        assert len(result) > 0


# ─────────────────────────────────────────────
# add_standardized_features
# ─────────────────────────────────────────────

class TestAddStandardizedFeatures:

    @pytest.fixture
    def indexed_df(self, daily_df) -> pd.DataFrame:
        df = daily_df.copy()
        df = df.set_index("date_index")
        df.index = pd.DatetimeIndex(df.index)
        return df

    def test_returns_dataframe(self, indexed_df):
        result = add_standardized_features(indexed_df)
        assert isinstance(result, pd.DataFrame)

    def test_expected_columns_present(self, indexed_df):
        result = add_standardized_features(indexed_df)
        expected = ["SPLI", "SPI", "SETI", "SSTI", "SSRI", "SWSI",
                    "SCCI", "SPMI", "SPEI", "SSMI"]
        for col in expected:
            assert col in result.columns, f"Colonne manquante : {col}"

    def test_original_columns_preserved(self, indexed_df):
        result = add_standardized_features(indexed_df)
        for col in indexed_df.columns:
            assert col in result.columns

    def test_no_peff_in_output(self, indexed_df):
        """Peff est une colonne intermédiaire — elle ne doit PAS survivre dans la sortie finale
        (ce test documente le comportement attendu dans feature_engineering)."""
        # Dans add_standardized_features seule, Peff EST présente (supprimée plus haut)
        result = add_standardized_features(indexed_df)
        assert "Peff" in result.columns  # ajoutée ici, retirée dans feature_engineering

    def test_index_unchanged(self, indexed_df):
        result = add_standardized_features(indexed_df)
        pd.testing.assert_index_equal(result.index, indexed_df.index)

    def test_multiple_scales(self, indexed_df):
        """Avec scales=[1, 3], chaque indice doit quand même exister (une seule clé par nom dans le dict)."""
        result = add_standardized_features(indexed_df, scales=[1, 3])
        assert "SPLI" in result.columns


# ─────────────────────────────────────────────
# featuring_dataset
# ─────────────────────────────────────────────

class TestFeaturingDataset:

    def test_returns_dataframe(self, daily_df):
        result = featuring_dataset(daily_df)
        assert isinstance(result, pd.DataFrame)

    def test_index_is_datetime(self, daily_df):
        result = featuring_dataset(daily_df)
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_rolling_columns_present(self, daily_df):
        result = featuring_dataset(daily_df)
        for col in ["p_cum_30d", "p_cum_90d", "peff_cum_30d", "peff_cum_90d",
                    "temperature_mean_30d", "temperature_mean_90d"]:
            assert col in result.columns, f"Colonne manquante : {col}"

    def test_no_nan_in_rolling_cols(self, daily_df):
        """Les NaN de début de rolling doivent être comblés par fillna."""
        result = featuring_dataset(daily_df)
        rolling_cols = ["p_cum_30d", "p_cum_90d", "peff_cum_30d", "peff_cum_90d",
                        "temperature_mean_30d", "temperature_mean_90d"]
        assert result[rolling_cols].isna().sum().sum() == 0

    def test_no_duplicated_index(self, daily_df):
        """Les doublons de dates doivent être supprimés."""
        # Injecter un doublon
        row = daily_df.iloc[[0]].copy()
        df_with_dup = pd.concat([daily_df, row], ignore_index=True)
        result = featuring_dataset(df_with_dup)
        assert not result.index.duplicated().any()

    def test_daily_frequency_complete(self, daily_df):
        """Après asfreq('D'), aucun jour ne doit manquer dans la plage."""
        result = featuring_dataset(daily_df)
        expected_range = pd.date_range(result.index.min(), result.index.max(), freq="D")
        assert len(result) == len(expected_range)

    def test_does_not_mutate_input(self, daily_df):
        original_cols = daily_df.columns.tolist()
        featuring_dataset(daily_df)
        assert daily_df.columns.tolist() == original_cols

    def test_temperature_rounding(self, daily_df):
        result = featuring_dataset(daily_df)
        # round(x, 2) → au plus 2 décimales
        temps = result["temperature_mean_30d"].dropna()
        assert (temps.round(2) == temps).all()


# ─────────────────────────────────────────────
# feature_engineering (orchestrateur)
# ─────────────────────────────────────────────

class TestFeatureEngineering:

    @patch("src.features.features_engineering.save_processed_data_to_s3")
    def test_save_called_when_flag_true(self, mock_save, daily_df):
        feature_engineering(daily_df, save_file=True)
        mock_save.assert_called_once()

    @patch("src.features.features_engineering.save_processed_data_to_s3")
    def test_save_not_called_when_flag_false(self, mock_save, daily_df):
        feature_engineering(daily_df, save_file=False)
        mock_save.assert_not_called()

    @patch("src.features.features_engineering.save_processed_data_to_s3")
    def test_peff_dropped(self, mock_save, daily_df):
        result = feature_engineering(daily_df, save_file=False)
        assert "Peff" not in result.columns

    @patch("src.features.features_engineering.save_processed_data_to_s3")
    def test_std_cols_no_nan(self, mock_save, daily_df):
        """Les NaN résiduels sur les colonnes S*I doivent être comblés par la mean."""
        result = feature_engineering(daily_df, save_file=False)
        std_cols = result.filter(regex=r"^S.*I$").columns
        assert result[std_cols].isna().sum().sum() == 0

    @patch("src.features.features_engineering.save_processed_data_to_s3")
    def test_does_not_mutate_input(self, mock_save, daily_df):
        original = daily_df.copy()
        feature_engineering(daily_df, save_file=False)
        pd.testing.assert_frame_equal(daily_df, original)

    @patch("src.features.features_engineering.save_processed_data_to_s3")
    def test_output_shape_reasonable(self, mock_save, daily_df):
        """Le pipeline ne doit pas réduire le nombre de lignes (interpolation au contraire complète)."""
        result = feature_engineering(daily_df, save_file=False)
        assert len(result) >= len(daily_df)