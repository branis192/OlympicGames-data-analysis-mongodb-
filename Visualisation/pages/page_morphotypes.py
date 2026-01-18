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

# --- DICTIONNAIRE DE LOGIQUE DE GROUPEMENT (plus facile à utiliser) ---
# Clé: la catégorie, Valeur: liste de mots-clés
DISCIPLINE_GROUPS = {
    'Sprint / Relais': ['100 metres', '200 metres', '400 metres', 'relay'],
    'Lancers': ['shot put', 'discus throw', 'javelin throw', 'hammer throw'],
    'Sauts': ['long jump', 'high jump', 'triple jump', 'pole vault'],
    'Fond / Demi-Fond': ['marathon', 'walk', '5,000 metres', '10,000 metres', 'steeplechase', '1,500 metres', '800 metres'],
    'Épreuves Combinées': ['decathlon', 'heptathlon', 'pentathlon'],
    'Haies': ['hurdles']
}

def get_discipline_group(event_name):
    event_lower = event_name.lower()
    for group, keywords in DISCIPLINE_GROUPS.items():
        if any(keyword in event_lower for keyword in keywords):
            return group
    return 'Autre'

# --- FONCTIONS DE RÉCUPÉRATION DE DONNÉES ---
@st.cache_data
def get_athlete_morphology_data():
    """Récupère la morphologie de TOUS les participants, pas seulement les médaillés."""
    # Récupère les athlètes avec morphologie
    athletes_with_morpho = list(db.athletes.find(
        {
            "height": {"$exists": True, "$ne": None},
            "weight": {"$exists": True, "$ne": None}
        },
        {"_id": 1, "height": 1, "weight": 1, "sex": 1}
    ))
    
    if not athletes_with_morpho:
        return pd.DataFrame()
    
    # Créer un dict pour lookup rapide
    athlete_dict = {str(a['_id']): a for a in athletes_with_morpho}
    
    # Récupère les résultats des athlètes avec morphologie
    athlete_ids = [str(a['_id']) for a in athletes_with_morpho]
    results_data = list(db.results.find(
        {"athlete_id": {"$in": athlete_ids}},
        {"athlete_id": 1, "athlete_name": 1, "event": 1, "medal": 1}
    ))
    
    if not results_data:
        return pd.DataFrame()
    
    # Enrichir les données avec la morphologie
    data = []
    for result in results_data:
        athlete_id = result['athlete_id']
        if athlete_id in athlete_dict:
            athlete = athlete_dict[athlete_id]
            data.append({
                'athlete': result['athlete_name'],
                'sex': athlete.get('sex'),
                'height': athlete['height'],
                'weight': athlete['weight'],
                'event': result['event'],
                'medal': result['medal']
            })
    
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # Nettoyage Pandas
    df[['height', 'weight']] = df[['height', 'weight']].apply(pd.to_numeric, errors='coerce')
    df.dropna(subset=['height', 'weight'], inplace=True)
    df = df[df['height'].between(140, 230) & df['weight'].between(40, 200)]
    
    # Création des nouvelles colonnes pour les graphiques
    df['Groupe Discipline'] = df['event'].apply(get_discipline_group)
    df['Statut'] = df['medal'].apply(lambda x: x if x in ['Gold', 'Silver', 'Bronze'] else 'Participant')
    
    return df

# --- INTERFACE UTILISATEUR (UI) ---
st.title("🔬 Analyse Morphologique des Athlètes")
st.markdown("Explorez les profils physiques (taille vs. poids) des athlètes.")

# Chargement initial des données
df_full = get_athlete_morphology_data()

if df_full.empty:
    st.error("❌ Aucune donnée disponible. Vérifiez votre connexion MongoDB et les données dans la base.")
    st.stop()

# Choix du mode d'affichage
view_mode = st.radio(
    "Comment voulez-vous colorer les points ?",
    ('Par Catégorie de Discipline', 'Par Statut (Participant vs. Médaillé)'),
    horizontal=True
)

st.sidebar.header("Filtres")
# --- FILTRES EN CASCADE ---
all_categories = sorted(df_full['Groupe Discipline'].unique())
selected_category = st.sidebar.selectbox("Filtrer par Catégorie :", ["Toutes"] + all_categories)

if selected_category != 'Toutes':
    # Filtrer le DataFrame pour ne garder que les disciplines de la catégorie choisie
    disciplines_in_category = sorted(df_full[df_full['Groupe Discipline'] == selected_category]['event'].unique())
    selected_discipline = st.sidebar.selectbox("Filtrer par Discipline :", ["Toutes"] + disciplines_in_category)
    
    if selected_discipline != 'Toutes':
        df_filtered = df_full[df_full['event'] == selected_discipline]
    else:
        df_filtered = df_full[df_full['Groupe Discipline'] == selected_category]
else:
    df_filtered = df_full

if not df_filtered.empty:
    
    # Construction dynamique du titre du graphique
    title = f"Relation Taille-Poids pour : {selected_category}"
    if 'selected_discipline' in locals() and selected_discipline != 'Toutes':
        title += f" - {selected_discipline}"

    # --- AFFICHAGE SELON LE MODE ---
    if view_mode == 'Par Catégorie de Discipline':
        color_column = 'Groupe Discipline'
        # On définit des couleurs pour chaque catégorie
        color_map = {
            'Sprint / Relais': 'blue', 'Lancers': 'red', 'Sauts': 'green',
            'Fond / Demi-Fond': 'purple', 'Épreuves Combinées': 'orange',
            'Haies': 'cyan', 'Autre': 'gray'
        }
    else: # Par Statut
        color_column = 'Statut'
        # On définit des couleurs pour le statut
        color_map = {
            'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32',
            'Participant': '#00CED1' # Cyan (vert bleu clair)
        }

    fig = px.scatter(
        df_filtered,
        x="height",
        y="weight",
        color=color_column,
        color_discrete_map=color_map,
        hover_data=['athlete', 'event', 'medal'],
        labels={"height": "Taille (cm)", "weight": "Poids (kg)"},
        title=title,
        # Catégoriser la légende pour qu'elle ne change pas d'ordre
        category_orders={color_column: sorted(df_full[color_column].unique())}
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune donnée à afficher pour les filtres sélectionnés.")