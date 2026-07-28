# Import libraries
import pandas as pd


def preprocessing(df, test_size=30):
    """
    Steps:
    1. Set temporal index
    2. Select relevant daily features (numeric, domain-informed)
    3. Temporal train/test split (last test_size days = test set)
    4. Split X / y
    Returns X_train, X_test, y_train, y_test.
    """
    df = df.copy()
    df = df.set_index("date_index", drop=False)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    feature_cols = [
        "shortwave_radiation_sum",
        "et0_fao_evapotranspiration",
        "soil_temperature_0_to_100cm_mean",
        "P_cum_90d",
        "Peff_cum_90d",
        "Temperature_mean_90d"
    ]
    target_col = "niveau_nappe_eau"

    df = df[feature_cols + [target_col]].dropna()

    test_size = test_size # days as the dataframe is daily
    df_train = df.iloc[:-test_size]
    df_test  = df.iloc[-test_size:]

    X_train = df_train[feature_cols]
    y_train = df_train[target_col]
    X_test  = df_test[feature_cols]
    y_test  = df_test[target_col]

    return X_train, X_test, y_train, y_test