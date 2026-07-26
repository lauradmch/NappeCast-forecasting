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

from src.app.app_doc import render_documentation
from src.helper.aws import read_csv_in_s3

#--------------------- VARIABLES ---------------------
CONFIG = load_config()

API_URL                 = os.getenv("API_URL", "http://localhost:8000")
CODE_BSS                = ",".join(CONFIG["api"]["piezometer"]["code_bss"])
STATION_RAW_FILENAME    = Path(CONFIG["paths"]["data"]["raw"]) / f"{CONFIG['paths']['station']['raw_filename']}.csv"
DATASET_FILENAME        = Path(CONFIG["paths"]["data"]["interim"]) / f"{CONFIG['paths']['merged_filename']}.csv"
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
    df_station = read_csv_in_s3(S3_SESSION, BUCKET_NAME, STATION_RAW_FILENAME)
    df_dataset = read_csv_in_s3(S3_SESSION, BUCKET_NAME, DATASET_FILENAME)
    return df_station, df_dataset

df_station, df_processed = load_data()

# --------------------- Sidebar menu ---------------------

render_sidebar(df_station, CODE_BSS, API_URL)

#---------------------  Onglets ---------------------

tab_apercu, tab_feature, tab_analyse, tab_prediction, tab_documentation = st.tabs(["Identity", "Features", "Analyse", "Prédiction", "Documentations"])
with tab_apercu:
    render_identity (df_processed)

with tab_feature:
    render_features(df_processed)

with tab_analyse:
    render_documentation()

with tab_prediction:
    render_predictions()
    
with tab_documentation:
    render_documentation()