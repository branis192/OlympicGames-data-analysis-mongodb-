# Fichier : 3_🌍_Carte_du_Monde.py

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

# --- DICTIONNAIRE DE MAPPING COMPLET (basé sur votre analyse) ---
# Ce dictionnaire est la source de vérité pour la conversion des codes pays.
NOC_TO_ISO3 = {
    'AFG': 'AFG', 'AHO': 'ANT', 'ALB': 'ALB', 'ALG': 'DZA', 'AND': 'AND', 'ANG': 'AGO',
    'ANT': 'ATG', 'ANZ': 'AUS', 'ARG': 'ARG', 'ARM': 'ARM', 'ARU': 'ABW', 'ASA': 'ASM',
    'AUS': 'AUS', 'AUT': 'AUT', 'AZE': 'AZE', 'BAH': 'BHS', 'BAN': 'BGD', 'BAR': 'BRB',
    'BDI': 'BDI', 'BEL': 'BEL', 'BEN': 'BEN', 'BER': 'BMU', 'BHU': 'BTN', 'BIH': 'BIH',
    'BIZ': 'BLZ', 'BLR': 'BLR', 'BOH': 'CZE', 'BOL': 'BOL', 'BOT': 'BWA', 'BRA': 'BRA',
    'BRN': 'BHR', 'BRU': 'BRN', 'BUL': 'BGR', 'BUR': 'BFA', 'CAF': 'CAF', 'CAM': 'KHM',
    'CAN': 'CAN', 'CAY': 'CYM', 'CGO': 'COG', 'CHA': 'TCD', 'CHI': 'CHL', 'CHN': 'CHN',
    'CIV': 'CIV', 'CMR': 'CMR', 'COD': 'COD', 'COK': 'COK', 'COL': 'COL', 'COM': 'COM',
    'CPV': 'CPV', 'CRC': 'CRI', 'CRO': 'HRV', 'CUB': 'CUB', 'CYP': 'CYP', 'CZE': 'CZE',
    'DEN': 'DNK', 'DJI': 'DJI', 'DMA': 'DMA', 'DOM': 'DOM', 'ECU': 'ECU', 'EGY': 'EGY',
    'ERI': 'ERI', 'ESA': 'SLV', 'ESP': 'ESP', 'EST': 'EST', 'ETH': 'ETH', 'EUN': 'RUS',
    'FIJ': 'FJI', 'FIN': 'FIN', 'FRA': 'FRA', 'FRG': 'DEU', 'FSM': 'FSM', 'GAB': 'GAB',
    'GAM': 'GMB', 'GBR': 'GBR', 'GBS': 'GNB', 'GDR': 'DEU', 'GEO': 'GEO', 'GEQ': 'GNQ',
    'GER': 'DEU', 'GHA': 'GHA', 'GRE': 'GRC', 'GRN': 'GRD', 'GUA': 'GTM', 'GUI': 'GIN',
    'GUM': 'GUM', 'GUY': 'GUY', 'HAI': 'HTI', 'HKG': 'HKG', 'HON': 'HND', 'HUN': 'HUN',
    'INA': 'IDN', 'IND': 'IND', 'IOA': 'IND', 'IRI': 'IRN', 'IRL': 'IRL', 'IRQ': 'IRQ',
    'ISL': 'ISL', 'ISR': 'ISR', 'ISV': 'VIR', 'ITA': 'ITA', 'IVB': 'VGB', 'JAM': 'JAM',
    'JOR': 'JOR', 'JPN': 'JPN', 'KAZ': 'KAZ', 'KEN': 'KEN', 'KGZ': 'KGZ', 'KIR': 'KIR',
    'KOR': 'KOR', 'KOS': 'XKX', 'KSA': 'SAU', 'KUW': 'KWT', 'LAO': 'LAO', 'LAT': 'LVA',
    'LBA': 'LBY', 'LBN': 'LBN', 'LBR': 'LBR', 'LCA': 'LCA', 'LES': 'LSO', 'LIE': 'LIE',
    'LTU': 'LTU', 'LUX': 'LUX', 'MAD': 'MDG', 'MAR': 'MAR', 'MAS': 'MYS', 'MAW': 'MWI',
    'MDA': 'MDA', 'MDV': 'MDV', 'MEX': 'MEX', 'MGL': 'MNG', 'MHL': 'MHL', 'MKD': 'MKD',
    'MLI': 'MLI', 'MLT': 'MLT', 'MNE': 'MNE', 'MON': 'MCO', 'MOZ': 'MOZ', 'MRI': 'MUS',
    'MTN': 'MRT', 'MYA': 'MMR', 'NAM': 'NAM', 'NCA': 'NIC', 'NED': 'NLD', 'NEP': 'NPL',
    'NGR': 'NGA', 'NIG': 'NER', 'NOR': 'NOR', 'NRU': 'NRU', 'NZL': 'NZL', 'OMA': 'OMN',
    'PAK': 'PAK', 'PAN': 'PAN', 'PAR': 'PRY', 'PER': 'PER', 'PHI': 'PHL', 'PLE': 'PSE',
    'PLW': 'PLW', 'PNG': 'PNG', 'POL': 'POL', 'POR': 'PRT', 'PRK': 'PRK', 'PUR': 'PRI',
    'QAT': 'QAT', 'ROC': 'TWN', 'ROU': 'ROU', 'RSA': 'ZAF', 'RUS': 'RUS', 'RWA': 'RWA',
    'SAM': 'WSM', 'SCG': 'SRB', 'SEN': 'SEN', 'SEY': 'SYC', 'SGP': 'SGP', 'SIN': 'SGP',
    'SKN': 'KNA', 'SLE': 'SLE', 'SLO': 'SVN', 'SMR': 'SMR', 'SOL': 'SLB', 'SOM': 'SOM',
    'SRB': 'SRB', 'SRI': 'LKA', 'SSD': 'SSD', 'STP': 'STP', 'SUD': 'SDN', 'SUI': 'CHE',
    'SUR': 'SUR', 'SVK': 'SVK', 'SWE': 'SWE', 'SWZ': 'SWZ', 'SYR': 'SYR', 'TAN': 'TZA',
    'TCH': 'CZE', 'TGA': 'TON', 'THA': 'THA', 'TJK': 'TJK', 'TKM': 'TKM', 'TLS': 'TLS',
    'TOG': 'TGO', 'TPE': 'TWN', 'TRI': 'TTO', 'TTO': 'TTO', 'TUN': 'TUN', 'TUR': 'TUR',
    'TUV': 'TUV', 'UAE': 'ARE', 'UAR': 'EGY', 'UGA': 'UGA', 'UKR': 'UKR', 'URS': 'RUS',
    'URU': 'URY', 'USA': 'USA', 'UZB': 'UZB', 'VAN': 'VUT', 'VEN': 'VEN', 'VIE': 'VNM',
    'VIN': 'VCT', 'WIF': 'VGB', 'YEM': 'YEM', 'YUG': 'SRB', 'ZAM': 'ZMB', 'ZIM': 'ZWE'
}

@st.cache_data
def get_iso_code(noc_code):
    """Convertit un code NOC en code ISO-3 à partir du dictionnaire interne."""
    return NOC_TO_ISO3.get(noc_code)

@st.cache_data
def get_medals_by_country_for_map():
    """Récupère le décompte de chaque type de médaille par pays."""
    pipeline = [
        {"$match": {"medal": {"$in": ["Gold", "Silver", "Bronze"]}}},
        {
            "$group": {
                "_id": "$noc",
                "Or": {"$sum": {"$cond": [{"$eq": ["$medal", "Gold"]}, 1, 0]}},
                "Argent": {"$sum": {"$cond": [{"$eq": ["$medal", "Silver"]}, 1, 0]}},
                "Bronze": {"$sum": {"$cond": [{"$eq": ["$medal", "Bronze"]}, 1, 0]}},
            }
        },
        {"$addFields": {"Total": {"$add": ["$Or", "$Argent", "$Bronze"]}}},
        {"$project": {"_id": 0, "Pays (NOC)": "$_id", "Or": 1, "Argent": 1, "Bronze": 1, "Total": 1}}
    ]
    data = list(db.results.aggregate(pipeline))
    if not data: return pd.DataFrame()
    
    df = pd.DataFrame(data)
    df['Code ISO-3'] = df['Pays (NOC)'].apply(get_iso_code)
    # On supprime les lignes pour lesquelles le mapping a échoué (s'il y en a)
    df.dropna(subset=['Code ISO-3'], inplace=True)
    return df


# --- INTERFACE UTILISATEUR (UI) ---
st.title("🌍 Carte du Monde des Médailles")
st.markdown("Explorez la répartition géographique des médailles en athlétisme. Utilisez les options ci-dessous pour filtrer par type de médaille.")

df_map = get_medals_by_country_for_map()

if not df_map.empty:
    st.sidebar.header("Options de la Carte")
    medal_type_to_display = st.sidebar.selectbox(
        "Choisissez le type de médailles à afficher :",
        ["Total", "Or", "Argent", "Bronze"]
    )

    color_scales = {
        "Total": px.colors.sequential.Plasma,
        "Or": px.colors.sequential.Oranges,
        "Argent": px.colors.sequential.Greys,
        "Bronze": px.colors.sequential.amp
    }
    
    fig = px.choropleth(
        df_map,
        locations="Code ISO-3",
        color=medal_type_to_display,
        hover_name="Pays (NOC)",
        hover_data={"Or": True, "Argent": True, "Bronze": True, "Total": True, "Code ISO-3": False},
        color_continuous_scale=color_scales[medal_type_to_display],
        projection="natural earth",
        title=f"Nombre de Médailles d'{'e Total' if medal_type_to_display == 'Total' else medal_type_to_display}"
    )

    fig.update_layout(
        margin={"r":0, "t":40, "l":0, "b":0},
        coloraxis_colorbar_title_text='Nombre de<br>Médailles'
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Voir le tableau de données complet"):
        st.dataframe(
            df_map.sort_values(medal_type_to_display, ascending=False),
            use_container_width=True, hide_index=True
        )

else:
    st.warning("Aucune donnée de médaille n'a pu être chargée pour la carte.")