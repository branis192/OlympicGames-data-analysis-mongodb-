import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
from datetime import datetime

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

# --- FONCTION DE RÉCUPÉRATION ET DE CALCUL DES ÂGES ---
@st.cache_data
def get_medalist_ages(discipline_filter=None):
    """
    Exécute une agrégation pour joindre 'results' et 'athletes',
    calcule l'âge de chaque médaillé au moment de la compétition.
    Un filtre optionnel par discipline est possible.
    """
    # Étape 1 : Le filtre initial (matcher uniquement les médaillés)
    match_stage = {"$match": {"medal": {"$in": ["Gold", "Silver", "Bronze"]}}}
    
    # Si une discipline est sélectionnée, on l'ajoute au filtre
    if discipline_filter and discipline_filter != "Toutes":
        match_stage["$match"]["event"] = discipline_filter

    pipeline = [
        match_stage,
        # Étape 2 : Joindre avec la collection 'athletes'
        {
            "$lookup": {
                "from": "athletes",
                "localField": "athlete_id",
                "foreignField": "_id",
                "as": "athlete_bio"
            }
        },
        # Étape 3 : "$unwind" pour transformer le tableau 'athlete_bio' en objet
        {"$unwind": "$athlete_bio"},
        # Étape 4 : Projeter uniquement les champs nécessaires et calculer l'âge
        {
            "$project": {
                "_id": 0,
                "year": "$year",
                "born": "$athlete_bio.born",
                "sex": "$athlete_bio.sex"
            }
        },
        # Étape 5 : Une seconde projection en Python car le calcul de dates est plus simple
    ]

    data = list(db.results.aggregate(pipeline))

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    
    # Nettoyage et calcul de l'âge en Python/Pandas
    df.dropna(subset=['born', 'year'], inplace=True)
    df['born'] = pd.to_datetime(df['born'], errors='coerce')
    df['age'] = df['year'] - df['born'].dt.year
    
    # Filtrer les âges aberrants (erreurs de données probables)
    df = df[(df['age'] >= 10) & (df['age'] <= 60)]
    
    return df

@st.cache_data
def get_discipline_list_for_filter():
    """Récupère la liste des disciplines pour le filtre."""
    disciplines = db.events.distinct("event_name")
    return ["Toutes"] + sorted(disciplines)

# --- INTERFACE UTILISATEUR (UI) ---

st.title("📊 Analyse de l'Âge des Médaillés")

# Filtre pour la discipline
discipline_list = get_discipline_list_for_filter()
selected_discipline = st.selectbox("Filtrer par discipline :", options=discipline_list)

# Chargement et calcul des données
df_ages = get_medalist_ages(selected_discipline)

if not df_ages.empty:
    # --- VISUALISATION : VIOLIN PLOT ÉLÉGANT ---
    fig = px.violin(
        df_ages,
        y="age",
        x="sex",
        color="sex",
        box=True,          # Affiche la boîte à moustaches à l'intérieur
        points="all",      # Affiche les petits points (jitter) sur le côté
        hover_data=["year"],
        title=f"Distribution et Densité de l'âge : {selected_discipline}",
        labels={"age": "Âge", "sex": "Sexe"},
        color_discrete_map={'Male': '#3498db', 'Female': '#e91e63'}, # Couleurs plus vives
        template="plotly_dark"
    )

    # Personnalisation avancée pour un look "Premium"
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Âge au moment de la performance",
        showlegend=False,
        font=dict(family="Arial", size=14),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    # Affichage du graphique principal
    st.plotly_chart(fig, use_container_width=True)

    # --- STATISTIQUES SOUS FORME DE CARTES ---
    st.divider()
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.metric("🏆 Âge Moyen", f"{df_ages['age'].mean():.1f} ans")
    with m2:
        # Âge le plus fréquent (Mode)
        mode_age = df_ages['age'].mode()[0]
        st.metric("🎯 Âge le plus fréquent", f"{int(mode_age)} ans")
    with m3:
        # Médianne
        st.metric("⚖️ Médiane", f"{df_ages['age'].median():.1f} ans")

else:
    st.warning("Aucune donnée disponible pour les filtres sélectionnés.")