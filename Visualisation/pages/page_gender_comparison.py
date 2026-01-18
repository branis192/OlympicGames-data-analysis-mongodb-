import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="Analyse de Genre - JO", page_icon="⚥")

# --- CONNEXION À MONGODB ---
@st.cache_resource
def init_connection():
    try:
        client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
        client.server_info()
        return client
    except Exception as e:
        st.error(f"Erreur de connexion à MongoDB : {e}")
        return None

client = init_connection()
if not client:
    st.stop()
db = client.athle_db

# --- FONCTIONS DE RÉCUPÉRATION DES DONNÉES ---

@st.cache_data
def get_gender_data_global():
    """Récupère la répartition globale pour le Donut chart."""
    pipeline = [
        {"$match": {"medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {
            "$lookup": {
                "from": "athletes",
                "localField": "athlete_id",
                "foreignField": "_id",
                "as": "athlete_info"
            }
        },
        {"$unwind": "$athlete_info"},
        {
            "$group": {
                "_id": "$athlete_info.sex",
                "count": {"$sum": 1}
            }
        },
        {"$project": {"_id": 0, "Sexe": "$_id", "Nombre": "$count"}}
    ]
    return pd.DataFrame(list(db.results.aggregate(pipeline)))

@st.cache_data
def get_gender_evolution():
    pipeline = [
        {"$match": {"medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {"$lookup": {"from": "athletes", "localField": "athlete_id", "foreignField": "_id", "as": "info"}},
        {"$unwind": "$info"},
        {"$group": {"_id": {"year": "$year", "sex": "$info.sex"}, "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "Année": "$_id.year", "Sexe": "$_id.sex", "Médailles": "$count"}}
    ]
    return pd.DataFrame(list(db.results.aggregate(pipeline))).sort_values("Année")

@st.cache_data
def get_top_sports_by_gender(gender, individual_only=False):
    """Récupère les sports dominants, avec option pour filtrer les sports individuels."""
    match_filter = {"info.sex": gender, "medal": {"$in": ["Gold", "Silver", "Bronze"]}}
    
    # Si individuel uniquement, on exclut les termes liés aux équipes
    if individual_only:
        match_filter["event"] = {"$not": {"$regex": "Team|Relay|Group|Doubles|Pairs", "$options": "i"}}

    pipeline = [
        {"$lookup": {"from": "athletes", "localField": "athlete_id", "foreignField": "_id", "as": "info"}},
        {"$unwind": "$info"},
        {"$match": match_filter},
        {"$group": {"_id": "$event", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    return pd.DataFrame(list(db.results.aggregate(pipeline)))

@st.cache_data
def get_world_gender_data_global():
    """Répartition par sexe pour les podiums mondiaux."""
    pipeline = [
        {"$match": {"position": {"$in": [1, 2, 3, "1", "2", "3"]}}},
        {
            "$lookup": {
                "from": "athletes",
                "localField": "athlete",
                "foreignField": "name",
                "as": "athlete_info"
            }
        },
        {"$unwind": "$athlete_info"},
        {"$group": {"_id": "$athlete_info.sex", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "Sexe": "$_id", "Nombre": "$count"}}
    ]
    return pd.DataFrame(list(db.world_results.aggregate(pipeline)))

@st.cache_data
def get_world_gender_evolution():
    """Évolution par sexe aux Mondiaux (utilise championships_index pour l'année)."""
    pipeline = [
        {"$match": {"position": {"$in": [1, 2, 3, "1", "2", "3"]}}},
        {
            "$lookup": {
                "from": "championships_index",
                "localField": "event_name",
                "foreignField": "meeting_name",
                "as": "m_info"
            }
        },
        {"$unwind": "$m_info"},
        {
            "$lookup": {
                "from": "athletes",
                "localField": "athlete",
                "foreignField": "name",
                "as": "a_info"
            }
        },
        {"$unwind": "$a_info"},
        {
            "$group": {
                "_id": {"year": "$m_info.year", "sex": "$a_info.sex"},
                "count": {"$sum": 1}
            }
        },
        {"$project": {"_id": 0, "Année": "$_id.year", "Sexe": "$_id.sex", "Podiums": "$count"}}
    ]
    df = pd.DataFrame(list(db.world_results.aggregate(pipeline)))
    return df.sort_values("Année") if not df.empty else df
# --- INTERFACE UTILISATEUR (UI) ---

st.title("⚥ Analyse Comparative des Genres")

df_global = get_gender_data_global()
df_evolution = get_gender_evolution()

tab1, tab2 = st.tabs(["📊 Répartition & Évolution", "🏃‍♂️ Top Sports"])

with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Répartition Globale")
        if not df_global.empty:
            fig_donut = px.pie(
                df_global, names='Sexe', values='Nombre',
                hole=0.4, title="Total des Médailles par Sexe",
                color='Sexe', color_discrete_map={'Male': '#3498db', 'Female': '#e91e63'},
                template="plotly_dark"
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            
            total_medals = df_global['Nombre'].sum()
            st.write(f"Total des médailles analysées : **{total_medals:,}**")

    with col2:
        st.subheader("Évolution de la Parité")
        if not df_evolution.empty:
            fig_line = px.line(
                df_evolution, x="Année", y="Médailles", color="Sexe",
                markers=True, template="plotly_dark",
                color_discrete_map={'Male': '#3498db', 'Female': '#e91e63'}
            )
            st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    st.subheader("Disciplines les plus médaillées (Toutes catégories)")
    c1, c2 = st.columns(2)
    
    for i, g in enumerate(['Male', 'Female']):
        df_s = get_top_sports_by_gender(g, individual_only=False)
        with (c1 if i==0 else c2):
            st.write(f"**Top 10 - {g}**")
            fig = px.bar(df_s, x="count", y="_id", orientation='h', 
                         color_discrete_sequence=['#3498db' if g=='Male' else '#e91e63'])
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
            st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("Données extraites en temps réel de MongoDB - Dashboard Exploratoire")
