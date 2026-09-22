"""
Train, evaluate and log ONE Prophet configuration (no grid search).

Use cases
---------
* Baseline      : Prophet defaults for the tuned params, to show what tuning gains
* Manual test   : try a config by hand before adding it to the tuning grid
* Candidate     : optionally register it and let champion/challenger decide

Same pipeline as the rest of the project:
* data frames          -> src.models.prophet (build_daily / build_train_frame / build_future_frame)
* fixed params         -> configs/config.yaml : model.prophet.base_params
* fit / CV / score     -> src.models.prophet_tune (fit_prophet, score_config, select_score)
* MLflow server + exp. -> src.config.mlflow_tracking_uri() + config mlflow.experiment_name
* registry & promotion -> src.models.production

Run from the project root:
    python -m src.models.prophet_predict --horizon 14                      # baseline (defaults)
    python -m src.models.prophet_predict --horizon 30 --cps 0.1 --sps 1.0  # manual config
    python -m src.models.prophet_predict --horizon 14 --from-production    # re-evaluate @production params
    python -m src.models.prophet_predict --horizon 14 --cps 0.1 --register # candidate -> champion/challenger
"""

import argparse
import logging
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.prophet
import os

from mlflow import MlflowClient
from pathlib import Path
from src.config import load_config, mlflow_tracking_uri
from src.models.prophet import build_train_frame, build_future_frame, plot_forecast, TARGET
from src.api.model_loader import load_model
from src.helper.aws import save_forecast_data_to_s3

from src.models.prophet_tune import (
    BASE_PARAMS, PARAM_GRID, EXPERIMENT_NAME, 
    load_daily, fit_prophet, score_config, select_score, rescore_params,
)
from src.models.production import (
    PRODUCTION_ALIAS, get_version_by_alias, get_run_params,
    notify_api_reload, promote_if_better, registered_name,
)

# ---------------------------- VARIABLES ---------------------------
CONFIG = load_config()

DATA_SOURCE = os.getenv("NAPPECAST_DATA_SOURCE", "local")  # "s3" or "local"

# ---------------------------- LOGGING --------------------------------
logger = logging.getLogger(__name__)
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)

# Prophet's own defaults for the tuned params -> the "no tuning" baseline
PROPHET_DEFAULTS = {
    "changepoint_prior_scale": 0.05,
    "seasonality_prior_scale": 10.0,
    "changepoint_range": 0.8,
}

# ---------------------------------------------------------------------------
# 1. Which config?
# ---------------------------------------------------------------------------
def resolve_tuned_params(args) -> tuple[dict, str]:
    """Return (tuned params, source label). CLI values override the chosen base."""
    if args.from_production:
        client = MlflowClient()
        mv = get_version_by_alias(client, registered_name(args.horizon), PRODUCTION_ALIAS)
        if mv is None:
            raise SystemExit(f"No @{PRODUCTION_ALIAS} for H={args.horizon}")
        run_params = get_run_params(client, mv)
        tuned = {k: float(run_params[k]) for k in PARAM_GRID}
        source = f"production_v{mv.version}"
    else:
        tuned = dict(PROPHET_DEFAULTS)
        source = "prophet_defaults"

    overrides = {"changepoint_prior_scale": args.cps,
                 "seasonality_prior_scale": args.sps,
                 "changepoint_range": args.cpr}
    overrides = {k: v for k, v in overrides.items() if v is not None}
    if overrides:
        tuned.update(overrides)
        source = "manual" if source == "prophet_defaults" else f"{source}+manual"
    return tuned, source

# ---------------------------------------------------------------------------
# predict
# ---------------------------------------------------------------------------
def predict (H: int, save_csv: bool = False) -> tuple[dict, str]:
    daily = load_daily()
    future, _ = build_future_frame(daily, H)

    try:
        model = load_model(model='Prophet', horizon=H)
    except Exception as e:
        raise Exception(status_code=503, detail=f"Model unavailable: {e}")

    # forecast
    try:
        forecast = model.predict(future)
    except Exception as e:
        raise Exception(status_code=422, detail=f"Prediction failed: {e}")

    last_train = daily[daily[TARGET].notna()].index.max().strftime("%Y-%m-%d")
    forecast["ds"] = forecast["ds"].dt.strftime("%Y-%m-%d")
    forecast = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    if save_csv:
        save_forecast_data_to_s3(forecast, Path(CONFIG["paths"]["data"]["forecast"]), CONFIG["paths"]["forecast_filename"], False)

    return last_train, forecast
    

# ---------------------------------------------------------------------------
# 2. Train + evaluate + log
# ---------------------------------------------------------------------------
def train_and_log(daily, H: int, tuned: dict, source: str, register: bool) -> dict:
    df_prophet, regressor_cols = build_train_frame(daily, H)
    future, _ = build_future_frame(daily, H)
    params = {**BASE_PARAMS, **tuned}          # same merge as prophet_tune.py

    with mlflow.start_run(run_name=f"prophet-single-H{H}-{source}") as run:
        # Same param keys as the tuning best run -> readable by rescore_params / /train
        mlflow.log_params({**params, "horizon_days": H,
                           "last_train_date": str(df_prophet["ds"].max().date()),
                           "n_train_rows": len(df_prophet)})
        mlflow.set_tags({"horizon": str(H), "train_type": "single", "params_source": source})

        # CV metrics: same function + same score as the grid search -> comparable
        metrics = score_config(df_prophet, regressor_cols, params, H)
        metrics["select_score"] = float(select_score(
            metrics["rmse"], metrics["horizon_degradation"], metrics["rmse_mae"]))
        mlflow.log_metrics({k: float(v) for k, v in metrics.items()})

        # Final fit on all known data + forecast
        model = fit_prophet(df_prophet, regressor_cols, params)
        forecast = model.predict(future)

        # Figures: Prophet components view + interactive forecast (same plot as the app)
        fig1 = model.plot(forecast)
        plt.title(f"Groundwater level (m) - Prophet + lagged weather (H={H}d)")
        mlflow.log_figure(fig1, f"prediction_H{H}.png")
        plt.close(fig1)
        fig2 = plot_forecast(df_prophet, forecast, H, interval_width=model.interval_width)
        mlflow.log_figure(fig2, f"forecast_H{H}.html")

        info = {"run_id": run.info.run_id, "metrics": metrics, "version": None}

        if register:
            model_info = mlflow.prophet.log_model(
                pr_model=model, name="model",
                registered_model_name=registered_name(H),
            )
            info["version"] = str(model_info.registered_model_version)
            mlflow.set_tag("registered_version", info["version"])
        else:
            # Kept in the run (loadable with runs:/<run_id>/model) but NOT in the registry
            mlflow.prophet.log_model(pr_model=model, name="model")

    print_report(H, source, params, metrics)
    return info


def print_report(H, source, params, m):
    width = params["interval_width"]
    print(f"\n================ H={H}d  ({source}) ================")
    print("params          : " + ", ".join(f"{k}={params[k]}" for k in PARAM_GRID))
    print(f"RMSE / MAE      : {m['rmse']:.3f} / {m['mae']:.3f} m")
    print(f"R2              : {m['r2']:.3f}")
    print(f"RMSE / std(y)   : {m['rmse_std_ratio']:.2f}  ->",
          "strong" if m["rmse_std_ratio"] < 0.5 else
          "useful" if m["rmse_std_ratio"] < 0.8 else
          "weak" if m["rmse_std_ratio"] < 1.0 else "no better than the mean")
    print(f"RMSE / MAE      : {m['rmse_mae']:.2f}  ->",
          "errors uniform" if m["rmse_mae"] < 1.3 else
          "some large misses" if m["rmse_mae"] < 1.8 else "dominated by big blow-ups")
    print(f"degradation     : x{m['horizon_degradation']:.1f} across the horizon")
    print(f"select_score    : {m['select_score']:.4f}  (lower = better, same as tuning)")


# ---------------------------------------------------------------------------
# 3. Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Train/evaluate one Prophet config.")
    parser.add_argument("--horizon", type=int, choices=[14, 30], required=True)
    parser.add_argument("--cps", type=float, help="changepoint_prior_scale")
    parser.add_argument("--sps", type=float, help="seasonality_prior_scale")
    parser.add_argument("--cpr", type=float, help="changepoint_range")
    parser.add_argument("--from-production", action="store_true",
                        help="start from the params of the current @production model")
    parser.add_argument("--register", action="store_true",
                        help="register the model and run champion/challenger promotion")
    args = parser.parse_args()

    mlflow.set_tracking_uri(mlflow_tracking_uri())
    mlflow.set_experiment(EXPERIMENT_NAME)

    H = args.horizon
    daily = load_daily()
    tuned, source = resolve_tuned_params(args)
    info = train_and_log(daily, H, tuned, source, register=args.register)
    print(f"\nRun ID: {info['run_id']}")

    if args.register:
        decision = promote_if_better(
            name=registered_name(H),
            challenger_version=info["version"],
            challenger_score=info["metrics"]["select_score"],
            rescore_champion=lambda run_params: rescore_params(daily, H, run_params),
        )
        print(f"Promotion H={H}d: {decision}")
        if decision["promoted"]:
            notify_api_reload(H)


if __name__ == "__main__":
    main()
