#---------------------------------------------------------------------------------
# Streamlit interface
#---------------------------------------------------------------------------------

# Import libraries
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

CONFIG = load_config()
API_URL = os.getenv("API_URL", "http://localhost:8000")

#--------------------- 🧠 Configuration section ---------------------
# st.set_page_config() defines metadata and layout of your Streamlit app.
# You can set the page title, the emoji/icon, and whether the layout is "wide" or "centered".
st.set_page_config(
    page_title='NappeCast',
    page_icon= '💧',
    layout='wide'
)

#--------------------- 🎨 App header ---------------------
st.title("Welcome in our application to deep dive into the nappecast.")

st.markdown("""
            This application was developped by Laura D., Ronan G. 
            and Adrien C. during there AI Fullstack bootcamp with Jedha's school.
            The context and objectives of this project are summarized in the 'Purpose & 
            Objectives' section.
            \nWe hope you will have a lovely experience going through our work!         
            """)

# url = "https://rainea.fr/wp-content/uploads/2025/07/iStock-514985574.jpg"
# st.image(url, caption= 'nappecast', use_container_width=True)


#--------------------- 📦 Load data ---------------------



# Connexion to S3 server on AWS
s3 = boto3.client("s3")
bucket_name = CONFIG["s3"]["bucket"]
s3 = boto3.client("s3")

@st.cache_data
def load_data():
    key = Path(CONFIG["paths"]["data"]["interim"]) / f"{CONFIG['paths']['merged_filename']}.csv"
    obj = s3.get_object(Bucket=CONFIG["s3"]["bucket"], Key=str(key))
    df = pd.read_csv(StringIO(obj["Body"].read().decode("utf-8")))
    return df
data = load_data()

#--------------------- test API ---------------------
if st.button("Vérifier la connexion à l'API"):
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        r.raise_for_status()
        st.success("API disponible ✅")
    except Exception as e:
        st.error(f"API indisponible : {e}")

            

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





st.markdown("<a id='Sources'></a>", unsafe_allow_html=True)
st.subheader("Data sources")





#--------------------- Exploratory Data Analysis ---------------------

st.header("Exploratory Data Analysis")
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




st.header("Nappecast level prediction")
st.markdown("<a id='ML-models'></a>", unsafe_allow_html=True)
st.subheader("Machine Learning models")





st.markdown("<a id='DL-models'></a>", unsafe_allow_html=True)
st.subheader("Deep Learning models")



# H1 st.title("Titre principal")
# H2 st.header("Section")                  
# H3 st.subheader("Sous-section")          
# Méthode générique st.write("Du texte ou n'importe quoi") 
# Markdown complet st.markdown("**Gras**, *italique*")   
# Petit texte gris st.caption("Légende discrète")        
# Bloc de code coloré st.code("print('Hello')", language="python")  
# Ligne horizontale st.divider()                          


