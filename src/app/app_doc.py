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
    st.write("Documentations, définition etc...")
    st.header("Purpose & Objectives")
    st.markdown("<a id='Purpose'></a>", unsafe_allow_html=True)
    st.subheader("Purpose")
    
    st.markdown("<a id='Objectives'></a>", unsafe_allow_html=True)
    st.subheader("Objectives")
    
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

