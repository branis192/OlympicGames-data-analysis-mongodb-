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
@st.cache_data
def get_top_10_athletes(sex_filter="Tous", country_filter="Tous", sort_by="Total"):
    """
    Récupère le top 10 des athlètes avec des filtres pour le sexe, le pays,
    et le critère de tri (Total de médailles vs. médailles d'Or).
    """
    # Étape 1 : Construire le filtre '$match' de base
    match_filter = {"total_medals": {"$gt": 0}}
    
    if sex_filter != "Tous":
        match_filter["sex"] = "Male" if sex_filter == "Hommes" else "Female"
        
    if country_filter != "Tous":
        match_filter["country_origin"] = country_filter
        
    # Étape 2 : Construire le critère de tri '$sort'
    if sort_by == "Or":
        # Tri principal par Or, puis par Total en cas d'égalité
        sort_criteria = {"medals_detail.gold": -1, "total_medals": -1}
    else: # Par défaut, tri par Total
        sort_criteria = {"total_medals": -1}
    
    pipeline = [
        {"$match": match_filter},
        {"$sort": sort_criteria},
        {"$limit": 10},
        {"$project": {
            "_id": 0, "Athlète": "$name", "Pays": "$country_origin",
            "Total": "$total_medals", "Or": {"$ifNull": ["$medals_detail.Gold", 0]},
            "Argent": {"$ifNull": ["$medals_detail.Silver", 0]}, 
            "Bronze": {"$ifNull": ["$medals_detail.Bronze", 0]}
        }}
    ]
    
    data = list(db.athletes.aggregate(pipeline))
    df = pd.DataFrame(data)
    
    # Ensure numeric types
    for col in ['Or', 'Argent', 'Bronze', 'Total']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    return df

@st.cache_data
def get_all_countries_with_medals():
    """Récupère la liste des pays pour le filtre."""
    codes = db.athletes.distinct("country_origin", {"total_medals": {"$gt": 0}})
    return ["Tous"] + sorted(codes)


# --- INTERFACE UTILISATEUR (UI) ---
st.title("🌟 Les Légendes de l'Athlétisme")
st.markdown("Explorez le classement des plus grands athlètes en utilisant les filtres ci-dessous.")

# --- FILTRES DANS LA BARRE LATÉRALE ---
st.sidebar.header("Filtres du Top 10")

sort_by_option = st.sidebar.radio(
    "Classer par :",
    ("Total de Médailles", "Or"),
    key="sort_top_athletes"
)
# Convertir le choix en clé pour la fonction
sort_by_key = "Or" if sort_by_option == "Or" else "Total"

sex_option = st.sidebar.radio(
    "Filtrer par sexe :",
    ("Tous", "Hommes", "Femmes"),
    key="sex_top_athletes"
)

country_list = get_all_countries_with_medals()
country_option = st.sidebar.selectbox(
    "Filtrer par pays :",
    country_list,
    key="country_top_athletes"
)


# --- CHARGEMENT ET AFFICHAGE ---
df_top_athletes = get_top_10_athletes(
    sex_filter=sex_option,
    country_filter=country_option,
    sort_by=sort_by_key
)

if not df_top_athletes.empty:
    # Colonne à utiliser pour l'axe X et le tri du graphique
    sort_column_df = "Or" if sort_by_key == "Or" else "Total"
    
    df_top_athletes['Athlète (Pays)'] = df_top_athletes['Athlète'] + " (" + df_top_athletes['Pays'] + ")"
    df_graph = df_top_athletes.sort_values(sort_column_df, ascending=True)

    fig = px.bar(
        df_graph,
        x=sort_column_df,
        y="Athlète (Pays)",
        orientation='h',
        text=sort_column_df,
        title=f"Top 10 des Athlètes classés par nombre de médailles d'{'Or' if sort_by_key == 'Or' else 'Total'}"
    )

    fig.update_traces(textposition='outside', marker_color='#F2BE22')
    fig.update_layout(
        xaxis_title=f"Nombre de médailles d'{'Or' if sort_by_key == 'Or' else 'Total'}",
        yaxis_title="Athlète", height=600
    )
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("Voir le classement détaillé"):
        st.dataframe(
            df_top_athletes[['Athlète', 'Pays', 'Or', 'Argent', 'Bronze', 'Total']],
            use_container_width=True, hide_index=True
        )

else:
    st.warning("Aucun athlète ne correspond aux filtres sélectionnés.")