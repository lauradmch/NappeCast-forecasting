"""
Contenu de l'onglet Documentations

"""


# --------------------------- LIBRARY --------------------------------
import ast
import pandas as pd
import streamlit as st
import requests
import plotly.express as px 
import os
import yaml

from src.config import load_config

# ---------------------------- VARIABLES ---------------------------

CONFIG = load_config()

API_URL                 = os.getenv("API_URL", "http://localhost:8000")

# ---------------------------- METHODES ---------------------------

def render_predictions()-> None:
    if st.button("Vérifier l'état des modèles"):
        try:
            response = requests.get(f"{API_URL}/model/info/all", timeout=10)
            response.raise_for_status()
            info = response.json()

            rows = []
            for model_type, data in info.items():
                rows.append({
                    "Modèle": model_type,
                    "Chargé": "✅" if data["loaded"] else "❌",
                    "Source": data["source"],
                    "Chargé le": data["loaded_at"] or "-",
                    "Détail": data["detail"] or "-",
                })

            df_status = pd.DataFrame(rows)
            st.table(df_status)

        except requests.exceptions.RequestException as e:
            st.error(f"Impossible de récupérer l'état des modèles : {e}")

    if st.button("Comparer les 3 modèles"):
        with st.spinner("Calcul des prédictions en cours..."):
            try:
                response = requests.get(f"{API_URL}/compare", timeout=60)
                response.raise_for_status()
                results = response.json()

                rows = []
                for model_type, res in results.items():
                    if "error" in res:
                        st.warning(f"{model_type} : erreur — {res['error']}")
                        continue
                    rows.append({"Modèle": model_type, "Date": res["date"], "Prédiction": res["prediction"]})

                df_compare = pd.DataFrame(rows)
                st.dataframe(df_compare)

            except requests.exceptions.RequestException as e:
                st.error(f"Erreur lors de l'appel à l'API : {e}")