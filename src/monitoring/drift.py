"""
Performance-drift monitoring for the NappeCast forecasts.
 
Principe
--------
Chaque matin le DAG écrit ses prévisions dans la table `forecast` (une ligne
par date prédite, avec `last_train` = date du dernier point observé). La vérité
terrain arrive ensuite jour après jour dans la table `processed`.
 
Ce module :
    1. joint `forecast` et `processed` -> une ligne = (prédiction, réalité)
    2. calcule le RMSE réel sur la fenêtre récente
    3. le compare au RMSE de validation croisée du modèle @production
       (journalisé dans MLflow au dernier ré-entraînement mensuel)
    4. produit un rapport HTML Evidently et journalise le tout dans MLflow
    5. renvoie un dict plat (XCom / JSON) avec un flag `drift_detected`
 
Référence = le modèle en production. On répond donc à la question
« le modèle fait-il pire en production qu'à sa propre validation ? », sans
confondre dégradation et saisonnalité.
 
Lancement :
    python -m src.monitoring.drift --horizon 14
    python -m src.monitoring.drift --horizon 30 --window-days 45 --no-mlflow
"""
 
from __future__ import annotations
 
import argparse
import logging
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
 
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
 
from src.config import load_config, mlflow_tracking_uri
 
# ---------------------------- CONFIG ---------------------------------
CONFIG = load_config()
 
DEFAULT_CODE_BSS = CONFIG["api"]["piezometer"]["code_bss"][0]
EXPERIMENT_NAME = CONFIG["mlflow"]["experiment_name"]
REPORTS_DIR = Path("reports/monitoring")
 
# Alerte si le RMSE observé dépasse de 25 % le RMSE de validation du modèle.
DRIFT_RMSE_RATIO = 1.5
 
# ---------------------------- LOGGING --------------------------------
logger = logging.getLogger(__name__)
 
 
# ---------------------------------------------------------------------
# 1. Données : la jointure prédiction / vérité terrain
# ---------------------------------------------------------------------
@lru_cache
def get_engine():
    """Un seul pool de connexions pour tout le module."""
    return create_engine(os.environ["NAPPECAST_BACKEND_STORE_URI"])
 
 
EVAL_FRAME_QUERY = text("""
    SELECT f.horizon,
           f.last_train,
           f.date_index,
           (f.date_index - f.last_train)  AS lead_time,
           f.yhat,
           f.yhat_lower,
           f.yhat_upper,
           p.niveau_nappe_eau             AS y_true
    FROM forecast f
    JOIN processed p
      ON p.code_bss   = f.code_bss
     AND p.date_index = f.date_index
    WHERE f.code_bss   = :code_bss
      AND f.horizon    = :horizon
      AND f.date_index >= :start_date
    ORDER BY f.date_index, f.last_train
""")
 
 
def read_eval_frame(code_bss: str, horizon: int, window_days: int) -> pd.DataFrame:
    """
    Prédictions déjà vérifiables sur les `window_days` derniers jours.
 
    Le JOIN interne fait le filtre de maturité : une prédiction dont la date
    cible n'est pas encore observée n'a pas de ligne dans `processed`.
    """
    start_date = (pd.Timestamp.today().normalize() - pd.Timedelta(days=window_days)).date()
 
    with get_engine().connect() as conn:
        df = pd.read_sql(
            EVAL_FRAME_QUERY,
            conn,
            params={"code_bss": code_bss, "horizon": horizon, "start_date": start_date},
        )
 
    df["date_index"] = pd.to_datetime(df["date_index"])
    df["lead_time"] = df["lead_time"].astype(int)
    return df
 
 
# ---------------------------------------------------------------------
# 2. Métriques
# ---------------------------------------------------------------------
def regression_metrics(df: pd.DataFrame) -> dict:
    """RMSE / MAE + biais + couverture de l'intervalle de prédiction."""
    err = df["yhat"] - df["y_true"]
    inside = (df["y_true"] >= df["yhat_lower"]) & (df["y_true"] <= df["yhat_upper"])
 
    return {
        "rmse": float(np.sqrt((err ** 2).mean())),
        "mae": float(err.abs().mean()),
        "bias": float(err.mean()),
        "coverage": float(inside.mean()),
    }
 
 
def reference_rmse(horizon: int) -> tuple[float, str]:
    """
    RMSE de validation croisée du modèle @production, et sa version.
 
    C'est la métrique que prophet_tune a journalisée lors du dernier
    ré-entraînement mensuel : la référence bouge avec le modèle.
    """
    import mlflow
    from mlflow import MlflowClient
 
    from src.models.production import PRODUCTION_ALIAS, get_version_by_alias, registered_name
 
    mlflow.set_tracking_uri(mlflow_tracking_uri())
    client = MlflowClient()
 
    mv = get_version_by_alias(client, registered_name(horizon), PRODUCTION_ALIAS)
    if mv is None:
        raise RuntimeError(f"Aucun modèle @{PRODUCTION_ALIAS} pour H={horizon}")
 
    rmse = client.get_run(mv.run_id).data.metrics["rmse"]
    return float(rmse), str(mv.version)
 
 
# ---------------------------------------------------------------------
# 3. Rapport Evidently (optionnel : le module fonctionne sans)
# ---------------------------------------------------------------------
def build_evidently_html(current: pd.DataFrame, out_path: Path) -> str | None:
    """
    Rapport de performance de régression sur la fenêtre courante.
 
    `lead_time` est déclaré comme feature numérique : Evidently produit alors
    la décomposition de l'erreur par lead_time (la courbe de dégradation).
    """
    try:
        from evidently import DataDefinition, Dataset, Regression, Report
        from evidently.presets import RegressionPreset
    except ImportError as e:  # pragma: no cover
        logger.warning("Evidently indisponible (%s) — rapport HTML ignoré.", e)
        return None
 
    definition = DataDefinition(
        numerical_columns=["lead_time"],
        regression=[Regression(target="y_true", prediction="yhat")],
    )
    dataset = Dataset.from_pandas(
        current[["y_true", "yhat", "lead_time"]], data_definition=definition
    )
 
    snapshot = Report(metrics=[RegressionPreset()]).run(current_data=dataset)
 
    out_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot.save_html(str(out_path))
    return str(out_path)
 
 
# ---------------------------------------------------------------------
# 4. Orchestration
# ---------------------------------------------------------------------
def run_performance_report(
    horizon: int,
    code_bss: str = DEFAULT_CODE_BSS,
    window_days: int | None = None,
    log_mlflow: bool = True,
) -> dict:
    """
    Compare l'erreur réelle récente au RMSE de validation du modèle @production.
    Un même jour est prédit H fois, par les H runs qui l'ont précédé, à des échéances 
    (lead_time) différentes. 
    La fenêtre sélectionne des DATES CIBLES, pas des runs : sur window_days=14
    avec H=14, on obtient 14 jours x 14 prédictions ≈ 196 lignes, et un seul
    RMSE calculé sur l'ensemble.
    Retourne un dict JSON. 
    """
    window_days = window_days or horizon
    df = read_eval_frame(code_bss, horizon, window_days)
 
    if len(df) < horizon:
        logger.warning("H=%d : seulement %d prédictions mûres", horizon, len(df))
        return {
            "status": "insufficient_data",
            "horizon": horizon,
            "code_bss": code_bss,
            "n_rows": len(df),
            "drift_detected": False,
        }
 
    metrics = regression_metrics(df)
    ref_rmse, model_version = reference_rmse(horizon)
    rmse_ratio = metrics["rmse"] / ref_rmse
 
    html_path = build_evidently_html(
        df, REPORTS_DIR / f"perf_H{horizon}_{datetime.now():%Y%m%d}.html"
    )
 
    result = {
        "status": "ok",
        "horizon": horizon,
        "code_bss": code_bss,
        "model_version": model_version,
        "window_days": window_days,
        "n_rows": len(df),
        "window_start": df["date_index"].min().strftime("%Y-%m-%d"),
        "window_end": df["date_index"].max().strftime("%Y-%m-%d"),
        **metrics,
        "reference_rmse": ref_rmse,
        "rmse_ratio": float(rmse_ratio),
        "drift_threshold": DRIFT_RMSE_RATIO,
        "drift_detected": bool(rmse_ratio > DRIFT_RMSE_RATIO),
        "report_path": html_path,
    }
 
    if log_mlflow:
        _log_to_mlflow(result, html_path)
 
    return result
 
 
def _log_to_mlflow(result: dict, html_path: str | None) -> None:
    """Une run par exécution : MLflow trace ainsi la série temporelle du RMSE."""
    try:
        import mlflow
 
        mlflow.set_tracking_uri(mlflow_tracking_uri())
        mlflow.set_experiment(EXPERIMENT_NAME)
 
        H = result["horizon"]
        with mlflow.start_run(run_name=f"monitoring-H{H}-{result['window_end']}"):
            mlflow.set_tags({
                "horizon": str(H),
                "train_type": "monitoring",
                "model_version": result["model_version"],
            })
            mlflow.log_params({
                "window_days": result["window_days"],
                "drift_threshold": DRIFT_RMSE_RATIO,
            })
            mlflow.log_metrics({
                k: float(result[k]) for k in
                ("rmse", "mae", "bias", "coverage", "reference_rmse", "rmse_ratio")
            })
            mlflow.log_metric("drift_detected", int(result["drift_detected"]))
            if html_path:
                mlflow.log_artifact(html_path)
    except Exception as e:  # le monitoring ne doit jamais casser le DAG
        logger.warning("Journalisation MLflow échouée : %s", e)
 
 
# ---------------------------------------------------------------------
# 5. CLI
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Monitoring de la performance des prévisions.")
    parser.add_argument("--horizon", type=int, choices=[14, 30], required=True)
    parser.add_argument("--code-bss", default=DEFAULT_CODE_BSS)
    parser.add_argument("--window-days", type=int, default=None)
    parser.add_argument("--no-mlflow", action="store_true")
    args = parser.parse_args()
 
    logging.basicConfig(level=logging.INFO, format=CONFIG["system"]["logging_format"])
 
    result = run_performance_report(
        horizon=args.horizon,
        code_bss=args.code_bss,
        window_days=args.window_days,
        log_mlflow=not args.no_mlflow,
    )
 
    for k, v in result.items():
        print(f"{k:18}: {v}")
 
 
if __name__ == "__main__":
    main()
