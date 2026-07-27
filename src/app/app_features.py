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
        st.header("""
            Exploratory Data Analysis and feature engineering performed on the merged weather & piezometer datasets:
            """)
        st.markdown("""
                The main objectives of this step were to investigate:
                
                - **Data types:** identify the types of data present in the datasets after data collection (not shown)
                
                - **Missing values:** assess and handle missing values (not shown)
                
                - **Feature correlations:** evaluate correlations between features and determine whether any treatment was required
                
                - **Feature engineering:** create new features based on domain expertise
                
                | Variable | Unit | Description |
                |----------|------|-------------|
                | `Precipitation` | mm | Sum of daily precipitation (including rain, showers and snowfall) |
                | `Daylight duration` | seconds | Number of seconds of daylight per day |
                | `Wind speed` | km/h (mph, m/s, knots) | Wind speed at 10 meters above ground (standard level) |
                | `Shortwave radiation` | MJ/m² | The sum of solar radiation on a given day in Megajoules |
                | `Evapotranspiration` | mm | Daily sum of ET₀ Reference Evapotranspiration of a well watered grass field |
                | `Soil temperature` | °C (°F)	| Average temperature of different soil levels below ground |
                | `Soil moisture` | m³/m³ | Average soil water content as volumetric mixing ratio at 0 - 255 cm depths |
                | `Cloud cover` | %	| Total cloud cover as an area fraction |
                | `Sea-level pressure` | hPa	| Atmospheric air pressure reduced to mean sea level |
                """)
    
        df_cleaned = df_cleaned.set_index('date_index', drop=False)
        df_cleaned.index = pd.to_datetime(df_cleaned.index)
    
        cols_to_drop = ['longitude', 'latitude', 'et0_fao_evapotranspiration_sum', 'relative_humidity_2m_mean', 'rain_sum', 'surface_pressure_mean',
                        'dew_point_2m_mean', 'precipitation_hours', 'sunshine_duration', 'weather_code', 'apparent_temperature_min', 
                        'apparent_temperature_max', "temperature_2m_min", "temperature_2m_max", 'sunrise', 'sunset', 'code_bss', 
                        'date_index', 'bss_id', 'mode_obtention', 'nom_producteur']
        df_reduced = df_cleaned.drop(columns=cols_to_drop, errors='ignore')
        df2 = df_reduced.copy()
        df2 = df2.rename(columns={'daylight_duration': 'Daylight duration', 'precipitation_sum': 'Precipitation', 'shortwave_radiation_sum': 'Shortwave radiation', 
                        'et0_fao_evapotranspiration': 'Evapotranspiration', 'cloud_cover_mean': 'Cloud cover', 'pressure_msl_mean': 'Sea-level pressure',
                        'wind_speed_10m_mean': 'Wind speed', 'soil_moisture_0_to_100cm_mean': 'Soil moisture', 'soil_temperature_0_to_100cm_mean': 'Soil temperature'}) 
    
        # Correlation of the numerical features after dropping columns with >= 70% of correlation
        corr = df2.corr(method='pearson', numeric_only=True)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm',
                    vmin=-1, vmax=1, square=True, ax=ax,
                annot_kws={"size": 7})
        ax.set_title('Correlation matrix after removal of correlated features', fontsize=9)
        ax.tick_params(axis='both', labelsize=7)
        plt.tight_layout()
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
                st.pyplot(fig)
        st.caption("""
               The feature selection process successfully removed redundant variables, cutting the feature space
               from 21 to 9. The resulting matrix confirms that multicollinearity has been largely reduced,
               which should improve model interpretability and reduce the risk of overfitting.
               """)
    
    
        # Exploration of the different features against the 'niveau_nappe_eau' column:
        st.markdown("""
                        Explore the cleaned features of the dataset by selecting a column from the dropdown menu.
                        Each feature is plotted against the ground water level to visually assess potential 
                        relationships or correlations.
                        """)
        
        col = st.selectbox('Select an additional column', [c for c in df2.columns if c != 'niveau_nappe_eau'])
        data = df2[['niveau_nappe_eau', col]].dropna()
        data.index = pd.to_datetime(data.index)
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        # Primary axis: 'niveau_nappe_eau'
        ax1.plot(data.index, data['niveau_nappe_eau'], 
                 color='steelblue', 
                 label='niveau_nappe_eau',
                 linewidth= 1.5,
                 linestyle= "--",
                 marker='o')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Ground water level', color='steelblue')
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
        
        ax1.set_title(f'ground water level & {col} over time')
        plt.tight_layout()
        st.pyplot(fig)