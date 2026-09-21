# tests/test_production.py

import pytest
from unittest.mock import patch, MagicMock, call

from src.models.production import (
    registered_name,
    get_version_by_alias,
    get_run_metric,
    get_run_params,
    promote,
    promote_if_better,
    rollback,
)


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

def _make_model_version(version: str, run_id: str = "run_abc") -> MagicMock:
    mv = MagicMock()
    mv.version = version
    mv.run_id  = run_id
    return mv


# ─────────────────────────────────────────────
# registered_name
# ─────────────────────────────────────────────

class TestRegisteredName:

    def test_returns_string(self):
        result = registered_name(14)
        assert isinstance(result, str)

    def test_horizon_in_name(self):
        assert "14" in registered_name(14)
        assert "30" in registered_name(30)


# ─────────────────────────────────────────────
# get_version_by_alias
# ─────────────────────────────────────────────

class TestGetVersionByAlias:

    def test_returns_model_version(self):
        client = MagicMock()
        mv = _make_model_version("3")
        client.get_model_version_by_alias.return_value = mv
        result = get_version_by_alias(client, "my_model", "production")
        assert result is mv

    def test_returns_none_on_mlflow_exception(self):
        from mlflow.exceptions import MlflowException
        client = MagicMock()
        client.get_model_version_by_alias.side_effect = MlflowException("not found")
        result = get_version_by_alias(client, "my_model", "production")
        assert result is None


# ─────────────────────────────────────────────
# get_run_metric
# ─────────────────────────────────────────────

class TestGetRunMetric:

    def test_returns_metric_value(self):
        client = MagicMock()
        client.get_run.return_value.data.metrics = {"select_score": 0.42}
        mv = _make_model_version("1")
        result = get_run_metric(client, mv, "select_score")
        assert result == 0.42

    def test_returns_none_if_metric_absent(self):
        client = MagicMock()
        client.get_run.return_value.data.metrics = {}
        mv = _make_model_version("1")
        result = get_run_metric(client, mv, "select_score")
        assert result is None


# ─────────────────────────────────────────────
# get_run_params
# ─────────────────────────────────────────────

class TestGetRunParams:

    def test_returns_params_dict(self):
        client = MagicMock()
        client.get_run.return_value.data.params = {"changepoint_prior_scale": "0.1"}
        mv = _make_model_version("1")
        result = get_run_params(client, mv)
        assert result == {"changepoint_prior_scale": "0.1"}


# ─────────────────────────────────────────────
# promote
# ─────────────────────────────────────────────

class TestPromote:

    def test_sets_production_alias(self):
        client = MagicMock()
        promote(client, "my_model", "5", None, "first run")
        client.set_registered_model_alias.assert_called_with("my_model", "production", "5")

    def test_saves_previous_champion(self):
        client = MagicMock()
        old = _make_model_version("3")
        promote(client, "my_model", "5", old, "beats champion")
        calls = client.set_registered_model_alias.call_args_list
        # Premier appel : sauvegarde du champion précédent
        assert calls[0] == call("my_model", "previous_production", "3")
        # Deuxième appel : promotion du challenger
        assert calls[1] == call("my_model", "production", "5")

    def test_no_previous_alias_if_no_old(self):
        client = MagicMock()
        promote(client, "my_model", "1", None, "first")
        # set_registered_model_alias appelé une seule fois (production uniquement)
        assert client.set_registered_model_alias.call_count == 1

    def test_sets_promotion_reason_tag(self):
        client = MagicMock()
        promote(client, "my_model", "5", None, "my reason")
        client.set_model_version_tag.assert_called_once_with(
            "my_model", "5", "promotion_reason", "my reason"
        )


# ─────────────────────────────────────────────
# promote_if_better
# ─────────────────────────────────────────────

class TestPromoteIfBetter:

    def _base_client(self, champion_version=None, champion_score=None):
        """Client MLflow mocké avec un champion optionnel."""
        client = MagicMock()
        if champion_version is None:
            client.get_model_version_by_alias.return_value = None
        else:
            mv = _make_model_version(str(champion_version))
            # production -> champion, challenger -> None par défaut
            client.get_model_version_by_alias.side_effect = lambda name, alias: (
                mv if alias == "production" else None
            )
            client.get_run.return_value.data.metrics = {"select_score": champion_score}
            client.get_run.return_value.data.params  = {}
        return client

    @patch("src.models.production.MlflowClient")
    def test_no_champion_promotes_directly(self, MockClient):
        MockClient.return_value = self._base_client(champion_version=None)
        result = promote_if_better("my_model", "1", challenger_score=0.5)
        assert result["promoted"] is True
        assert result["champion_version"] is None

    @patch("src.models.production.MlflowClient")
    def test_same_version_no_promotion(self, MockClient):
        client = self._base_client(champion_version=3, champion_score=0.4)
        MockClient.return_value = client
        result = promote_if_better("my_model", "3", challenger_score=0.4)
        assert result["promoted"] is False

    @patch("src.models.production.MlflowClient")
    def test_challenger_better_promotes(self, MockClient):
        MockClient.return_value = self._base_client(champion_version=2, champion_score=0.5)
        # 0.38 < 0.5 * (1 - 0.02) = 0.49 → promotion
        result = promote_if_better("my_model", "3", challenger_score=0.38)
        assert result["promoted"] is True
        assert result["champion_version"] == "2"

    @patch("src.models.production.MlflowClient")
    def test_challenger_marginally_better_no_promotion(self, MockClient):
        MockClient.return_value = self._base_client(champion_version=2, champion_score=0.5)
        # 0.495 > threshold 0.49 → pas de promotion (gain < 2 %)
        result = promote_if_better("my_model", "3", challenger_score=0.495)
        assert result["promoted"] is False

    @patch("src.models.production.MlflowClient")
    def test_rescore_champion_called(self, MockClient):
        MockClient.return_value = self._base_client(champion_version=2, champion_score=0.5)
        rescore = MagicMock(return_value=0.5)
        promote_if_better("my_model", "3", challenger_score=0.38, rescore_champion=rescore)
        rescore.assert_called_once()

    @patch("src.models.production.MlflowClient")
    def test_champion_no_score_promotes(self, MockClient):
        """Champion sans select_score → promotion automatique."""
        client = self._base_client(champion_version=2, champion_score=None)
        # get_run retourne un dict vide pour metrics
        client.get_run.return_value.data.metrics = {}
        MockClient.return_value = client
        result = promote_if_better("my_model", "3", challenger_score=0.4)
        assert result["promoted"] is True
        assert result["champion_score"] is None


# ─────────────────────────────────────────────
# rollback
# ─────────────────────────────────────────────

class TestRollback:

    @patch("src.models.production.MlflowClient")
    def test_rollback_swaps_aliases(self, MockClient):
        client = MagicMock()
        MockClient.return_value = client

        previous = _make_model_version("2")
        current  = _make_model_version("3")
        client.get_model_version_by_alias.side_effect = lambda name, alias: (
            current  if alias == "production"          else
            previous if alias == "previous_production" else None
        )

        rollback("my_model")

        # previous -> production
        client.set_registered_model_alias.assert_any_call("my_model", "production", "2")
        # current -> previous_production
        client.set_registered_model_alias.assert_any_call("my_model", "previous_production", "3")

    @patch("src.models.production.MlflowClient")
    def test_rollback_raises_if_no_previous(self, MockClient):
        client = MagicMock()
        MockClient.return_value = client
        client.get_model_version_by_alias.return_value = None
        with pytest.raises(RuntimeError, match="nothing to roll back"):
            rollback("my_model")