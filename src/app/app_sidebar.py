"""
Contenu de la sidebar

"""


# --------------------------- LIBRARY --------------------------------
import ast
import pandas as pd
import streamlit as st
import requests
import plotly.express as px 


# ---------------------------- VARIABLES ---------------------------


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

def render_sidebar(df_station: pd.DataFrame, 
                   code_bss: str, 
                   api_url: str) -> None:
    station = df_station.iloc[0]  # ligne unique -> Series pour l'affichage texte
    with st.sidebar:
        st.header(f"**{station['libelle_pe']}**")
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
        st.caption(f"Dernière mise à jour : {station['date_maj']}")
        st.subheader("API")
        if st.button("Vérifier la connexion à l'API"):
            try:
                r = requests.get(f"{api_url}/health", timeout=5)
                r.raise_for_status()
                st.success("API disponible ✅")
            except Exception as e:
                st.error(f"API indisponible : {e}")
