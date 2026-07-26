#---------------------------------------------------------------------------------
# Streamlit interface
#---------------------------------------------------------------------------------

#--------------------- LIBRARY ---------------------
import streamlit as st
import requests
import pandas as pd
import plotly.express as px 
import plotly.graph_objects as go
import boto3
import os
import yaml

from io import StringIO
from pathlib import Path
from src.config import load_config

from src.app.app_sidebar import render_sidebar
from src.app.app_identity import render_identity
from src.app.app_predictions import render_predictions
from src.app.app_features import render_features
from src.app.app_stats import render_stats

from src.app.app_doc import render_documentation
from src.helper.aws import read_csv_in_s3

#--------------------- VARIABLES ---------------------
CONFIG = load_config()

API_URL                 = os.getenv("API_URL", "http://localhost:8000")
CODE_BSS                = ",".join(CONFIG["api"]["piezometer"]["code_bss"])
STATION_RAW_FILENAME    = Path(CONFIG["paths"]["data"]["raw"]) / f"{CONFIG['paths']['station']['raw_filename']}.csv"
INTERIM_FILENAME        = Path(CONFIG["paths"]["data"]["interim"]) / f"{CONFIG['paths']['interim_filename']}.csv"
PROCESSED_FILENAME        = Path(CONFIG["paths"]["data"]["processed"]) / f"{CONFIG['paths']['processed_filename']}.csv"

S3_SESSION              = boto3.client("s3")
BUCKET_NAME             = CONFIG["s3"]["bucket"]

#---------------------  Configuration section ---------------------
st.set_page_config(
    page_title='NappeCast',
    page_icon= '💧',
    layout='wide'
)

st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem !important;
    }
    .stApp {{ background: {C_BG}; }}
    .block-container {{ padding-top: 2.2rem; max-width: 1250px; }}
    h1, h2, h3 {{ color: {C_DEEP}; font-weight: 700; }}
    .hero {{
        background: linear-gradient(120deg, {C_DEEP} 0%, {C_BLUE} 55%, {C_TEAL} 100%);
        color: white; padding: 1.6rem 2rem; border-radius: 16px;
        box-shadow: 0 8px 24px rgba(11,79,108,0.18); margin-bottom: 1.4rem;
    }}
    .hero h1 {{ color: white; margin: 0 0 .3rem 0; font-size: 2.0rem; }}
    .hero p {{ margin: 0; opacity: .92; font-size: 1.02rem; }}
    .card {{
        background: white; border: 1px solid {C_GRID}; border-radius: 14px;
        padding: 1.1rem 1.3rem 0.4rem 1.3rem; margin-bottom: 1.2rem;
        box-shadow: 0 2px 10px rgba(11,79,108,0.05);
    }}
    .caption {{ color: #567; font-size: 0.9rem; line-height: 1.45; }}

    [data-testid="stMetricValue"] {{ color: {C_DEEP}; }}
    [data-testid="stSidebarHeader"] {
        min-height: 0 !important;
        padding: 0.5rem 1rem 0 1rem !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0.5rem !important;
    }
    [data-testid="stDecoration"] {
        display: none;
    }

    /* --- Onglets en barre de menu --- */
    [data-testid="stTabs"] div[data-baseweb="tab-list"] {
        gap: 2rem;
        justify-content: center;
        border-bottom: 1px solid #e0e0e0;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"] {
    height: 4rem !important;
    padding: 0 1.5rem !important;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"] [data-testid="stMarkdownContainer"] p {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        border-bottom: 3px solid #FF4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

#---------------------  Load data ---------------------
@st.cache_data
def load_data()-> tuple[pd.DataFrame, pd.DataFrame]:
    df_station      = read_csv_in_s3(S3_SESSION, BUCKET_NAME, STATION_RAW_FILENAME)
    df_interim      = read_csv_in_s3(S3_SESSION, BUCKET_NAME, INTERIM_FILENAME)
    df_processed    = read_csv_in_s3(S3_SESSION, BUCKET_NAME, PROCESSED_FILENAME)
    return df_station, df_interim, df_processed

df_station, df_interim, df_processed = load_data()

# --------------------- Sidebar menu ---------------------

render_sidebar(df_station, CODE_BSS, API_URL)

#---------------------  Onglets ---------------------

tab_apercu, tab_feature, tab_analyse, tab_prediction, tab_documentation = st.tabs(["Identity", "Features", "Analyse", "Prédiction", "Documentations"])
with tab_apercu:
    render_identity (df_interim)

with tab_feature:
    render_features(df_interim)

with tab_analyse:
    render_stats(df_processed)

with tab_prediction:
    render_predictions()
    
with tab_documentation:
    render_documentation()