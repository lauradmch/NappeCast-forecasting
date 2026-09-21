# tests/test_prophet_predict.py

import pytest
from unittest.mock import patch, MagicMock, call
import argparse

from src.models.prophet_predict import resolve_tuned_params, print_report, PROPHET_DEFAULTS


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

def _make_args(
    horizon: int = 14,
    from_production: bool = False,
    cps: float = None,
    sps: float = None,
    cpr: float = None,
    register: bool = False,
) -> argparse.Namespace:
    return argparse.Namespace(
        horizon=horizon,
        from_production=from_production,
        cps=cps,
        sps=sps,
        cpr=cpr,
        register=register,
    )


# ─────────────────────────────────────────────
# resolve_tuned_params
# ─────────────────────────────────────────────

class TestResolveTunedParams:

    def test_defaults_source_label(self):
        args = _make_args()
        _, source = resolve_tuned_params(args)
        assert source == "prophet_defaults"

    def test_defaults_values(self):
        args = _make_args()
        tuned, _ = resolve_tuned_params(args)
        assert tuned == PROPHET_DEFAULTS

    def test_manual_override_cps(self):
        args = _make_args(cps=0.3)
        tuned, source = resolve_tuned_params(args)
        assert tuned["changepoint_prior_scale"] == 0.3
        assert source == "manual"

    def test_manual_override_multiple(self):
        args = _make_args(cps=0.3, sps=5.0, cpr=0.9)
        tuned, source = resolve_tuned_params(args)
        assert tuned["changepoint_prior_scale"] == 0.3
        assert tuned["seasonality_prior_scale"] == 5.0
        assert tuned["changepoint_range"] == 0.9
        assert source == "manual"

    def test_no_override_does_not_mutate_defaults(self):
        args = _make_args()
        tuned, _ = resolve_tuned_params(args)
        # PROPHET_DEFAULTS ne doit pas être modifié en place
        assert PROPHET_DEFAULTS["changepoint_prior_scale"] == 0.05

    @patch("src.models.prophet_predict.get_run_params")
    @patch("src.models.prophet_predict.get_version_by_alias")
    @patch("src.models.prophet_predict.MlflowClient")
    def test_from_production_reads_registry(self, MockClient, mock_get_alias, mock_get_params):
        mv = MagicMock()
        mv.version = "3"
        mock_get_alias.return_value = mv
        mock_get_params.return_value = {
            "changepoint_prior_scale": "0.1",
            "seasonality_prior_scale": "1.0",
            "changepoint_range": "0.85",
        }
        args = _make_args(from_production=True)
        tuned, source = resolve_tuned_params(args)
        assert tuned["changepoint_prior_scale"] == 0.1
        assert "production_v3" in source

    @patch("src.models.prophet_predict.get_run_params")
    @patch("src.models.prophet_predict.get_version_by_alias")
    @patch("src.models.prophet_predict.MlflowClient")
    def test_from_production_no_model_raises(self, MockClient, mock_get_alias, mock_get_params):
        mock_get_alias.return_value = None
        args = _make_args(from_production=True)
        with pytest.raises(SystemExit):
            resolve_tuned_params(args)

    @patch("src.models.prophet_predict.get_run_params")
    @patch("src.models.prophet_predict.get_version_by_alias")
    @patch("src.models.prophet_predict.MlflowClient")
    def test_from_production_with_manual_override(self, MockClient, mock_get_alias, mock_get_params):
        mv = MagicMock()
        mv.version = "3"
        mock_get_alias.return_value = mv
        mock_get_params.return_value = {
            "changepoint_prior_scale": "0.1",
            "seasonality_prior_scale": "1.0",
            "changepoint_range": "0.85",
        }
        args = _make_args(from_production=True, cps=0.5)
        tuned, source = resolve_tuned_params(args)
        assert tuned["changepoint_prior_scale"] == 0.5
        assert "manual" in source


# ─────────────────────────────────────────────
# print_report
# ─────────────────────────────────────────────

class TestPrintReport:

    def _make_metrics(self, rmse=0.3, mae=0.2, r2=0.85,
                      rmse_std_ratio=0.4, rmse_mae=1.2,
                      horizon_degradation=1.5, select_score=0.35):
        return {
            "rmse": rmse, "mae": mae, "r2": r2,
            "rmse_std_ratio": rmse_std_ratio, "rmse_mae": rmse_mae,
            "horizon_degradation": horizon_degradation,
            "select_score": select_score,
        }

    def _make_params(self, cps=0.1, sps=1.0, cpr=0.8, interval_width=0.8):
        return {
            "changepoint_prior_scale": cps,
            "seasonality_prior_scale": sps,
            "changepoint_range": cpr,
            "interval_width": interval_width,
        }

    def test_does_not_raise(self, capsys):
        print_report(14, "manual", self._make_params(), self._make_metrics())
        captured = capsys.readouterr()
        assert "H=14" in captured.out

    def test_strong_label(self, capsys):
        print_report(14, "s", self._make_params(), self._make_metrics(rmse_std_ratio=0.4))
        assert "strong" in capsys.readouterr().out

    def test_useful_label(self, capsys):
        print_report(14, "s", self._make_params(), self._make_metrics(rmse_std_ratio=0.6))
        assert "useful" in capsys.readouterr().out

    def test_weak_label(self, capsys):
        print_report(14, "s", self._make_params(), self._make_metrics(rmse_std_ratio=0.9))
        assert "weak" in capsys.readouterr().out

    def test_no_better_than_mean_label(self, capsys):
        print_report(14, "s", self._make_params(), self._make_metrics(rmse_std_ratio=1.2))
        assert "no better than the mean" in capsys.readouterr().out

    def test_errors_uniform_label(self, capsys):
        print_report(14, "s", self._make_params(), self._make_metrics(rmse_mae=1.1))
        assert "errors uniform" in capsys.readouterr().out

    def test_large_misses_label(self, capsys):
        print_report(14, "s", self._make_params(), self._make_metrics(rmse_mae=1.5))
        assert "some large misses" in capsys.readouterr().out

    def test_blow_ups_label(self, capsys):
        print_report(14, "s", self._make_params(), self._make_metrics(rmse_mae=2.0))
        assert "dominated by big blow-ups" in capsys.readouterr().out

    def test_select_score_in_output(self, capsys):
        print_report(14, "s", self._make_params(), self._make_metrics(select_score=0.1234))
        assert "0.1234" in capsys.readouterr().out