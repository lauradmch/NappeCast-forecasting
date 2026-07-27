"""
Features tab content

"""


# --------------------------- LIBRARY --------------------------------
import ast
from pathlib import Path
from src.config import load_config
import pandas as pd
import streamlit as st
import requests
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px 

# ---------------------------- LOADING DATA ---------------------------


# ---------------------------- METHODES ---------------------------

def render_features(df_cleaned = pd.DataFrame) -> None:
    st.markdown("""
                This page provides an overview of the exploratory data analysis (EDA) performed on the weather dataset during the project.
                \nIt presents the main characteristics and distributions of the weather features, as well as the data cleaning process, 
                including the analysis of feature correlations using a correlation matrix.
                \nFinally, it presents the new features created during the feature engineering process and their contribution to the 
                dataset.
                """)
    
    st.header("""
            Exploratory Data Analysis and feature engineering performed on the merged weather & piezometer datasets:
            """)
    st.markdown("""
                The main objectives of this step were to investigate:
                \n- **Data types:** identify the types of data present in the datasets after data collection (not shown)
                \n- **Missing values:** assess and handle missing values (not shown)
                \n- **Feature correlations:** evaluate correlations between features and determine whether any treatment was required
                \n- **Feature engineering:** create new features based on domain expertise
                
                
                \n List of the features collected and their description:
                \n\n Weather Variables
                
                | Variable | Unit | Description |
                |----------|------|-------------|
                | `weather_code` | WMO code | The most severe weather condition on a given day |
                | `temperature_2m_max` / `temperature_2m_min` | °C (°F) | Maximum and minimum daily air temperature at 2 meters above ground |
                | `apparent_temperature_max` / `apparent_temperature_min` | °C (°F) | Maximum and minimum daily apparent temperature |
                | `precipitation_sum` | mm | Sum of daily precipitation (including rain, showers and snowfall) |
                | `rain_sum` | mm | Sum of daily rain |
                | `snowfall_sum` | cm | Sum of daily snowfall |
                | `precipitation_hours` | hours | The number of hours with rain |
                | `sunrise` / `sunset` | iso8601 | Sun rise and set times |
                | `sunshine_duration` | seconds | The number of seconds of sunshine per day is determined by calculating direct normalized irradiance exceeding 120 W/m², following the WMO definition. Sunshine duration will consistently be less than daylight duration due to dawn and dusk. |
                | `daylight_duration` | seconds | Number of seconds of daylight per day |
                | `wind_speed_10m_max` / `wind_gusts_10m_max` | km/h (mph, m/s, knots) | Maximum wind speed and gusts on a day |
                | `wind_direction_10m_dominant` | ° | Dominant wind direction |
                | `shortwave_radiation_sum` | MJ/m² | The sum of solar radiation on a given day in Megajoules |
                | `et0_fao_evapotranspiration` | mm | Daily sum of ET₀ Reference Evapotranspiration of a well watered grass field |
                """)
    
    
    # Correlation of the numerical features
    st.subheader("Weather Dataset After Data Collection")
    st.markdown("""
                This section presents the weather dataset after collection and cleaning for features with 100% of NaN and non-informative data.
                """)
    corr = df_cleaned.corr(method='pearson', numeric_only=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, square=True, ax=ax)
    ax.set_title('Correlation matrix between features before removal of correlated features')
    plt.tight_layout()
    st.pyplot(fig)
    st.caption("""
           The correlation matrix highlights strong relationships between several weather features, 
           which were considered during the data cleaning and feature selection processes.
           """)
    
    st.write("""
             Regarding those results, we put a threshold at 70% to select the features to drop during the analysis.
             """)
    
    cols_to_drop = ['et0_fao_evapotranspiration_sum', 'relative_humidity_2m_mean', 'rain_sum', 'surface_pressure_mean',
                    'dew_point_2m_mean', 'precipitation_hours', 'sunshine_duration', 'weather_code', 'apparent_temperature_min', 
                    'apparent_temperature_max', "temperature_2m_min", "temperature_2m_max"]
    df_reduced = df_cleaned.drop(columns=cols_to_drop, errors='ignore')
    
    
    # Correlation of the numerical features after dropping columns with >= 70% of correlation
    corr = df_reduced.corr(method='pearson', numeric_only=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, square=True, ax=ax)
    ax.set_title('Correlation matrix between features after removal of correlated features')
    plt.tight_layout()
    st.pyplot(fig)
    st.caption("""
               The feature selection process successfully removed redundant variables, cutting the feature space
               from 21 to 9. The resulting matrix confirms that multicollinearity has been largely reduced,
               which should improve model interpretability and reduce the risk of overfitting.
               """)
    
    
    # Exploration of the different features against the 'niveau_nappe_eau' column:
    st.markdown("""
                Explore the cleaned features of the dataset by selecting a column from the dropdown menu.
                Each feature is plotted against the water table level (niveau_nappe_eau) to visually assess
                potential relationships or correlations.
                """)

    col = st.selectbox('Select an additional column', [c for c in df_reduced.columns if c != 'niveau_nappe_eau'])
    data = df_reduced[['niveau_nappe_eau', col]].dropna()
    fig, ax1 = plt.subplots(figsize=(10, 8))
    
    # Primary axis: 'niveau_nappe_eau'
    ax1.plot(data.index, data['niveau_nappe_eau'], color='steelblue', label='niveau_nappe_eau')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('niveau_nappe_eau', color='steelblue')
    ax1.tick_params(axis='y', labelcolor='steelblue')
    # Secondary axis : selected column
    ax2 = ax1.twinx()
    ax2.plot(data.index, data[col], color='coral', alpha=0.7, label=col)
    ax2.set_ylabel(col, color='coral')
    ax2.tick_params(axis='y', labelcolor='coral')
    
    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    ax1.set_title(f'niveau_nappe_eau & {col} over time')
    plt.tight_layout()
    st.pyplot(fig)