import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import mlflow
import mlflow.prophet
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# 1. Training dataset
# ---------------------------------------------------------------------------

# Loading the dataframe
input_path = Path("../..") / 'data' / 'processed' / 'dataset_processed.csv'
dataset = pd.read_csv(input_path)
dataset = dataset.set_index("date_index", drop=False)
dataset.index = pd.to_datetime(dataset.index)
df_daily = dataset.copy()

TARGET = "niveau_nappe_eau"
DAILY_FEATURES = [
    "shortwave_radiation_sum", "et0_fao_evapotranspiration",
    "soil_temperature_0_to_100cm_mean",
    "P_cum_90d", "Peff_cum_90d",
    "Temperature_mean_90d",
]
daily = df_daily[[TARGET] + DAILY_FEATURES].groupby(level=0).mean()
assert not (set(DAILY_FEATURES) - set(df_daily.columns)), \
    f"missing features: {set(DAILY_FEATURES) - set(df_daily.columns)}"

# ---------------------------------------------------------------------------
# 2. Entraînement + tracking MLflow
# ---------------------------------------------------------------------------
def interpret_prophet(df_cv, y_train, label="model"):
        """
        df_cv     : output of prophet.cross_validation (needs y, yhat, *_lower/upper, cutoff, ds)
        y_train   : the training target series (df_prophet['y']) — sets the scale baseline
        target_interval : the interval_width you passed to Prophet (for coverage check)
        """
        perf = performance_metrics(df_cv)                     # horizon-bucketed table
        rmse, mae = perf["rmse"].mean(), perf["mae"].mean()   # avg across horizons
        std_y = y_train.std()

        # --- scale-normalized skill vs. "predict the mean" ---
        rmse_ratio   = rmse / std_y                           # <1 good, ~1 worthless
        rmse_mae     = rmse / mae                             # ~1 uniform, >>1 = big blow-ups

        # R2: coefficient of determination
        ss_res = np.sum((df_cv["y"] - df_cv["yhat"])**2)
        ss_tot = np.sum((df_cv["y"] - df_cv["y"].mean())**2)
        r2 = 1 - ss_res/ss_tot

        print(f"\n================ {label} ================")
        print(f"RMSE            : {rmse:.3f}   (target unit)")
        print(f"MAE             : {mae:.3f}   (typical error, target unit)")
        print(f"std(y)          : {std_y:.3f}")
        print(f"R2              : {r2:.3f}")
        print(f"RMSE / std(y)   : {rmse_ratio:.2f}  ->", 
            "strong" if rmse_ratio < 0.5 else
            "useful" if rmse_ratio < 0.8 else
            "weak"   if rmse_ratio < 1.0 else "no better than the mean")
        print(f"RMSE / MAE      : {rmse_mae:.2f}  ->",
            "errors uniform" if rmse_mae < 1.3 else
            "some large misses" if rmse_mae < 1.8 else "dominated by big blow-ups")

        # --- horizon read: does error grow, and how fast? ---
        first, last = perf.iloc[0], perf.iloc[-1]
        print(f"RMSE @ {first['horizon']}  : {first['rmse']:.3f}")
        print(f"RMSE @ {last['horizon']}   : {last['rmse']:.3f}   "
            f"(x{last['rmse']/first['rmse']:.1f} degradation across horizon)")

        return r2, std_y, rmse_ratio, rmse_mae


def train_and_log(daily: pd.DataFrame) -> str:
    mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME"))

    #  Future-aware lagged regressors: Extends the date range by 30 days 
    H = 30                                    # days ahead == lag 
    period = 90
    future_idx = pd.date_range(daily.index.min(), periods=len(daily) + H, freq="D")
    df_ext = daily.reindex(future_idx)        # H new empty rows at the end
    # shifting values forward by 30 days
    for col in DAILY_FEATURES:
        df_ext[f"{col}_lag{H}"] = df_ext[col].shift(H)   # observed value pulled forward
    regressor_cols = [f"{col}_lag{H}" for col in DAILY_FEATURES]

    #  single frame: ds, y, lagged regressors
    df_all = pd.DataFrame({"ds": df_ext.index, "y": df_ext[TARGET].values})
    for col in regressor_cols:
        df_all[col] = df_ext[col].values

    # Train = y known and all regressors known
    df_prophet = df_all.dropna(subset=["y"] + regressor_cols).reset_index(drop=True)
    # Predict frame: regressors known (history + H forecast days)
    future = df_all[["ds"] + regressor_cols].dropna(subset=regressor_cols).reset_index(drop=True)

    params = {
        "seasonality_mode": "additive",
        "weekly_seasonality": False,
        "daily_seasonality":False,
        "yearly_seasonality":True, 
        "interval_width":0.80,
        "changepoint_prior_scale":0.05
    }

    with mlflow.start_run(run_name="prophet-forecast") as run:
        mlflow.log_params(params)
        mlflow.log_params({                    # backtest / setup config
            "horizon": f"{H} days",
            "cv_period": f"{period} days",
            "cv_initial_frac": 0.8,
        })
        # Fit
        model = Prophet(**params)
        for col in regressor_cols:
            model.add_regressor(col)
        model.fit(df_prophet)

        # 5. Forecast
        forecast = model.predict(future)

        # 6. Rolling backtest (calendar days)
        n_days = (df_prophet.ds.max() - df_prophet.ds.min()).days
        df_cv = cross_validation(model, horizon=f"{H} days", period=f"{period} days",
                                initial=f"{int(n_days * 0.8)} days")

        metrics_df = performance_metrics(df_cv)
        r2, std_y, rmse_ratio, rmse_mae = interpret_prophet(df_cv, df_prophet["y"])
        mlflow.log_metrics({
            "rmse": metrics_df["rmse"].mean(),
            "mae": metrics_df["mae"].mean(),
            "mape": metrics_df["mape"].mean(),
            "r2": r2,
            "std_y": std_y,
            "rmse_std_ratio": rmse_ratio,
            "rmse_mae": rmse_mae,
        })
  

        mlflow.prophet.log_model(
            pr_model=model,
            name="prophet-forecast"
        )

        print(f"Run ID: {run.info.run_id}")
        print(f"RMSE moyen (CV): {metrics_df['rmse'].mean():.3f}")
        print(f"R2 (CV): {r2:.3f}")

        # --- visualize ---
        fig1 = model.plot(forecast); plt.title(f"Groundwater level (m) -  Prophet + lagged weather (H={H}d)")
        mlflow.log_figure(fig1, "prediction.png")


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
                        color="#d62728", alpha=0.18, label="95% interval")
        ax.axvline(last_train, ls="--", color="gray", lw=1)
        ax.set_title(f"Groundwater level — Prophet forecast (H={H} days)", fontweight="bold")
        ax.set_xlabel("Date"); ax.set_ylabel("Groundwater level (m)")
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.set_xlim(pd.Timestamp("2026-01-01"), fut["ds"].max())
        ax.legend(loc="upper left", framealpha=0.9)
        fig2.autofmt_xdate(); 
        mlflow.log_figure(fig2, "forecast.png")

        return run.info.run_id

if __name__ == "__main__":
    run_id = train_and_log(daily)
    print(run_id)