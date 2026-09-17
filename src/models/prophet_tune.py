"""
Prophet hyperparameter tuning for groundwater-level forecasting.

Grid-searches changepoint_prior_scale (trend flexibility),
seasonality_prior_scale (seasonal amplitude regularization) and
changepoint_range, separately for each forecast horizon H.

Selection objective: minimize mean cross-validation RMSE across the horizon,
while surfacing robustness signals (RMSE/MAE spread and error growth across the
horizon) so a flexible-but-not-overfit config can be chosen.

Run:
    python prophet_tune.py

Notes
-----
* The lagged regressors are shifted by H, so the *feature set changes with H*.
  Tuning is therefore repeated independently for each horizon.
* Prophet defaults for reference: changepoint_prior_scale=0.05,
  seasonality_prior_scale=10, changepoint_range=0.8.
"""

import os
import logging
import itertools
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import mlflow
from mlflow import MlflowClient
import mlflow.prophet
from prophet import Prophet
from src.models.prophet import (build_train_frame,
                                build_future_frame,
                                build_daily,
                                plot_forecast)
from prophet.diagnostics import cross_validation, performance_metrics
from dotenv import load_dotenv

from src.config import load_config, mlflow_tracking_uri, PROJECT_ROOT
from src.models.production import promote_if_better, registered_name, notify_api_reload

load_dotenv()
CONFIG = load_config()
# NB: no module-level MlflowClient() -> it would be created before
# mlflow.set_tracking_uri() in main() and could point to the wrong server.

# Quiet Prophet / cmdstanpy chatter during the grid search
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)

# ---------------------------------------------------------------------------
# 0. Config
# ---------------------------------------------------------------------------
# Absolute path -> works whatever the working directory (run from project root:
# python -m src.models.prophet_tune)
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "dataset_processed.csv"
RESULTS_DIR = Path(__file__).resolve().parent

TARGET = "niveau_nappe_eau"
DAILY_FEATURES = [
    "shortwave_radiation_sum", "et0_fao_evapotranspiration",
    "soil_temperature_0_to_100cm_mean",
    "P_cum_90d", "Peff_cum_90d",
    "Temperature_mean_90d",
]

# Horizons to tune (days). Feature lag == H, so each is tuned separately.
HORIZONS = [14, 30]

# CV backtest setup
CV_PERIOD = 45          # days between successive CV cutoffs
CV_INITIAL_FRAC = 0.8   # fraction of the series used before the first cutoff
CV_PARALLEL = "processes"

# Fixed Prophet params (not tuned)
# Single definition in configs/config.yaml (also used by API /train)
BASE_PARAMS = dict(CONFIG["model"]["prophet"]["base_params"])

# ---- Tuning grid ----------------------------------------------------------
# Trimmed vs. the reference paper: CPS denser in the useful low region, SPS
# spanning both sides of Prophet's default (10), changepoint_range <= 0.9 to
# avoid overfitting the extrapolation tail.
PARAM_GRID = {
    "changepoint_prior_scale": [0.01, 0.05, 0.1, 0.3, 0.5], # [0.1, 0.3, 0.5, 0.7],
    "seasonality_prior_scale": [0.1, 1.0, 10.0], # [0.05, 0.1, 1.0, 10.0]
    "changepoint_range":       [0.8],#[0.8, 0.9],
}
# --- Selection penalty (RMSE + robustness) ---
# score = rmse, inflated when error grows across the horizon (degradation)
# or when a few big misses dominate (rmse_mae). 0 = ignore that penalty.
LAMBDA_DEGRADATION = 0.4    # weight on horizon error growth
LAMBDA_SPREAD      = 0.3    # weight on RMSE/MAE blow-up ratio

EXPERIMENT_NAME = CONFIG["mlflow"]["experiment_name"]

# ---------------------------------------------------------------------------
# 1. Data
# ---------------------------------------------------------------------------
def load_daily() -> pd.DataFrame:
    dataset = pd.read_csv(INPUT_PATH)
    daily = build_daily(dataset)
    return daily


# ---------------------------------------------------------------------------
# 2. Fit + score one config
# ---------------------------------------------------------------------------
def fit_prophet(df_prophet, regressor_cols, params):
    model = Prophet(**params)
    for col in regressor_cols:
        model.add_regressor(col)
    model.fit(df_prophet)
    return model


def score_config(df_prophet, regressor_cols, params, H):
    """Fit, cross-validate, and return a metrics dict for one param combo."""
    model = fit_prophet(df_prophet, regressor_cols, params)

    n_days = (df_prophet.ds.max() - df_prophet.ds.min()).days
    initial = f"{int(n_days * CV_INITIAL_FRAC)} days"

    df_cv = cross_validation(
        model, horizon=f"{H} days", period=f"{CV_PERIOD} days",
        initial=initial, parallel=CV_PARALLEL,
    )
    perf = performance_metrics(df_cv)

    rmse = perf["rmse"].mean()
    mae = perf["mae"].mean()
    mape = perf["mape"].mean()          # fraction, not %, in Prophet's output
    std_y = df_prophet["y"].std()

    ss_res = np.sum((df_cv["y"] - df_cv["yhat"]) ** 2)
    ss_tot = np.sum((df_cv["y"] - df_cv["y"].mean()) ** 2)
    r2 = 1 - ss_res / ss_tot

    first, last = perf.iloc[0], perf.iloc[-1]
    degradation = last["rmse"] / first["rmse"]   # error growth across horizon

    return {
        "rmse": rmse,
        "mae": mae,
        "mape": mape,
        "std_y": std_y,
        "r2": r2,
        "rmse_std_ratio": rmse / std_y,          # <1 beats "predict the mean"
        "rmse_mae": rmse / mae,                   # ~1 uniform, >>1 big blow-ups
        "horizon_degradation": degradation,      # robustness signal
        # share of observations inside [yhat_lower, yhat_upper]; calibrated if ~= interval_width
        "coverage": float(((df_cv["y"] >= df_cv["yhat_lower"]) &
                           (df_cv["y"] <= df_cv["yhat_upper"])).mean()),
    }


def select_score(rmse, horizon_degradation, rmse_mae):
    """
    Penalized RMSE (lower = better). Single definition, used both for the grid
    search and to re-score the production champion -> identical criterion.
    Works on floats and on pandas Series.
    """
    deg_pen = np.clip(horizon_degradation - 1, 0, None)
    spread_pen = np.clip(rmse_mae - 1, 0, None)
    return rmse * (1 + LAMBDA_DEGRADATION * deg_pen) * (1 + LAMBDA_SPREAD * spread_pen)


def rescore_params(daily, H, run_params: dict) -> float:
    """
    Re-run the CV of a past model's hyperparameters on TODAY's data.
    run_params comes from MLflow, where every param is stored as a string.
    """
    df_prophet, regressor_cols = build_train_frame(daily, H)
    tuned = {k: float(run_params[k]) for k in PARAM_GRID}   # "0.05" -> 0.05
    params = {**BASE_PARAMS, **tuned}
    m = score_config(df_prophet, regressor_cols, params, H)
    return float(select_score(m["rmse"], m["horizon_degradation"], m["rmse_mae"]))


# ---------------------------------------------------------------------------
# 3. Grid search for one horizon
# ---------------------------------------------------------------------------
def tune_horizon(daily, H) -> pd.DataFrame:
    df_prophet, regressor_cols = build_train_frame(daily, H)

    keys = list(PARAM_GRID.keys())
    combos = list(itertools.product(*PARAM_GRID.values()))
    print(f"\n=== Tuning H={H}d : {len(combos)} configs, "
          f"{len(df_prophet)} training rows ===")

    rows = []
    with mlflow.start_run(run_name=f"prophet-forecast-H{H}") as parent:
        mlflow.log_params({
            "horizon_days": H,
            "cv_period_days": CV_PERIOD,
            "cv_initial_frac": CV_INITIAL_FRAC,
            "n_configs": len(combos),
        })

        for i, values in enumerate(combos, 1):
            tuned = dict(zip(keys, values))
            params = {**BASE_PARAMS, **tuned}
            try:
                metrics = score_config(df_prophet, regressor_cols, params, H)
            except Exception as e:                 # a bad combo shouldn't kill the sweep
                print(f"  [{i}/{len(combos)}] {tuned} -> FAILED: {e}")
                continue

            with mlflow.start_run(run_name=f"prophet-forecast-H{H}-cfg{i}", nested=True):
                mlflow.log_params({f"grid_{k}": v for k, v in tuned.items()})   # the swept config
                mlflow.log_params({**BASE_PARAMS, "horizon_days": H})           # the fixed context
                mlflow.log_metrics(metrics)

            print(f"  [{i}/{len(combos)}] {tuned} "
                  f"-> RMSE={metrics['rmse']:.3f}  R2={metrics['r2']:.3f}  "
                  f"degr=x{metrics['horizon_degradation']:.1f}")
            rows.append({"horizon": H, **tuned, **metrics})

        #compute score with (RMSE + robustness) penalty
        # select_score: RMSE penalized when error grows across the horizon
        # (degradation>1) or is driven by a few big misses (rmse_mae>1) — lowest wins.
        results = pd.DataFrame(rows)
        results["select_score"] = select_score(
            results["rmse"], results["horizon_degradation"], results["rmse_mae"]
        )
        results = results.sort_values("select_score").reset_index(drop=True)
        mlflow.log_metric("best_cv_rmse", results.iloc[0]["rmse"])

    return results


# ---------------------------------------------------------------------------
# 4. Refit + log the winning config for a horizon
# ---------------------------------------------------------------------------
def refit_best(daily, H, best_row):
    future, regressor_cols = build_future_frame(daily, H)
    df_prophet, regressor_cols = build_train_frame(daily, H)

    tuned = {k: best_row[k] for k in PARAM_GRID}
    params = {**BASE_PARAMS, **tuned}

    model_name = registered_name(H)          # "nappecast_Prophet_h14" (same as the API)

    with mlflow.start_run(run_name=f"prophet-forecast-best-H{H}") as run:
        mlflow.log_params({**params, "horizon_days": H})
        model = fit_prophet(df_prophet, regressor_cols, params)
        forecast = model.predict(future)

        mlflow.log_metrics({
            k: float(best_row[k]) for k in
            ["rmse", "mae", "r2", "rmse_std_ratio", "rmse_mae", "coverage",
             "horizon_degradation", "select_score"]      # select_score = promotion criterion
        })
        mlflow.set_tags({"horizon": str(H), "train_type": "tuning"})

        # log_model with registered_model_name -> creates a NEW VERSION in the registry
        # (the registered model itself is created on the first call)
        model_info = mlflow.prophet.log_model(
            pr_model=model,
            name="model",                        # artifact folder inside the run
            registered_model_name=model_name,    # registry entry read by the API
        )
        version = str(model_info.registered_model_version)
        mlflow.set_tag("registered_version", version)
        print(f"Registered {model_name} v{version} (run {run.info.run_id})")

        # --- forecast figure ---

        # TODO: sortir la fonction de plot dans une fonction a part

        fig1 = model.plot(forecast); plt.title(f"Groundwater level (m) -  Prophet + lagged weather (H={H}d)")
        mlflow.log_figure(fig1, f"prediction_best_H{H}.png")
        plt.close(fig1) 

        plt.rcParams.update({
            "figure.dpi": 120, "axes.grid": True, "grid.alpha": 0.3,
            "axes.spines.top": False, "axes.spines.right": False,
            "font.size": 11,
        })
        # forecast at the last training date
        last_train = df_prophet.ds.max()
        hist = forecast[forecast.ds <= last_train]
        fut = forecast[forecast.ds > last_train]

        fig2, ax = plt.subplots(figsize=(10,6))
        ax.plot(df_prophet.ds, df_prophet.y, ".", color="#0f5792", ms=6,            # observed ground truth
                label="Observed")
        ax.plot(hist.ds, hist.yhat, ".", color="#d6272789", ms=6,           # prediction on history
                label=f"Prediction")
        ax.plot(fut.ds, fut.yhat, "-", color="#d62728", lw=2.5,         # forecast horizon
                label=f"Forecast (+{H}d)")
        ax.fill_between(fut.ds, fut.yhat_lower, fut.yhat_upper,             # uncertainty band
                        color="#d62728", alpha=0.18,
                        label=f"{model.interval_width:.0%} interval")
        ax.axvline(last_train, ls="--", color="gray", lw=1)
        ax.set_title(f"Groundwater level — Prophet forecast (H={H} days)", fontweight="bold")
        ax.set_xlabel("Date"); ax.set_ylabel("Groundwater level (m)")
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.set_xlim(pd.Timestamp("2026-01-01"), fut["ds"].max())
        ax.legend(loc="upper left", framealpha=0.9)
        fig2.autofmt_xdate(); 
        mlflow.log_figure(fig2, f"forecast_best_H{H}.png")
        plt.close(fig2)

    return {"name": model_name, "version": version, "run_id": run.info.run_id,
            "select_score": float(best_row["select_score"])}


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------
def main():
    mlflow.set_tracking_uri(mlflow_tracking_uri())
    mlflow.set_experiment(EXPERIMENT_NAME)

    daily = load_daily()
    all_results = []

    for H in HORIZONS:
        results = tune_horizon(daily, H)
        out_csv = RESULTS_DIR / f"tuning_results_H{H}.csv"
        results.to_csv(out_csv, index=False)
        all_results.append(results)

        print(f"\n----- Top 5 configs for H={H}d (by CV RMSE) -----")
        cols = ["changepoint_prior_scale", "seasonality_prior_scale",
                "changepoint_range", "rmse", "mae", "r2", "mape",
                "rmse_mae", "horizon_degradation", "select_score"]
        print(results[cols].head().to_string(index=False))

        best = results.iloc[0]
        print(f"\nBest H={H}d: CPS={best['changepoint_prior_scale']}, "
              f"SPS={best['seasonality_prior_scale']}, "
              f"cp_range={best['changepoint_range']}  ->  RMSE={best['rmse']:.3f}")
        challenger = refit_best(daily, H, best)

        # Champion / challenger: the champion is re-scored on the SAME data and
        # CV folds as the challenger, with the SAME select_score formula.
        decision = promote_if_better(
            name=challenger["name"],
            challenger_version=challenger["version"],
            challenger_score=challenger["select_score"],
            rescore_champion=lambda run_params, H=H: rescore_params(daily, H, run_params),
        )
        print(f"Promotion H={H}d: {decision}")
        if decision["promoted"]:
            notify_api_reload(H)

    combined = pd.concat(all_results, ignore_index=True)
    combined.to_csv(RESULTS_DIR / "tuning_results_all.csv", index=False)
    print("\nSaved: tuning_results_H14.csv, tuning_results_H30.csv, tuning_results_all.csv")


if __name__ == "__main__":
    main()
