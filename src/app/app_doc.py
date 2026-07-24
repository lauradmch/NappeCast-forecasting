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

