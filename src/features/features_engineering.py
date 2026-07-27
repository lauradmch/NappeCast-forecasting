#---------------------------------------------------------------------------------
# Features engineering
#---------------------------------------------------------------------------------

# Import libraries
from pathlib import Path
import pandas as pd
import numpy as np
import logging


from src.config import load_config
from src.helper.aws import save_processed_data_to_s3
from scipy.stats import norm


CONFIG = load_config()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)



def standardize_index(series: pd.Series, 
                      scale=1, 
                      agg: str="mean", 
                      freq: str="MS")-> pd.Series:
    
    """Monthly standardized index via Gringorten plotting position + inverse-normal.
    Returns a monthly Series ~ N(0,1)."""
    m = series.resample(freq).agg(agg)                 # 1) daily -> monthly
    if scale > 1:                                      # 2) accumulate over `scale` months
        m = m.rolling(scale).sum() if agg == "sum" else m.rolling(scale).mean()
    g = m.groupby(m.index.month)                       # 3) fit per calendar month
    ranks = g.transform("rank"); n = g.transform("count")
    p = (ranks - 0.44) / (n + 1 - 2*0.44)              # Gringorten plotting position
    return pd.Series(norm.ppf(p), index=m.index, name=f"{series.name}_s{scale}")


def add_standardized_features(df: pd.DataFrame, 
                              scales: list[int] = [1]) -> pd.DataFrame:
    """Add SPLI + companion standardized indices (monthly, N(0,1)) as DAILY columns.
    Each monthly index value is forward-filled across the days of that month."""

    # Water balance P - ET0, the driver of the SPEI-like index (created here, as in the analysis nb)
    df["Peff"] = df["precipitation_sum"] - df["et0_fao_evapotranspiration"]

    # (index name, source column, aggregation): "mean" for state vars, "sum" for fluxes
    spec = [
        ("SPLI", "niveau_nappe_eau",                 "mean"),  # groundwater level  <-- the target-derived one
        ("SPI",  "precipitation_sum",                "sum"),
        ("SETI", "et0_fao_evapotranspiration",       "sum"),
        ("SSTI", "soil_temperature_0_to_100cm_mean", "sum"),
        ("SSRI", "shortwave_radiation_sum",          "sum"),
        ("SWSI", "wind_speed_10m_mean",              "sum"),
        ("SCCI", "cloud_cover_mean",                 "sum"),
        ("SPMI", "pressure_msl_mean",                "sum"),
        ("SPEI", "Peff",                             "sum"),   # rain minus ET0
        ("SSMI", "soil_moisture_0_to_100cm_mean",    "mean"),
    ]

    # Build the monthly panel
    monthly = {}
    for name, col, agg in spec:
        for s in scales:
            monthly[f"{name}"] = standardize_index(df[col], s, agg)
    panel = pd.DataFrame(monthly)

    # Broadcast monthly -> daily: align each day to its month start, then map
    month_key = df.index.to_period("M").to_timestamp()        # each daily row -> its 1st-of-month
    daily = panel.reindex(month_key).set_index(df.index, drop=False)      # ffill happens implicitly via reindex-on-month

    logger.info(f"add_standardized_features terminé !")
    return df.join(daily)


def featuring_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering performed on clean merged dataset (after merging piezometer_cleaned.csv & weather_cleaned.csv datasets)
    """
    df = df.copy()
    
    # Setting 'date_index' as index of the dataframe
    df["date_index"] = pd.to_datetime(df["date_index"])
    df = df.set_index("date_index", drop=False)
    
    # Treatment of duplicated rows (kept only one reading per day)
    df = df[~df.index.duplicated(keep="first")]

    # Interpolate missing dates to keep daily frequency
    cols = df.select_dtypes(include=['number']).columns
    df[cols] = df[cols].sort_index().asfreq("D").interpolate()
    
    # Computation of cumulative precipitation (during the last 30-90 days)
    df['P_cum_30d'] = df['precipitation_sum'].rolling(window=30).sum()
    df['P_cum_90d'] = df['precipitation_sum'].rolling(window=90).sum()
    
    # Computation of cumulative effective precipitation (during the last 30 & 90 days)
    df['Peff_cum_30d'] = (df['precipitation_sum'] - df['et0_fao_evapotranspiration']).rolling(window=30).sum()
    df['Peff_cum_90d'] = (df['precipitation_sum'] - df['et0_fao_evapotranspiration']).rolling(window=90).sum()
    
    # Computation of the mean temperature (during the last 30 and 90 days)
    df['Temperature_mean_30d'] = round(df['soil_temperature_0_to_100cm_mean'].rolling(window=30).mean(), 2)
    df['Temperature_mean_90d'] = round(df['soil_temperature_0_to_100cm_mean'].rolling(window=90).mean(), 2)

    # Filling the NaN generated during the earliest period of the dataframe (no computation of the cumulative data)
    df['P_cum_30d']             = df['P_cum_30d'].fillna(df['P_cum_30d'].dropna().iloc[0])
    df['P_cum_90d']             = df['P_cum_90d'].fillna(df['P_cum_90d'].dropna().iloc[0])
    df['Peff_cum_30d']          = df['Peff_cum_30d'].fillna(df['Peff_cum_30d'].dropna().iloc[0])
    df['Peff_cum_90d']          = df['Peff_cum_90d'].fillna(df['Peff_cum_90d'].dropna().iloc[0])
    df['Temperature_mean_30d']   = df['Temperature_mean_30d'].fillna(df['Temperature_mean_30d'].dropna().iloc[0])
    df['Temperature_mean_90d']  = df['Temperature_mean_90d'].fillna(df['Temperature_mean_90d'].dropna().iloc[0])

    logger.info(f"featuring_dataset terminé !")
    return df

def feature_engineering(df: pd.DataFrame, 
                        save_file: bool = True) -> pd.DataFrame:

    df = df.copy()
    df = featuring_dataset(df)
    df = add_standardized_features (df)
    df = df.drop(columns="Peff")

    # Filling the NaN
    std_cols = df.filter(regex=r"^S.*I$").columns
    df[std_cols] = df[std_cols].fillna(df[std_cols].mean())

    if save_file:
        save_processed_data_to_s3(df, Path(CONFIG["paths"]["data"]["processed"]), CONFIG["paths"]["processed_filename"], False)

    return df