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

# --- FONCTION DE GROUPEMENT DES DISCIPLINES ---
def get_discipline_group(event_name):
    """
    Classe une discipline dans une grande catégorie pour simplifier la visualisation.
    """
    event_lower = event_name.lower()
    if any(s in event_lower for s in ['100 metres', '200 metres', '400 metres', 'relay']):
        return 'Sprint / Relais'
    if any(s in event_lower for s in ['shot put', 'discus throw', 'javelin throw', 'hammer throw']):
        return 'Lancers'
    if any(s in event_lower for s in ['long jump', 'high jump', 'triple jump', 'pole vault']):
        return 'Sauts'
    if any(s in event_lower for s in ['marathon', 'walk', '5,000 metres', '10,000 metres', 'steeplechase']):
        return 'Fond / Demi-Fond'
    if any(s in event_lower for s in ['decathlon', 'heptathlon', 'pentathlon']):
        return 'Épreuves Combinées'
    if any(s in event_lower for s in ['hurdles']):
        return 'Haies'
    return 'Autre'

# --- FONCTION DE RÉCUPÉRATION DES DONNÉES ---
@st.cache_data
def get_medalist_morphology():
    """
    Récupère la taille et le poids des médaillés.
    """
    pipeline = [
        {"$match": {"medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {
            "$lookup": {
                "from": "athletes",
                "localField": "athlete_id",
                "foreignField": "_id",
                "as": "athlete_bio"
            }
        },
        {"$unwind": "$athlete_bio"},
        {
            # Garder seulement les athlètes avec des données de taille et poids complètes
            "$match": {
                "athlete_bio.height": {"$exists": True, "$ne": None},
                "athlete_bio.weight": {"$exists": True, "$ne": None}
            }
        },
        {
            "$project": {
                "_id": 0,
                "athlete": "$athlete_name",
                "sex": "$athlete_bio.sex",
                "height": "$athlete_bio.height",
                "weight": "$athlete_bio.weight",
                "event": "$event"
            }
        },
        {"$limit": 5000} # Limiter la quantité de données pour de meilleures performances
    ]
    data = list(db.results.aggregate(pipeline))
    
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    # Appliquer la fonction de groupement
    df['Groupe Discipline'] = df['event'].apply(get_discipline_group)
    return df

# --- INTERFACE UTILISATEUR (UI) ---
st.title("🔬 Analyse Morphologique par Type d'Épreuve")
st.markdown("Ce nuage de points montre la corrélation entre la taille et le poids des athlètes médaillés. Chaque point représente un(e) athlète, et la couleur indique sa catégorie de discipline.")

# Chargement et préparation des données
df_morph = get_medalist_morphology()

# Filtre par sexe
sex_filter = st.radio("Filtrer par sexe :", ["Tous", "Hommes", "Femmes"], horizontal=True)

if sex_filter == "Hommes":
    df_filtered = df_morph[df_morph['sex'] == 'Male']
elif sex_filter == "Femmes":
    df_filtered = df_morph[df_morph['sex'] == 'Female']
else:
    df_filtered = df_morph


if not df_filtered.empty:
    # Création du nuage de points
    fig = px.scatter(
        df_filtered,
        x="height",
        y="weight",
        color="Groupe Discipline",  # La clé de la visualisation
        hover_data=['athlete', 'event'], # Infos supplémentaires au survol
        labels={
            "height": "Taille (cm)",
            "weight": "Poids (kg)",
            "Groupe Discipline": "Catégorie d'Épreuve"
        },
        title="Relation Taille-Poids des Médaillés par Catégorie de Discipline"
    )
    
    # Amélioration de l'apparence
    fig.update_layout(
        legend_title_text='Catégories'
    )
    fig.update_traces(marker=dict(size=8, opacity=0.7))

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Aucune donnée disponible pour créer le graphique.")