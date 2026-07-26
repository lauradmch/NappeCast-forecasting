# Import libraries
import streamlit as st
import requests
import pandas as pd




#--------------------- 🧭 Sidebar menu ---------------------
# st.sidebar gives you access to a dedicated sidebar panel.
# Useful for navigation menus, filters, or extra info.
st.sidebar.header('Purpose & Objectives')
st.sidebar.markdown("""
                    * [Purpose](#Purpose)
                    * [Objectives](#Objectives)
                    * [Data sources](#Sources)
                    * [GitHub Repository](https://github.com/lauradmch/NappeCast-forecasting)
                    """)

st.sidebar.header('Exploratory Data Analysis')
st.sidebar.markdown("""
                    * [Features Engineering](#Features-Engineering)
                    * [Visualization](#Visualization)
                    """)



st.sidebar.header('Nappecast level prediction')
st.sidebar.markdown("""
                    * [Machine Learning models](#ML-models)
                    * [Deep Learning models](#DL-models)
                    """)


#--------------------- Purpose & Objectives ---------------------

st.header("Purpose & Objectives")
st.markdown("<a id='Purpose'></a>", unsafe_allow_html=True)
st.subheader("Purpose")





st.markdown("<a id='Objectives'></a>", unsafe_allow_html=True)
st.subheader("Objectives")
st.markdown("""
            cc
            """)




st.markdown("<a id='Sources'></a>", unsafe_allow_html=True)
st.subheader("Data sources")
st.markdown("""
            **Piezometer data** (capturing the nappecast level, among other data) were collected from the 
            "Hub eau"'s open API (https://hubeau.eaufrance.fr/page/api-piezometrie). List of data collected:\n
            - code_bss, bss_id, urn_bss, date_mesure, timestamp_mesure, niveau_nappe_eau,
            mode_obtention, statut, qualification, code_continuite, nom_continuite, code_producteur, nom_producteur,
            code_nature_mesure, nom_nature_mesure, profondeur_nappe.
            \n
            **Open-meteo data** (capturing many different meteorological data at a specify localization) were
            collected from the Open-Meto's API (https://open-meteo.com/en/docs). List of data collected:\n
            - date, latitude, longitude, weather_code, temperature_2m_max, temperature_2m_min, apparent_temperature_max,
            apparent_temperature_min, sunrise, sunset, daylight_duration, sunshine_duration, uv_index_max, 
            uv_index_clear_sky_max, rain_sum, showers_sum, snowfall_sum, precipitation_sum, precipitation_hours,
            precipitation_probability_max, shortwave_radiation_sum, et0_fao_evapotranspiration, cloud_cover_mean, 
            dew_point_2m_mean, et0_fao_evapotranspiration_sum, relative_humidity_2m_mean, snowfall_water_equivalent_sum,
            pressure_msl_mean, surface_pressure_mean, visibility_mean, wind_speed_10m_mean, soil_moisture_0_to_100cm_mean,
            soil_temperature_0_to_100cm_mean.
            """)





#--------------------- Exploratory Data Analysis ---------------------

st.header("Exploratory Data Analysis")
st.markdown("<a id='Features-Engineering'></a>", unsafe_allow_html=True)
st.subheader("Features Engineering Strategy")
st.markdown("""
            During the Exploratory analysis, we evaluated the computation 
            of new features to try to better characterized our data. To that end, multiple new features were created such as:
            \n**- Cumulative Precipitation** (during the last 7-30-90 days, *e.g* '*P_cum_7d*'): to try to track the effect of the cumulative 
            precipitation during a specified timeframe and its impact on nappecast level.
            \n**- Cumulative Effectve Precipitation** (during the last 30 & 90 days, *e.g* '*Peff_cum_30d*'): calculated by making the sum of the 
            difference between the sum of the precipitation minus the 'et0_fao_evapotranspiration' (measurement of the 
            water quantity which evaporate at the ground). This feature traduce the level of water that goes into the ground.
            \n**Mean Temperature** (during the last 7 & 30 days, *e.g* '*Temperature_mean_7d*'): mean temperature during the last 7 & 3 days that may impact 
            the nappecast level.
            """)





st.markdown("<a id='Visualization'></a>", unsafe_allow_html=True)
st.subheader("Visualization")

# Figure 1
fig = px.line(
    data,
    x="date_index",
    y="niveau_nappe_eau",
    title="Évolution du niveau de la nappe",
    labels={
        "date_index": "Date",
        "niveau_nappe_eau": "Niveau nappe (m)"
    }
)
st.plotly_chart(fig, use_container_width=True)

# Figure 2
fig = px.scatter_mapbox(
    data,
    lat="latitude",
    lon="longitude",
    hover_name="nom_producteur",
    zoom=6,
    title="Localisation des piézomètres"
)
fig.update_layout(
    mapbox_style="open-street-map",
    uirevision="constant"
)
st.plotly_chart(fig, use_container_width=True)

#############################################################################################################
#############################################################################################################
#############################################################################################################
#############################################################################################################
#############################################################################################################
#############################################################################################################
#############################################################################################################
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
            Exploratory Data Analysis performed on the weather dataset:
            """)
    st.markdown("""
                The main objectives of this step were to investigate:
                - **Data types:** identify the types of data present in the `weather` dataset after data collection
                - **Missing values:** assess and handle missing values
                - **Feature correlations:** evaluate correlations between features and determine whether any treatment was required
                - **Feature engineering:** create new features based on domain expertise
                """)
    # Exploration of the different features against the 'niveau_nappe_eau' column:
    st.markdown("""
                Explore the raw features of the dataset by selecting a column from the dropdown menu.
                Each feature is plotted against the water table level (niveau_nappe_eau) to visually assess
                potential relationships or correlations before any cleaning or transformation was applied.
                """)
    col = st.selectbox('Select a column', [c for c in df.columns if c != 'niveau_nappe_eau'])
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.scatter(df[col].dropna(), df['niveau_nappe_eau'].dropna(), alpha=0.5)
    ax.set_title(f'{col} vs niveau_nappe_eau')
    ax.set_xlabel(col)
    ax.set_ylabel('niveau_nappe_eau')
    plt.tight_layout()
    st.pyplot(fig)  
    
    
    # Correlation of the numerical features
    st.subheader("Weather Dataset After Data Collection")
    st.markdown("""
                This section presents the weather dataset after collection and cleaning for features with 100% of NaN and non-informative data.
                """)
    corr = df.corr(method='pearson', numeric_only=True)
    fig, ax = plt.subplots(figsize=(20, 20))
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
    df_reduced = df.drop(columns=cols_to_drop, errors='ignore')
    
    
    # Correlation of the numerical features after dropping columns with >= 70% of correlation
    corr = df_reduced.corr(method='pearson', numeric_only=True)
    fig, ax = plt.subplots(figsize=(20, 20))
    sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', vmin=-1, vmax=1, square=True, ax=ax)
    ax.set_title('Correlation matrix between features after removal of correlated features')
    plt.tight_layout()
    st.pyplot(fig)
    st.caption("""
               The feature selection process successfully removed redundant variables, cutting the feature space
               from 21 to 9. The resulting matrix confirms that multicollinearity has been largely reduced,
               which should improve model interpretability and reduce the risk of overfitting.
               """)