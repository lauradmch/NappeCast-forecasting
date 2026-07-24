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

def render_predictions()-> None:
    st.write("Résultats du modèle ML...")
    