"""
Contenu de la sidebar

"""


# --------------------------- LIBRARY --------------------------------
import ast
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from src.app import api_client
from src.config import load_config

# ---------------------------- VARIABLES ---------------------------
CONFIG = load_config()

API_URL = os.getenv("API_URL", "http://localhost:8000")

# ---------------------------- METHODES ---------------------------
def _parse_list_str(value: str) -> str:
    """Convertit une chaîne du type "['A', 'B']" en "A, B"."""
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return ", ".join(parsed)
    except (ValueError, SyntaxError):
        pass
    return value

def render_sidebar(df_station: pd.DataFrame, code_bss: str) -> None:
    station = df_station.iloc[0]  # ligne unique -> Series pour l'affichage texte
    with st.sidebar:
        st.header(f"**Piezometer {station['libelle_pe']}**")
        st.caption(f"BSS {station['bss_id']} — {station['code_bss']}")
        fig = px.scatter_mapbox(
            df_station,
            lat="latitude",
            lon="longitude",
            hover_name="libelle_pe",
            zoom=6
        )
        fig.update_layout(
            mapbox_style="open-street-map",
            uirevision="constant",
            height=250,
            margin=dict(l=0, r=0, t=0, b=0),
        )
        fig.update_traces(marker=dict(size=16, color="#FF4B4B"))
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Localisation")
        st.write(f"**Commune :** {station['nom_commune']} ({station['code_commune_insee']})")
        st.write(f"**Département :** {station['nom_departement']} ({station['code_departement']})")
        st.write(f"**Altitude :** {station['altitude_station']} m NGF")
        st.write(f"**Coordonnées :** {station['latitude']:.5f}, {station['longitude']:.5f}")
        st.subheader("Suivi piézométrique")
        st.write(f"**Période de mesure :** {station['date_debut_mesure']} → {station['date_fin_mesure']}")
        st.write(f"**Nombre de mesures :** {station['nb_mesures_piezo']}")
        st.write(f"**Profondeur d'investigation :** {station['profondeur_investigation']} m")
        st.subheader("Masse d'eau / BDLISA")
        st.write(f"**Masse d'eau :** {_parse_list_str(station['noms_masse_eau_edl'])}")
        st.write(f"**Code masse d'eau :** {_parse_list_str(station['codes_masse_eau_edl'])}")
        st.write(f"**Entité BDLISA :** {_parse_list_str(station['codes_bdlisa'])}")
        st.caption(f"Dernière mise à jour : {station['date_fin_mesure']}")

        st.subheader("API")

        if st.button("Vérifier la connexion à l'API"):
            try:
                api_client.get_health()
                st.success("API disponible ✅")
            except requests.RequestException as e:
                st.error(f"API indisponible : {e}")

        if st.button("Mettre à jour les données"):
            try:
                with st.spinner("Traitement en cours, cela peut prendre jusqu'à une minute..."):
                    result = api_client.run_collect_pipeline()
                st.cache_data.clear()   # force app.py to reload the CSVs from S3
                st.success(f"Données mises à jour : {result['processed_rows']} lignes")
            except requests.RequestException as e:
                st.error(f"API indisponible : {e}")

        if st.button("Vérifier l'état des modèles"):
            try:
                info = api_client.get_all_models_info()
            except requests.RequestException as e:
                st.error(f"Could not retrieve model status: {e}")
            else:
                rows = [
                    {
                        "Model": model_type,
                        "Loaded": "✅" if data["loaded"] else "❌",
                        "Source": data["source"],
                        "Loaded at": data["loaded_at"] or "-",
                        "Detail": data["detail"] or "-",
                    }
                    for model_type, data in info.items()
                ]
                st.table(pd.DataFrame(rows))