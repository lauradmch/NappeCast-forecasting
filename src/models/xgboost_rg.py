#-------------------------------------------------------------------------------
# XGBoost regressor model
#-------------------------------------------------------------------------------

import mlflow
import mlflow.xgboost
import pandas as pd
import numpy as np
from pathlib import Path
import os
from dotenv import load_dotenv
from src.models.preprocessing import preprocessing
from xgboost import XGBRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

load_dotenv()

# Loading dataframe
input_path = Path("../..") / 'data' / 'processed' / 'dataset_processed.csv'
dataset    = pd.read_csv(input_path)
dataset    = dataset.set_index("date_index", drop=False)
dataset.index = pd.to_datetime(dataset.index)
df_daily   = dataset.copy()


def xgboost_regressor(df, n_estimators=100, learning_rate=0.1, max_depth=4,
                      subsample=0.8, colsample_bytree=0.8, random_state=42):
    """
    XGBoost Regressor predicting groundwater level (niveau_nappe_eau).
    Logs parameters, metrics and model to MLflow.
    Returns predictions and evaluation metrics DataFrames.
    """
    mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME"))

    X_train, X_test, y_train, y_test = preprocessing(df, test_size=30)

    with mlflow.start_run():

        # Parameters
        params = {
            "n_estimators"    : n_estimators,
            "learning_rate"   : learning_rate,
            "max_depth"       : max_depth,
            "subsample"       : subsample,
            "colsample_bytree": colsample_bytree,
            "random_state"    : random_state
        }
        mlflow.log_params(params)

        # Model
        model = XGBRegressor(**params)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        # Metrics :
        metrics = {
            "test_length_days"  : float((y_test.index[-1] - y_test.index[0]).days + 1),
            "R2_train"          : float(model.score(X_train, y_train)),
            "R2_test"           : float(r2_score(y_test, y_pred)),
            "RMSE"              : float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "MAE"               : float(mean_absolute_error(y_test, y_pred)),
            "MAPE"              : float(np.mean(np.abs((y_test - y_pred) / y_test)) * 100),
            "Biais"             : float(np.mean(y_pred - y_test.values))
        }
        mlflow.log_metrics(metrics)

        # Model artifact
        mlflow.xgboost.log_model(model, artifact_path="xgboost_model")

        # Split tags
        mlflow.set_tags({
            "train_start": str(y_train.index[0].date()),
            "train_end"  : str(y_train.index[-1].date()),
            "test_start" : str(y_test.index[0].date()),
            "test_end"   : str(y_test.index[-1].date())
        })

        print(f"Run loggé — R2_train={metrics['R2_train']:.3f} | "
              f"R2_test={metrics['R2_test']:.3f} | "
              f"RMSE={metrics['RMSE']:.3f} | "
              f"MAPE={metrics['MAPE']:.2f}%")

    # Output DataFrames
    predictions_xgboost_reg = pd.DataFrame({
        "y_test": y_test.values,
        "y_pred": y_pred
    }, index=y_test.index)

    evaluation_metrics_xgboost_reg = pd.DataFrame(
        metrics, index=["niveau_nappe_eau"]
    )

    return predictions_xgboost_reg, evaluation_metrics_xgboost_reg

if __name__ == "__main__":
    predictions, metrics = xgboost_regressor(df_daily)