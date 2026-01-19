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
if not client: st.stop()
db = client.athle_db

# --- FONCTION DE RÉCUPÉRATION DES DONNÉES AMÉLIORÉE ---
@st.cache_data(ttl=3600)  # Cache pour 1 heure
def get_top_10_countries(competition_filter="Toutes", sort_by="Total"):
    """
    Récupère le top 10 des pays avec un filtre par compétition
    et un critère de tri (Total de médailles vs. médailles d'Or).
    """
    # Étape 1 : Construire le filtre '$match' de base
    match_filter = {"medal": {"$in": ["Gold", "Silver", "Bronze"]}}
    
    if competition_filter != "Toutes":
        match_filter["competition"] = competition_filter
        
    # Étape 2 : Définir le critère de tri pour l'étape '$sort'
    # Le classement officiel se fait par Or, puis Argent, puis Bronze.
    if sort_by == "Or":
        sort_criteria = {"Or": -1, "Argent": -1, "Bronze": -1}
    else: # Tri par Total
        sort_criteria = {"Total": -1}

    pipeline = [
        {"$match": match_filter},
        {
            # Étape 3 : Grouper par pays et compter chaque type de médaille
            "$group": {
                "_id": "$noc",
                "Or": {"$sum": {"$cond": [{"$eq": ["$medal", "Gold"]}, 1, 0]}},
                "Argent": {"$sum": {"$cond": [{"$eq": ["$medal", "Silver"]}, 1, 0]}},
                "Bronze": {"$sum": {"$cond": [{"$eq": ["$medal", "Bronze"]}, 1, 0]}},
            }
        },
        # Étape 4 : Calculer le total
        {"$addFields": {"Total": {"$add": ["$Or", "$Argent", "$Bronze"]}}},
        # Étape 5 : Appliquer le tri
        {"$sort": sort_criteria},
        # Étape 6 : Garder les 10 premiers
        {"$limit": 10},
        # Étape 7 : Mettre en forme pour le DataFrame
        {"$project": {"_id": 0, "Pays": "$_id", "Or": 1, "Argent": 1, "Bronze": 1, "Total": 1}}
    ]
    
    data = list(db.results.aggregate(pipeline))
    return pd.DataFrame(data)

# --- INTERFACE UTILISATEUR (UI) ---
st.title("🏆 Top 10 des Nations de l'Athlétisme")
st.markdown("Explorez le classement des pays les plus médaillés et changez les critères pour affiner l'analyse.")

# --- FILTRES DANS LA BARRE LATÉRALE ---
st.sidebar.header("⚙️ Filtres du Top 10")

sort_by_option = st.sidebar.radio(
    "Classer par :",
    ("Classement Olympique (par Or)", "Total de Médailles"),
    key="sort_top_countries"
)
sort_by_key = "Or" if sort_by_option == "Classement Olympique (par Or)" else "Total"

# --- CHARGEMENT ET AFFICHAGE ---
df_top_countries = get_top_10_countries(
    competition_filter="Toutes",
    sort_by=sort_by_key
)

if not df_top_countries.empty:
    
    # Afficher le graphique en premier
    graph_sort_column = "Or" if sort_by_key == "Or" else "Total"
    df_graph = df_top_countries.sort_values(by=graph_sort_column, ascending=True)

    x_label = "Nombre de Médailles d'Or" if sort_by_key == "Or" else "Nombre Total de Médailles"
    
    fig = px.bar(
        df_graph,
        x=graph_sort_column,
        y="Pays",
        orientation='h',
        text=graph_sort_column,
        title=f"Top 10 des Pays (Classement : {sort_by_option})"
    )
    
    fig.update_traces(textposition='outside', marker_color='#FFD700' if sort_by_key == "Or" else '#0087FF')
    fig.update_layout(
        xaxis_title=x_label,
        yaxis_title="Pays (Code NOC)",
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Afficher le tableau détaillé en bas
    st.subheader("📊 Tableau détaillé des médailles")
    display_df = df_top_countries[['Pays', 'Or', 'Argent', 'Bronze', 'Total']].copy()
    st.dataframe(display_df, use_container_width=True, hide_index=True)
else:
    st.error("❌ Aucun pays ne correspond aux filtres sélectionnés. Vérifiez les données disponibles.")