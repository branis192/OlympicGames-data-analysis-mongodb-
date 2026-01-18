# Fichier : 4_📈_Évolution_Disciplines.py (Version adaptée aux données existantes)

import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide")

# --- CONNEXION À MONGODB ---
@st.cache_resource
def init_connection():
    # ... (coller votre fonction de connexion ici) ...
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    client.server_info()
    return client
client = init_connection()
if not client: st.stop()
db = client.athle_db


# --- FONCTION DE RÉCUPÉRATION (SIMPLIFIÉE) ---
@st.cache_data
def get_discipline_evolution_by_gender_olympics_only():
    """
    Calcule le nombre de disciplines UNIQUEMENT pour les JO,
    séparées par sexe.
    """
    pipeline = [
        # La jointure reste nécessaire pour obtenir le sexe
        {"$lookup": {"from": "athletes", "localField": "athlete_id", "foreignField": "_id", "as": "athlete_info"}},
        {"$unwind": "$athlete_info"},
        # On peut retirer le groupement par compétition car il n'y en a qu'une
        {"$group": {"_id": {"year": "$year", "sex": "$athlete_info.sex", "event": "$event"}}},
        {"$group": {"_id": {"year": "$_id.year", "sex": "$_id.sex"}, "count_disciplines": {"$sum": 1}}},
        {"$project": {"_id": 0, "Année": "$_id.year", "Sexe": "$_id.sex", "Nombre de Disciplines": "$count_disciplines"}},
        {"$sort": {"Année": 1}}
    ]
    
    data = list(db.results.aggregate(pipeline))
    if not data: return pd.DataFrame()

    df = pd.DataFrame(data)
    df = df[df['Sexe'].isin(['Male', 'Female'])]
    # On renomme 'Male'/'Female' pour une légende plus jolie
    df['Sexe'] = df['Sexe'].replace({'Male': 'Épreuves Hommes', 'Female': 'Épreuves Femmes'})
    return df

# --- INTERFACE UTILISATEUR (UI) ---
st.title("📈 Évolution Historique des Disciplines Olympiques")
st.markdown("Ce graphique illustre l'évolution du nombre d'épreuves d'athlétisme aux Jeux Olympiques, montrant la progression vers la parité entre les épreuves masculines et féminines.")

df_evolution = get_discipline_evolution_by_gender_olympics_only()

if not df_evolution.empty:
    fig = px.line(
        df_evolution,
        x="Année",
        y="Nombre de Disciplines",
        color="Sexe", # La couleur est maintenant directement basée sur le sexe
        markers=True,
        title="Nombre d'épreuves d'athlétisme aux JO par édition"
    )
    fig.update_layout(
        xaxis_title="Année de l'édition",
        yaxis_title="Nombre d'épreuves",
        legend_title_text='Catégorie'
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Voir les données détaillées"):
        st.dataframe(df_evolution, use_container_width=True, hide_index=True)
else:
    st.warning("Impossible de charger les données d'évolution des disciplines.")