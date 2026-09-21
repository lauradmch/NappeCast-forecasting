# tests/test_prophet_tune.py

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from src.models.prophet_tune import (
    select_score,
    rescore_params,
    LAMBDA_DEGRADATION,
    LAMBDA_SPREAD,
    PARAM_GRID,
    BASE_PARAMS,
)


# ─────────────────────────────────────────────
# select_score
# ─────────────────────────────────────────────

class TestSelectScore:

    def test_no_penalty_when_perfect(self):
        """degradation=1 et rmse_mae=1 → score = rmse (pas de pénalité)."""
        assert select_score(0.5, 1.0, 1.0) == pytest.approx(0.5)

    def test_degradation_penalty_applied(self):
        """degradation > 1 → score > rmse."""
        score = select_score(0.5, 2.0, 1.0)
        expected = 0.5 * (1 + LAMBDA_DEGRADATION * 1.0)
        assert score == pytest.approx(expected)

    def test_spread_penalty_applied(self):
        """rmse_mae > 1 → score > rmse."""
        score = select_score(0.5, 1.0, 2.0)
        expected = 0.5 * (1 + LAMBDA_SPREAD * 1.0)
        assert score == pytest.approx(expected)

    def test_both_penalties_combined(self):
        score = select_score(0.5, 2.0, 2.0)
        expected = 0.5 * (1 + LAMBDA_DEGRADATION * 1.0) * (1 + LAMBDA_SPREAD * 1.0)
        assert score == pytest.approx(expected)

    def test_degradation_below_1_no_penalty(self):
        """degradation < 1 → clippé à 0, pas de pénalité négative."""
        score = select_score(0.5, 0.5, 1.0)
        assert score == pytest.approx(0.5)

    def test_rmse_mae_below_1_no_penalty(self):
        """rmse_mae < 1 → clippé à 0."""
        score = select_score(0.5, 1.0, 0.8)
        assert score == pytest.approx(0.5)

    def test_zero_rmse(self):
        assert select_score(0.0, 2.0, 2.0) == pytest.approx(0.0)

    def test_works_on_series(self):
        """Doit fonctionner sur des pd.Series (utilisé dans tune_horizon)."""
        rmse = pd.Series([0.3, 0.5])
        deg  = pd.Series([1.0, 2.0])
        mae  = pd.Series([1.0, 1.5])
        result = select_score(rmse, deg, mae)
        assert isinstance(result, pd.Series)
        assert len(result) == 2

    def test_lower_rmse_gives_lower_score_all_else_equal(self):
        assert select_score(0.3, 1.5, 1.2) < select_score(0.5, 1.5, 1.2)

    def test_higher_degradation_gives_higher_score(self):
        assert select_score(0.5, 1.5, 1.0) < select_score(0.5, 3.0, 1.0)

    def test_higher_spread_gives_higher_score(self):
        assert select_score(0.5, 1.0, 1.5) < select_score(0.5, 1.0, 3.0)


# ─────────────────────────────────────────────
# rescore_params
# ─────────────────────────────────────────────

class TestRescoreParams:

    def _make_daily(self) -> pd.DataFrame:
        """DataFrame minimal avec les colonnes attendues par build_train_frame."""
        dates = pd.date_range("2020-01-01", periods=200, freq="D")
        rng = np.random.default_rng(0)
        n = len(dates)
        return pd.DataFrame({
            "date_index":                        dates,
            "niveau_nappe_eau":                  rng.normal(5, 1, n),
            "shortwave_radiation_sum":           rng.uniform(0, 30, n),
            "et0_fao_evapotranspiration":        rng.uniform(0, 8, n),
            "soil_temperature_0_to_100cm_mean":  rng.normal(12, 5, n),
            "P_cum_90d":                         rng.uniform(0, 300, n),
            "Peff_cum_90d":                      rng.uniform(-100, 200, n),
            "Temperature_mean_90d":              rng.normal(12, 3, n),
        })

    def _make_run_params(self) -> dict:
        """Params au format MLflow (strings)."""
        return {
            "changepoint_prior_scale": "0.1",
            "seasonality_prior_scale": "1.0",
            "changepoint_range":       "0.8",
        }

    @patch("src.models.prophet_tune.score_config")
    @patch("src.models.prophet_tune.build_train_frame")
    def test_returns_float(self, mock_build, mock_score):
        mock_build.return_value = (MagicMock(), [])
        mock_score.return_value = {
            "rmse": 0.4, "mae": 0.3, "horizon_degradation": 1.2, "rmse_mae": 1.3,
        }
        result = rescore_params(self._make_daily(), 14, self._make_run_params())
        assert isinstance(result, float)

    @patch("src.models.prophet_tune.score_config")
    @patch("src.models.prophet_tune.build_train_frame")
    def test_converts_string_params_to_float(self, mock_build, mock_score):
        """Les params MLflow sont des strings — rescore_params doit les caster."""
        mock_build.return_value = (MagicMock(), [])
        mock_score.return_value = {
            "rmse": 0.4, "mae": 0.3, "horizon_degradation": 1.0, "rmse_mae": 1.0,
        }
        # Ne doit pas lever de TypeError
        rescore_params(self._make_daily(), 14, self._make_run_params())
        called_params = mock_score.call_args[0][2]  # 3ème arg positionnel = params
        for k in PARAM_GRID:
            assert isinstance(called_params[k], float)

    @patch("src.models.prophet_tune.score_config")
    @patch("src.models.prophet_tune.build_train_frame")
    def test_merges_base_params(self, mock_build, mock_score):
        """BASE_PARAMS doit être fusionné avec les tuned params."""
        mock_build.return_value = (MagicMock(), [])
        mock_score.return_value = {
            "rmse": 0.4, "mae": 0.3, "horizon_degradation": 1.0, "rmse_mae": 1.0,
        }
        rescore_params(self._make_daily(), 14, self._make_run_params())
        called_params = mock_score.call_args[0][2]
        for k in BASE_PARAMS:
            assert k in called_params

    @patch("src.models.prophet_tune.score_config")
    @patch("src.models.prophet_tune.build_train_frame")
    def test_score_consistent_with_select_score(self, mock_build, mock_score):
        """La valeur retournée doit être égale à select_score appliqué aux métriques mockées."""
        mock_build.return_value = (MagicMock(), [])
        mock_score.return_value = {
            "rmse": 0.4, "mae": 0.3, "horizon_degradation": 1.5, "rmse_mae": 1.2,
        }
        result = rescore_params(self._make_daily(), 14, self._make_run_params())
        expected = float(select_score(0.4, 1.5, 1.2))
        assert result == pytest.approx(expected)