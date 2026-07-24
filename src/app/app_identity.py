"""
Contenu d'onglet identity'

"""

# --------------------------- LIBRARY --------------------------------
import ast
import pandas as pd
import streamlit as st
import requests
import plotly.express as px 

# ---------------------------- VARIABLES ---------------------------


# ---------------------------- METHODES ---------------------------

def render_identity (df_processed : pd.DataFrame)-> None:
    st.markdown("""
            This application was developped by Laura D., Ronan G. 
            and Adrien C. during there AI Fullstack bootcamp with Jedha's school.
            The context and objectives of this project are summarized in the 'Purpose & 
            Objectives' section.
            nWe hope you will have a lovely experience going through our work!         
            """)

    # suivi du niveau
    fig = px.line(
        df_processed,
        x="date_index",
        y="niveau_nappe_eau",
        title="Évolution du niveau de la nappe",
        labels={
            "date_index": "Date",
            "niveau_nappe_eau": "Niveau nappe (m)"
        }
    )
    fig.update_layout(
            mapbox_style="open-street-map",
            uirevision="constant",
            height=250,
            margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)
