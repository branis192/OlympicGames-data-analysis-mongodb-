import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px
import pycountry

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

# --- FONCTIONS DE TRAITEMENT DES DONNÉES ---

# Dictionnaire pour les codes NOC non standards ou ambigus
# C'est un point clé pour que la carte fonctionne bien.
NOC_TO_ISO3_MANUAL_MAPPING = {
    'GDR': 'DEU',  # Allemagne de l'Est -> Allemagne
    'FRG': 'DEU',  # Allemagne de l'Ouest -> Allemagne
    'URS': 'RUS',  # Union Soviétique -> Russie
    'EUN': 'RUS',  # Équipe Unifiée -> Russie
    'TCH': 'CZE',  # Tchécoslovaquie -> République Tchèque
    'YUG': 'SRB',  # Yougoslavie -> Serbie
    'SGP': 'SGP',  # Singapour (parfois mal interprété)
    'PUR': 'PRI',  # Porto Rico
    'KOR': 'KOR',  # Corée du Sud
    'IRI': 'IRN',  # Iran
    'VIE': 'VNM',  # Vietnam
    'TRI': 'TTO',  # Trinité et Tobago (TRI est l'ancien code, TTO est l'actuel)
}


@st.cache_data
def get_iso_code(noc_code):
    """
    Tente de convertir un code NOC en code ISO-3.
    Utilise un dictionnaire de mapping manuel pour les cas difficiles.
    """
    if noc_code in NOC_TO_ISO3_MANUAL_MAPPING:
        return NOC_TO_ISO3_MANUAL_MAPPING[noc_code]
    try:
        # Recherche par code à 3 lettres
        country = pycountry.countries.get(alpha_3=noc_code)
        if country:
            return country.alpha_3
        # Si ça échoue, recherche par code à 2 lettres (si le NOC en est un)
        country = pycountry.countries.get(alpha_2=noc_code)
        if country:
            return country.alpha_3
    except Exception:
        return None # Retourne None si aucune correspondance n'est trouvée
    return None

@st.cache_data
def get_medals_by_country_for_map():
    """
    Récupère le nombre total de médailles par pays depuis MongoDB.
    """
    pipeline = [
        {"$match": {"medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {"$group": {"_id": "$noc", "total_medailles": {"$sum": 1}}},
        {"$project": {"_id": 0, "Pays (NOC)": "$_id", "Médailles": "$total_medailles"}}
    ]
    data = list(db.results.aggregate(pipeline))
    if not data:
        return pd.DataFrame()
    
    df = pd.DataFrame(data)
    # Applique la conversion de code pour chaque pays
    df['Code ISO-3'] = df['Pays (NOC)'].apply(get_iso_code)
    
    # Supprime les lignes où la conversion a échoué pour ne pas casser la carte
    df.dropna(subset=['Code ISO-3'], inplace=True)
    
    return df

# --- INTERFACE UTILISATEUR (UI) ---

st.title("🌍 Carte du Monde des Médailles")
st.markdown("Répartition géographique de toutes les médailles (Or, Argent, Bronze) remportées dans les compétitions étudiées.")

# Chargement des données
df_map = get_medals_by_country_for_map()

if not df_map.empty:
    # Création de la carte avec Plotly Express
    fig = px.choropleth(
        df_map,
        locations="Code ISO-3",          # Nom de la colonne avec les codes ISO-3
        color="Médailles",               # La valeur qui détermine la couleur
        hover_name="Pays (NOC)",         # Ce qui s'affiche au survol
        color_continuous_scale=px.colors.sequential.Plasma, # Palette de couleurs
        projection="natural earth",      # Type de projection de la carte
        title="Nombre total de médailles par pays"
    )
    
    # Amélioration de l'apparence de la carte
    fig.update_layout(
        margin={"r":0, "t":40, "l":0, "b":0},
        coloraxis_colorbar_title_text='Nombre de<br>Médailles'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Afficher le tableau de données en dessous pour consultation
    with st.expander("Voir les données du tableau"):
        st.dataframe(df_map.sort_values("Médailles", ascending=False), use_container_width=True)
else:
    st.warning("Aucune donnée de médaille n'a pu être chargée pour la carte.")