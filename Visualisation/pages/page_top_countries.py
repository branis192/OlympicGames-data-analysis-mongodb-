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

# --- FONCTION DE RÉCUPÉRATION DES DONNÉES ---
@st.cache_data
def get_top_10_countries():
    """
    Récupère le top 10 des pays par nombre total de médailles.
    """
    pipeline = [
        # Étape 1 : Filtrer uniquement les résultats avec une médaille
        {"$match": {"medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        
        # Étape 2 : Regrouper par code pays (noc) et compter les médailles
        {"$group": {"_id": "$noc", "total_medailles": {"$sum": 1}}},
        
        # Étape 3 : Trier par le total des médailles en ordre décroissant
        {"$sort": {"total_medailles": -1}},
        
        # Étape 4 : Garder uniquement les 10 premiers
        {"$limit": 10},
        
        # Étape 5 : Renommer les champs pour le DataFrame
        {"$project": {"_id": 0, "Pays": "$_id", "Nombre de Médailles": "$total_medailles"}}
    ]
    
    data = list(db.results.aggregate(pipeline))
    
    if not data:
        return pd.DataFrame()
        
    return pd.DataFrame(data)


# --- INTERFACE UTILISATEUR (UI) ---

st.title("🏆 Top 10 des Nations les Plus Médaillées")
st.markdown("Classement des pays en fonction du nombre total de médailles (Or, Argent et Bronze) remportées dans toutes les disciplines confondues.")

# Chargement des données
df_top_countries = get_top_10_countries()

if not df_top_countries.empty:
    # Pour un graphique horizontal, il faut trier les données dans l'autre sens
    # afin que la barre la plus haute soit en haut.
    df_top_countries = df_top_countries.sort_values("Nombre de Médailles", ascending=True)

    # Création du graphique en barres horizontales
    fig = px.bar(
        df_top_countries,
        x="Nombre de Médailles",
        y="Pays",
        orientation='h', # C'est la clé pour un graphique horizontal
        text="Nombre de Médailles", # Affiche le nombre sur les barres
        labels={
            "Pays": "Pays (Code NOC)",
            "Nombre de Médailles": "Nombre Total de Médailles"
        },
        title="Top 10 des Pays par Total de Médailles"
    )

    # Amélioration du design
    fig.update_traces(
        textposition='outside',
        marker_color='#FF914D' # Une couleur orange/or
    )
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'}, # Assure le bon ordre
        xaxis_title="Total de Médailles",
        yaxis_title="" # On enlève le titre de l'axe Y pour plus de clarté
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Option pour afficher le tableau des données
    with st.expander("Voir le classement détaillé"):
        st.dataframe(
            df_top_countries.sort_values("Nombre de Médailles", ascending=False),
            use_container_width=True,
            hide_index=True
        )

else:
    st.warning("Aucune donnée sur les médailles n'a pu être chargée.")