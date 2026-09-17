"""
Smoke test of the production models in the MLflow Model Registry.

For each horizon, checks that:
  1. the aliases resolve (@production is mandatory, the others are informative)
  2. models:/<name>@production loads exactly like in the API
  3. the loaded model carries the hyperparameters logged in its MLflow run
  4. its regressors match the features expected for this horizon
  5. it predicts H future days without NaN, with coherent intervals
  6. (info) whether the production config equals the latest tuning best
  7. (optional, --api) the API serves the same version

Run from the project root:
    python -m src.models.test_best
    python -m src.models.test_best --horizon 14
    python -m src.models.test_best --api        # also query the deployed API

Exit code 0 = all checks passed, 1 = at least one failure (usable in CI / Airflow).
"""

import argparse
import os
import sys

import mlflow
import mlflow.prophet
import numpy as np
import pandas as pd
from mlflow import MlflowClient

from src.config import load_config, PROJECT_ROOT
from src.models.prophet import build_daily, build_future_frame, build_train_frame
from src.models.production import (
    PRODUCTION_ALIAS, CHALLENGER_ALIAS, PREVIOUS_ALIAS, SCORE_METRIC,
    get_version_by_alias, get_run_metric, registered_name,
)

CONFIG = load_config()
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "dataset_processed.csv"
TUNING_DIR = PROJECT_ROOT / "src" / "models"
TUNED_KEYS = ["changepoint_prior_scale", "seasonality_prior_scale", "changepoint_range"]


class Checker:
    """Collects PASS/FAIL lines instead of stopping at the first error."""
    def __init__(self):
        self.failures = 0

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  ({detail})" if detail else ""))
        self.failures += not ok
        return ok

    @staticmethod
    def info(label: str):
        print(f"  [INFO] {label}")


def test_horizon(H: int, daily: pd.DataFrame, client: MlflowClient, c: Checker, api_url=None):
    name = registered_name(H)
    print(f"\n=== {name} (H={H}d) ===")

    # 1. Aliases -------------------------------------------------------------
    for alias in (CHALLENGER_ALIAS, PREVIOUS_ALIAS):
        mv = get_version_by_alias(client, name, alias)
        c.info(f"@{alias}: " + (f"v{mv.version}" if mv else "-"))

    prod = get_version_by_alias(client, name, PRODUCTION_ALIAS)
    if not c.check(prod is not None, f"@{PRODUCTION_ALIAS} exists"):
        return                                   # nothing else can be tested
    run = client.get_run(prod.run_id)
    score = get_run_metric(client, prod, SCORE_METRIC)
    c.info(f"@{PRODUCTION_ALIAS} -> v{prod.version}, run {prod.run_id}, "
           f"{SCORE_METRIC}={score}, reason={prod.tags.get('promotion_reason', '-')}")

    # 2. Load exactly like src/api/model_loader.py ---------------------------
    uri = f"models:/{name}@{PRODUCTION_ALIAS}"
    try:
        model = mlflow.prophet.load_model(uri)
    except Exception as e:
        c.check(False, f"load {uri}", str(e))
        return
    c.check(True, f"load {uri}")

    # 3. Hyperparameters of the loaded object == params logged in the run ----
    # (MLflow stores params as strings -> compare as floats)
    for k in TUNED_KEYS:
        logged = run.data.params.get(k)
        actual = getattr(model, k)
        ok = logged is not None and np.isclose(float(logged), float(actual))
        c.check(ok, f"{k} matches run", f"model={actual}, run={logged}")

    # 4. Regressors: same lagged features as today's training frame ----------
    _, regressor_cols = build_train_frame(daily, H)
    model_regs = set(model.extra_regressors.keys())
    c.check(model_regs == set(regressor_cols), "regressors match features",
            f"missing={set(regressor_cols) - model_regs or '-'}, "
            f"extra={model_regs - set(regressor_cols) or '-'}")

    # 5. Prediction sanity ---------------------------------------------------
    future, _ = build_future_frame(daily, H)
    try:
        fc = model.predict(future)
    except Exception as e:
        c.check(False, "predict", str(e))
        return

    last_obs = daily[daily[CONFIG["model"]["prophet"]["data"]["target"]].notna()].index.max()
    fut = fc[fc["ds"] > last_obs]
    c.check(len(fut) >= H, f"forecast covers {H} future days", f"got {len(fut)}")
    c.check(not fc[["yhat", "yhat_lower", "yhat_upper"]].isna().any().any(), "no NaN in forecast")
    c.check(bool((fc["yhat_lower"] <= fc["yhat"]).all() and (fc["yhat"] <= fc["yhat_upper"]).all()),
            "yhat_lower <= yhat <= yhat_upper")
    if len(fut):
        c.info(f"forecast {fut['ds'].min().date()} -> {fut['ds'].max().date()}: "
               f"yhat in [{fut['yhat'].min():.2f}, {fut['yhat'].max():.2f}] m")

    # 6. Production config vs latest tuning best (informative only) ----------
    csv = TUNING_DIR / f"tuning_results_H{H}.csv"
    if csv.exists():
        best = pd.read_csv(csv).iloc[0]          # sorted by select_score
        same = all(np.isclose(float(best[k]), float(getattr(model, k))) for k in TUNED_KEYS)
        c.info(f"production config {'==' if same else '!='} latest tuning best "
               f"({', '.join(f'{k}={best[k]}' for k in TUNED_KEYS)})"
               + ("" if same else " -> normal if the champion was kept"))

    # 7. Optional: what the deployed API actually serves ---------------------
    if api_url:
        import requests
        try:
            r = requests.post(f"{api_url}/predict", params={"H": H}, timeout=120)
            r.raise_for_status()
            api_pts = pd.DataFrame(r.json()["points"])
            merged = api_pts.merge(fc.assign(ds=fc["ds"].dt.strftime("%Y-%m-%d")),
                                   on="ds", suffixes=("_api", "_local"))
            gap = (merged["yhat_api"] - merged["yhat_local"]).abs().max()
            # Same model + same data => same yhat. A gap means the API cache holds
            # an older version (call /model/reload) or its S3 data differs.
            c.check(gap < 1e-3, "API serves the same model as @production",
                    f"max |yhat_api - yhat_local| = {gap:.4g} on {len(merged)} days")
        except Exception as e:
            c.check(False, "API /predict", str(e))


def main():
    parser = argparse.ArgumentParser(description="Smoke test of @production models.")
    parser.add_argument("--horizon", type=int, choices=[14, 30], help="default: both")
    parser.add_argument("--api", action="store_true", help="also compare with the deployed API")
    args = parser.parse_args()

    if "MLFLOW_TRACKING_URI" in os.environ:
        mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    print(f"Tracking URI: {mlflow.get_tracking_uri()}")

    api_url = os.getenv("API_URL") if args.api else None
    if args.api and not api_url:
        print("--api requires API_URL in .env"); sys.exit(1)

    daily = build_daily(pd.read_csv(DATA_PATH))
    client = MlflowClient()
    c = Checker()

    for H in ([args.horizon] if args.horizon else [14, 30]):
        test_horizon(H, daily, client, c, api_url)

    print(f"\n{'ALL CHECKS PASSED' if c.failures == 0 else f'{c.failures} CHECK(S) FAILED'}")
    sys.exit(1 if c.failures else 0)


if __name__ == "__main__":
    main()
