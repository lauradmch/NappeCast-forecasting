#---------------------------------------------------------------------------------
# Streamlit interface
#---------------------------------------------------------------------------------

#--------------------- LIBRARY ---------------------
from pathlib import Path

import pandas as pd
import streamlit as st

from src.app.app_doc import render_documentation
from src.app.app_features import render_features
from src.app.app_predictions import render_predictions
from src.app.app_sidebar import render_sidebar
from src.app.app_stats import render_stats
from src.config import load_config
from datetime import date
from src.app import api_client

#--------------------- VARIABLES ---------------------
CONFIG = load_config()

CODE_BSS    = ",".join(CONFIG["api"]["piezometer"]["code_bss"])
DATE_TRAIN  = date.today()
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
    [data-testid="stMetric"] {
    background-color: #f4f4f7;
    border-radius: 4px;
    padding: 15px;
    border-left: 4px solid #D85A30;
    }
    [data-testid="stMetricLabel"] {
        color: #5f5f5f;
    }
    [data-testid="stMetricValue"] {
        color: #5f5f5f;
    }
    </style>
    """, unsafe_allow_html=True)

#---------------------  Load data ---------------------
@st.cache_data
def load_data(code_bss: str, end_date: datetime)-> tuple[pd.DataFrame, pd.DataFrame]:
    df_station      = api_client.post_station(code_bss)
    df_processed    = api_client.post_processed(code_bss, end_date)

    return df_station, df_processed

df_station, df_processed = load_data(CODE_BSS, DATE_TRAIN)

# --------------------- Sidebar menu ---------------------

render_sidebar(df_station, CODE_BSS)

#---------------------  Onglets ---------------------

tab_documentation, tab_feature, tab_analyse, tab_prediction = st.tabs(["Documentation", "Data", "Analyse", "Prédictions"])

with tab_documentation:
    render_documentation()

with tab_feature:
    render_features(CODE_BSS, df_processed)

with tab_analyse:
    render_stats(CODE_BSS, df_processed)

with tab_prediction:
    render_predictions(CODE_BSS, DATE_TRAIN, df_processed)
    
