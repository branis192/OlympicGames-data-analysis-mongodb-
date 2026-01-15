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
def get_top_10_athletes():
    """
    Récupère le top 10 des athlètes les plus médaillés en utilisant
    le champ pré-calculé 'total_medals' de la collection 'athletes'.
    """
    pipeline = [
        # Étape 1 : S'assurer qu'on ne prend que les athlètes avec des médailles
        {"$match": {"total_medals": {"$gt": 0}}},
        
        # Étape 2 : Trier par le total de médailles en ordre décroissant
        {"$sort": {"total_medals": -1}},
        
        # Étape 3 : Garder uniquement les 10 premiers
        {"$limit": 10},
        
        # Étape 4 : Projeter tous les champs nécessaires pour le tableau et le graphique
        {
            "$project": {
                "_id": 0,
                "Athlète": "$name",
                "Pays": "$country_origin",
                "Total": "$total_medals",
                "Or": {"$ifNull": ["$medals_detail.gold", 0]},
                "Argent": {"$ifNull": ["$medals_detail.silver", 0]},
                "Bronze": {"$ifNull": ["$medals_detail.bronze", 0]}
            }
        }
    ]
    
    data = list(db.athletes.aggregate(pipeline))
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Ensure columns exist and have proper types
    for col in ['Or', 'Argent', 'Bronze', 'Total']:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
    return df


# --- INTERFACE UTILISATEUR (UI) ---

st.title("🌟 Top 10 des Légendes de l'Athlétisme")
st.markdown("Classement des athlètes ayant remporté le plus de médailles, toutes compétitions confondues.")

# Chargement des données
df_top_athletes = get_top_10_athletes()

if not df_top_athletes.empty:
    # On ajoute le pays au nom de l'athlète pour plus de clarté dans le graphique
    df_top_athletes['Athlète (Pays)'] = df_top_athletes['Athlète'] + " (" + df_top_athletes['Pays'] + ")"
    
    # On trie pour l'affichage horizontal
    df_top_athletes_sorted = df_top_athletes.sort_values("Total", ascending=True)

    # Création du graphique en barres horizontales
    fig = px.bar(
        df_top_athletes_sorted,
        x="Total",
        y="Athlète (Pays)",
        orientation='h',
        text="Total",
        title="Top 10 des Athlètes par Nombre Total de Médailles"
    )

    # Amélioration du design
    fig.update_traces(
        textposition='outside',
        marker_color='#F2BE22' # Une couleur dorée
    )
    fig.update_layout(
        xaxis_title="Nombre Total de Médailles",
        yaxis_title="Athlète",
        height=600 # Un peu plus haut pour laisser de la place aux noms
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # Afficher le tableau de données avec le détail des médailles
    with st.expander("Voir le classement détaillé avec la répartition Or/Argent/Bronze"):
        # Ensure all required columns exist
        cols_to_display = ['Athlète', 'Pays', 'Or', 'Argent', 'Bronze', 'Total']
        display_df = df_top_athletes[[col for col in cols_to_display if col in df_top_athletes.columns]]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

else:
    st.warning("Aucune donnée sur les athlètes les plus médaillés n'a pu être chargée.")