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
    """Récupère les codes pays uniques des deux bases."""
    # Pays des JO
    olympic_countries = db.results.distinct("noc", {"medal": {"$in": ["Gold", "Silver", "Bronze"]}})
    # Pays des Mondiaux
    world_countries = db.world_results.distinct("country", {"position": {"$in": [1, 2, 3, "1", "2", "3"]}})
    
    # Fusion et tri unique
    combined = list(set(olympic_countries) | set(world_countries))
    return sorted([c for c in combined if c])

@st.cache_data
def get_combined_medals_by_discipline(country_noc):
    # 1. Top 5 JO
    pipe_oly = [
        {"$match": {"noc": country_noc, "medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {"$group": {"_id": "$event", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
        {"$project": {"Discipline": "$_id", "Médailles": "$count", "Source": "Olympics", "_id": 0}}
    ]
    df_oly = pd.DataFrame(list(db.results.aggregate(pipe_oly)))

    # 2. Top 5 Mondiaux
    pipe_world = [
        {"$match": {"country": country_noc, "position": {"$in": [1, 2, 3, "1", "2", "3"]}}},
        {"$group": {"_id": "$event", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
        {"$project": {"Discipline": "$_id", "Médailles": "$count", "Source": "World Championships", "_id": 0}}
    ]
    df_world = pd.DataFrame(list(db.world_results.aggregate(pipe_world)))

    return pd.concat([df_oly, df_world], ignore_index=True)

@st.cache_data
def get_combined_timeline(country_noc):
    # --- PARTIE OLYMPIQUE ---
    pipe_oly = [
        {"$match": {"noc": country_noc, "medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {"$group": {"_id": "$year", "total": {"$sum": 1}}},
        {"$project": {"Année": "$_id", "Médailles": "$total", "Source": "Olympics", "_id": 0}}
    ]
    df_oly = pd.DataFrame(list(db.results.aggregate(pipe_oly)))

    # --- PARTIE CHAMPIONNATS DU MONDE ---
    pipe_world = [
        {"$match": {
            "country": country_noc, 
            "position": {"$in": [1, 2, 3, "1", "2", "3"]}
        }},
        {
            "$lookup": {
                "from": "championships_index",
                "localField": "event_name",    # Nom dans world_results
                "foreignField": "meeting_name", # Nom dans championships_index (vérifie bien !)
                "as": "info"
            }
        },
        {"$unwind": "$info"},
        {"$group": {"_id": "$info.year", "total": {"$sum": 1}}},
        {"$project": {"Année": "$_id", "Médailles": "$total", "Source": "World Championships", "_id": 0}}
    ]
    df_world = pd.DataFrame(list(db.world_results.aggregate(pipe_world)))

    # Fusion des DataFrames
    df_final = pd.concat([df_oly, df_world], ignore_index=True)
    
    if not df_final.empty:
        df_final['Année'] = pd.to_numeric(df_final['Année'], errors='coerce')
        # On s'assure que 'Source' est bien traité comme une catégorie pour Plotly
        df_final = df_final.dropna(subset=['Année']).sort_values(["Année", "Source"])
        
    return df_final
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
        st.subheader(f"🥇 Disciplines de prédilection")
        df_disc = get_combined_medals_by_discipline(selected_country)
        
        if not df_disc.empty:
            # Treemap avec distinction de la source par couleur
            fig1 = px.treemap(
                df_disc,
                path=['Source', 'Discipline'], 
                values='Médailles',
                color='Source',
                color_discrete_map={'Olympics': '#FFD700', 'World Championships': '#C0C0C0'},
                title="Répartition par Source et Discipline"
            )
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader(f"📈 Comparaison Historique")
        df_time = get_combined_timeline(selected_country)
        
        if not df_time.empty:
            # Graphe linéaire avec deux lignes (une par source)
            fig2 = px.line(
                df_time,
                x="Année",
                y="Médailles",
                color="Source",
                markers=True,
                title="Évolution des médailles : JO vs Mondiaux",
                color_discrete_map={'Olympics': '#FF4B4B', 'World Championships': '#0068C9'}
            )
            st.plotly_chart(fig2, use_container_width=True)