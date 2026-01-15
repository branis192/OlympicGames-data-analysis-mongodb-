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
# --- Utilisation du nom de base de données correct ---
db = client.athle_db

# --- FONCTION DE RÉCUPÉRATION DES DONNÉES ---
@st.cache_data
def get_discipline_counts_over_time():
    """
    Récupère le nombre de disciplines par année et par type de compétition
    depuis la collection 'editions'.
    """
    # Projection pour ne récupérer que les champs nécessaires
    cursor = db.editions.find(
        {},
        {
            "_id": 0,
            "year": 1,
            "competition": 1,
            "count_disciplines": 1
        }
    ).sort("year", 1) # Trier par année croissante

    data = list(cursor)
    
    if not data:
        return pd.DataFrame()
        
    return pd.DataFrame(data)

# --- INTERFACE UTILISATEUR (UI) ---

st.title("📈 Évolution du Nombre de Disciplines")
st.markdown("""
Cette visualisation montre comment le nombre de disciplines d'athlétisme a évolué au fil du temps.
On peut observer la croissance des Jeux Olympiques et l'apparition des Championnats du Monde en 1983.
""")

# Chargement des données
df_evolution = get_discipline_counts_over_time()

if not df_evolution.empty:
    # Nettoyage simple des données pour garantir que 'year' est numérique
    df_evolution['year'] = pd.to_numeric(df_evolution['year'])
    
    # Création du graphique en ligne avec Plotly Express
    fig = px.line(
        df_evolution,
        x="year",
        y="count_disciplines",
        color="competition",        # Crée une ligne par type de compétition
        markers=True,               # Ajoute des points sur la ligne pour chaque édition
        labels={
            "year": "Année",
            "count_disciplines": "Nombre de Disciplines",
            "competition": "Type de Compétition"
        },
        title="Nombre de disciplines d'athlétisme par édition"
    )

    # Amélioration de l'apparence
    fig.update_layout(
        xaxis_title="Année de l'édition",
        yaxis_title="Nombre de disciplines",
        legend_title_text='Compétition'
    )
    
    # Affichage du graphique dans Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # Afficher le tableau de données en dessous pour consultation
    with st.expander("Voir les données du tableau"):
        st.dataframe(df_evolution.sort_values("year", ascending=False), use_container_width=True)

else:
    st.warning("Aucune donnée sur les éditions n'a pu être chargée.")