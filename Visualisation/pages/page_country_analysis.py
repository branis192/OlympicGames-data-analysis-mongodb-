import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide")

# --- CONNEXION À MONGODB ---
@st.cache_resource
def init_connection():
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        client.server_info()
        return client
    except Exception as e:
        st.error(f"Erreur de connexion à MongoDB : {e}")
        return None

client = init_connection()
if not client:
    st.stop()
db = client.athle_db

# --- FONCTIONS DE RÉCUPÉRATION DE DONNÉES ---
@st.cache_data
def get_all_country_codes():
    """Récupère la liste de tous les codes pays (NOC) ayant gagné au moins une médaille."""
    codes = db.results.distinct("noc", {"medal": {"$in": ["Gold", "Silver", "Bronze"]}})
    return sorted(codes)

@st.cache_data
def get_medals_by_discipline_for_country(country_noc):
    """
    Récupère le nombre de médailles par discipline pour un pays donné.
    """
    pipeline = [
        {"$match": {"noc": country_noc, "medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {"$group": {"_id": "$event", "total_medailles": {"$sum": 1}}},
        {"$sort": {"total_medailles": -1}},
        {"$project": {"Discipline": "$_id", "Médailles": "$total_medailles", "_id": 0}},
        {"$limit": 15} # On garde le top 15 pour la clarté
    ]
    data = list(db.results.aggregate(pipeline))
    return pd.DataFrame(data)

@st.cache_data
def get_medals_over_time_for_country(country_noc):
    """
    Récupère l'évolution du nombre de médailles par année pour un pays donné.
    """
    pipeline = [
        {"$match": {"noc": country_noc, "medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {"$group": {"_id": "$year", "total_medailles": {"$sum": 1}}},
        {"$sort": {"_id": 1}}, # Trier par année croissante
        {"$project": {"Année": "$_id", "Médailles": "$total_medailles", "_id": 0}}
    ]
    data = list(db.results.aggregate(pipeline))
    return pd.DataFrame(data)

# --- INTERFACE UTILISATEUR (UI) ---

st.title("🌍 Analyse Détaillée par Pays")
st.markdown("Choisissez un pays pour découvrir ses disciplines de prédilection et suivre l'évolution de ses performances au fil des ans.")

# Menu de sélection du pays
country_list = get_all_country_codes()
# Sélectionner les USA par défaut, car ils ont beaucoup de données
default_index = country_list.index("USA") if "USA" in country_list else 0
selected_country = st.selectbox("Sélectionnez un Pays (Code NOC)", country_list, index=default_index)


if selected_country:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Points Forts de {selected_country}")
        df_disciplines = get_medals_by_discipline_for_country(selected_country)
        
        if not df_disciplines.empty:
            # Le treemap est excellent pour voir les proportions
            fig1 = px.treemap(
                df_disciplines,
                path=['Discipline'], 
                values='Médailles',
                title=f"Top 15 des disciplines les plus médaillées pour {selected_country}"
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info(f"Aucune donnée de médaille par discipline trouvée pour {selected_country}.")

    with col2:
        st.subheader(f"Performance Historique de {selected_country}")
        df_timeline = get_medals_over_time_for_country(selected_country)
        
        if not df_timeline.empty:
            fig2 = px.line(
                df_timeline,
                x="Année",
                y="Médailles",
                markers=True,
                title=f"Nombre de médailles remportées par édition"
            )
            fig2.update_layout(xaxis_title="Année", yaxis_title="Nombre de médailles")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(f"Aucune donnée historique de médailles trouvée pour {selected_country}.")