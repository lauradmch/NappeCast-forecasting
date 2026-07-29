"""
Contenu de l'onglet Documentations

"""


# --------------------------- LIBRARY --------------------------------
import ast
import pandas as pd
import streamlit as st
import requests
import plotly.express as px 

# ---------------------------- VARIABLES ---------------------------


# ---------------------------- METHODES ---------------------------

def render_documentation()-> None:
    st.header("Purpose & Objectives")
    st.markdown("<a id='Purpose'></a>", unsafe_allow_html=True)
    st.subheader("Purpose")
    st.markdown("""
                Groundwater aquifers are a critical shared resource, supplying drinking water to households, 
                supporting agricultural irrigation, and meeting industrial needs. Yet today, aquifer management 
                remains largely reactive and empirical — when water levels drop to critical thresholds, interventions 
                such as manual recharge are triggered only after the deficit has already occurred. This approach 
                carries significant operational costs and, more importantly, offers no foresight into future depletion 
                risks. Compounding the challenge, water authorities must continuously arbitrate between competing 
                users — residents, farmers, and industries — often under pressure and without reliable predictive tools.
                """)
    
    st.markdown("<a id='Objectives'></a>", unsafe_allow_html=True)
    st.subheader("Objectives")
    st.markdown("""
                This project addresses these limitations through a data-driven approach structured around three core 
                analytical steps:
                \n- **Critical level identification** — establishing historical baselines to characterise what constitutes 
                a critical aquifer level, drawing from long-term observational data
                \n- **Climate impact analysis** — quantifying how meteorological events modulate aquifer dynamics, 
                identifying the key drivers of depletion and recharge
                \n- **Predictive modelling* — forecasting future water levels from current weather data, enabling 
                anticipation rather than reaction
                \n\nThe ability to predict critical aquifer levels ahead of time unlocks two concrete management levers:
                \n-**Demand prioritisation** — anticipating water allocation conflicts between user groups before a crisis 
                point is reached, slowing depletion rates
                \n- **Proactive recharge planning** — scheduling aquifer replenishment operations in advance, rather 
                than as an emergency response
                """)
    
    st.markdown("<a id='Sources'></a>", unsafe_allow_html=True)
    st.subheader("Data sources")
    st.markdown("""
            **Piezometer data** (capturing the nappecast level, among other data) were collected from the 
            "Hub eau"'s open API (https://hubeau.eaufrance.fr/page/api-piezometrie). List of data collected:
            \n- **Station Identification** - Unique station identifiers (BSS code, BSS ID, URN) used to 
            reference each monitoring well in the national database.
            \n- **Measurement** - Daily groundwater level (meters above sea level) and aquifer depth, along 
            with the timestamp and date of each reading.
            \n- **Data Quality & Status** - Qualification status, continuity code, and measurement nature — 
            indicating whether each record is validated, estimated, or provisional.
            \n- **Data Producer** - Identification of the organisation responsible for collecting and 
            submitting the measurement.
            \n\n**Open-meteo data** (capturing many different meteorological data at a specify localization) were
            collected from the Open-Meto's API (https://open-meteo.com/en/docs). List of data collected:
            \n- **Temperature & Comfort** - Daily maximum and minimum air temperature, apparent (felt) temperature, 
            dew point, and relative humidity
            \n- **Solar Radiation & Daylight** - Shortwave radiation sum, UV index (actual and clear-sky), sunshine 
            and daylight duration, and sunrise/sunset times
            \n- **Precipitation & Water Input** - Total precipitation, rainfall, showers, snowfall (and its water 
            equivalent), precipitation hours, and maximum precipitation probability
            \n- **Evapotranspiration & Soil** - FAO-56 reference evapotranspiration (ET₀), soil moisture and soil 
            temperature (averaged over 0–100 cm depth).
            \n- **Atmosphere & Visibility** - Mean sea-level pressure, surface pressure, cloud cover, and visibility
            \n- **Wind** - Mean wind speed at 10 m height
            """)

