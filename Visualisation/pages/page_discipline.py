import streamlit as st
from pymongo import MongoClient
import pandas as pd

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide")

# --- CONNEXION À MONGODB (fonction réutilisable) ---
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

# --- FONCTIONS SPÉCIFIQUES À LA DISCIPLINE ---
@st.cache_data
def get_all_discipline_names():
    disciplines = db.events.distinct("event_name")
    return sorted(disciplines)

@st.cache_data
def get_medals_by_country_for_discipline(event_name):
    pipeline = [
        {"$match": {"event": event_name, "medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {"$group": {"_id": "$noc",
                    "Gold": {"$sum": {"$cond": [{"$eq": ["$medal", "Gold"]}, 1, 0]}},
                    "Silver": {"$sum": {"$cond": [{"$eq": ["$medal", "Silver"]}, 1, 0]}},
                    "Bronze": {"$sum": {"$cond": [{"$eq": ["$medal", "Bronze"]}, 1, 0]}}}},
        {"$addFields": {"Total": {"$add": ["$Gold", "$Silver", "$Bronze"]}}},
        {"$sort": {"Gold": -1, "Silver": -1, "Bronze": -1}},
        {"$project": {"Pays": "$_id", "Gold": 1, "Silver": 1, "Bronze": 1, "Total": 1, "_id": 0}}
    ]
    return pd.DataFrame(list(db.results.aggregate(pipeline)))

@st.cache_data
def get_top_medallists_for_discipline(event_name):
    pipeline = [
        {"$match": {"event": event_name, "medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {"$group": {"_id": "$athlete_name",
                    "Gold": {"$sum": {"$cond": [{"$eq": ["$medal", "Gold"]}, 1, 0]}},
                    "Silver": {"$sum": {"$cond": [{"$eq": ["$medal", "Silver"]}, 1, 0]}},
                    "Bronze": {"$sum": {"$cond": [{"$eq": ["$medal", "Bronze"]}, 1, 0]}}}},
        {"$addFields": {"Total": {"$add": ["$Gold", "$Silver", "$Bronze"]}}},
        {"$sort": {"Gold": -1, "Silver": -1, "Bronze": -1, "Total": -1}},
        {"$limit": 10},
        {"$project": {"Athlète": "$_id", "Gold": 1, "Silver": 1, "Bronze": 1, "Total": 1, "_id": 0}}
    ]
    return pd.DataFrame(list(db.results.aggregate(pipeline)))

# --- AFFICHAGE DE LA PAGE DISCIPLINE ---
st.title("🏃 Fiche Discipline")
st.markdown("Statistiques des médailles par pays et par athlète pour une épreuve donnée.")

discipline_names = get_all_discipline_names()
# Sélection de "100 metres" par défaut pour l'exemple
default_index = discipline_names.index("100 metres") if "100 metres" in discipline_names else 0
selected_discipline = st.selectbox("Sélectionnez une discipline", discipline_names, index=default_index)

if selected_discipline:
    st.subheader(f"Médailles par Pays pour : {selected_discipline}")
    df_countries = get_medals_by_country_for_discipline(selected_discipline)
    if not df_countries.empty:
        st.dataframe(df_countries, hide_index=True, use_container_width=True)
    else:
        st.info("Aucune médaille enregistrée.")
        
    st.divider()

    st.subheader(f"Top 10 des Athlètes Médaillés pour : {selected_discipline}")
    df_top_athletes = get_top_medallists_for_discipline(selected_discipline)
    if not df_top_athletes.empty:
        st.dataframe(df_top_athletes, hide_index=True, use_container_width=True)
    else:
        st.info("Aucun athlète médaillé trouvé.")