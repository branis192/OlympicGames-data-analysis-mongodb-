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

# --- FONCTIONS SPÉCIFIQUES À LA DISCIPLINE (MODIFIÉES) ---
@st.cache_data
def get_all_discipline_names():
    """### MODIFIÉ ###
    Fusionne les noms de disciplines des JO et des CM."""
    events_jo = db.results.distinct("event")
    events_cm = db.world_results.distinct("event")
    # Utilise set() pour garantir l'unicité avant de trier
    all_events = sorted(list(set(events_jo + events_cm)))
    return all_events

@st.cache_data
def get_medals_by_country_for_discipline(event_name):
    """### MODIFIÉ ###
    Agrège les médailles par pays depuis les DEUX collections."""
    pipeline = [
        {"$match": {"event": event_name, "medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {"$group": {"_id": "$noc", "Gold": {"$sum": {"$cond": [{"$eq": ["$medal", "Gold"]}, 1, 0]}}, "Silver": {"$sum": {"$cond": [{"$eq": ["$medal", "Silver"]}, 1, 0]}}, "Bronze": {"$sum": {"$cond": [{"$eq": ["$medal", "Bronze"]}, 1, 0]}}}},
    ]
    
    # 1. Requête sur les deux collections
    data_jo = list(db.results.aggregate(pipeline))
    data_cm = list(db.world_results.aggregate(pipeline))
    
    if not data_jo and not data_cm: return pd.DataFrame()

    df_jo = pd.DataFrame(data_jo).rename(columns={'_id': 'Pays'})
    df_cm = pd.DataFrame(data_cm).rename(columns={'_id': 'Pays'})

    # 2. Concaténer les DataFrames
    df_combined = pd.concat([df_jo, df_cm], ignore_index=True)
    
    # 3. Grouper et sommer pour obtenir le total final
    if df_combined.empty: return pd.DataFrame()
    df_final = df_combined.groupby('Pays').sum().reset_index()
    
    # 4. Calculer le total et trier
    df_final['Total'] = df_final['Or'] + df_final['Argent'] + df_final['Bronze']
    df_final = df_final.sort_values(by=['Or', 'Argent', 'Bronze', 'Total'], ascending=False)
    
    return df_final[['Pays', 'Or', 'Argent', 'Bronze', 'Total']]


@st.cache_data
def get_top_medallists_for_discipline(event_name):
    """### MODIFIÉ ###
    Agrège les médailles par athlète depuis les DEUX collections."""
    pipeline = [
        {"$match": {"event": event_name, "medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {"$group": {"_id": "$athlete_name", "Gold": {"$sum": {"$cond": [{"$eq": ["$medal", "Gold"]}, 1, 0]}}, "Silver": {"$sum": {"$cond": [{"$eq": ["$medal", "Silver"]}, 1, 0]}}, "Bronze": {"$sum": {"$cond": [{"$eq": ["$medal", "Bronze"]}, 1, 0]}}}},
    ]

    data_jo = list(db.results.aggregate(pipeline))
    data_cm = list(db.world_results.aggregate(pipeline))

    if not data_jo and not data_cm: return pd.DataFrame()

    df_jo = pd.DataFrame(data_jo).rename(columns={'_id': 'Athlète'})
    df_cm = pd.DataFrame(data_cm).rename(columns={'_id': 'Athlète'})
    
    df_combined = pd.concat([df_jo, df_cm], ignore_index=True)

    if df_combined.empty: return pd.DataFrame()
        
    df_final = df_combined.groupby('Athlète').sum().reset_index()

    df_final['Total'] = df_final['Or'] + df_final['Argent'] + df_final['Bronze']
    # Trier et prendre les 10 meilleurs
    df_final = df_final.sort_values(by=['Or', 'Argent', 'Bronze', 'Total'], ascending=False).head(10)

    return df_final[['Athlète', 'Or', 'Argent', 'Bronze', 'Total']]

# --- AFFICHAGE DE LA PAGE DISCIPLINE (LÉGÈREMENT AJUSTÉ POUR LES EMOJIS) ---
st.title("🏃 Fiche Discipline")
st.markdown("Statistiques des médailles par pays et par athlète pour les JO et les Championnats du Monde.")

discipline_names = get_all_discipline_names()
# Sélection de "100 metres" par défaut pour l'exemple
if discipline_names:
    default_index = discipline_names.index("100 metres") if "100 metres" in discipline_names else 0
    selected_discipline = st.selectbox("Sélectionnez une discipline", discipline_names, index=default_index)

    if selected_discipline:
        st.subheader(f"Médailles par Pays pour : {selected_discipline}")
        df_countries = get_medals_by_country_for_discipline(selected_discipline)
        if not df_countries.empty:
            df_countries.rename(columns={'Or': '🥇 Or', 'Argent': '🥈 Argent', 'Bronze': '🥉 Bronze', 'Total': '🏆 Total'}, inplace=True)
            st.dataframe(df_countries, hide_index=True, use_container_width=True)
        else:
            st.info("Aucune médaille enregistrée.")
            
        st.divider()

        st.subheader(f"Top 10 des Athlètes Médaillés pour : {selected_discipline}")
        df_top_athletes = get_top_medallists_for_discipline(selected_discipline)
        if not df_top_athletes.empty:
            df_top_athletes.rename(columns={'Or': '🥇 Or', 'Argent': '🥈 Argent', 'Bronze': '🥉 Bronze', 'Total': '🏆 Total'}, inplace=True)
            st.dataframe(df_top_athletes, hide_index=True, use_container_width=True)
        else:
            st.info("Aucun athlète médaillé trouvé.")
else:
    st.warning("Aucune discipline n'a pu être chargée.")