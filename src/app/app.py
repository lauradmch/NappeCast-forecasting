#---------------------------------------------------------------------------------
# Streamlit interface
#---------------------------------------------------------------------------------

# Import libraries
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px 
import plotly.graph_objects as go
import boto3
from io import StringIO
from dotenv import load_dotenv
import os
import yaml

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

# @st.cache_data is a Streamlit decorator that caches function results.
# When you reload the app, data is read from the cache instead of reloading from the source.

# Connexion to S3 server on AWS
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")

base_dir = Path(__file__).resolve().parents[2]
config_path = base_dir / "configs" / "config.yaml"

with open(config_path, "r") as f:
    config = yaml.safe_load(f)

bucket_name = config["s3"]["bucket"]

s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region
)

@st.cache_data
def load_data():
    response = s3.get_object(Bucket=bucket_name, Key="data/raw/2026/07/dataset.csv_20260722.csv")
    df = pd.read_csv(StringIO(response["Body"].read().decode("utf-8")))
    return df

data = load_data()

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


