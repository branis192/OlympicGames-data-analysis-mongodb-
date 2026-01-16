import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(layout="wide")

@st.cache_resource
def init_connection():
    client = MongoClient("mongodb://localhost:27017/")
    return client

client = init_connection()
db = client.athle_db

# --- FONCTION CORRIGÉE ---
@st.cache_data
def get_clean_discipline_evolution():
    # Agrégation pour éviter les erreurs de comptage
    pipeline = [
        {
            "$project": {
                "year": {"$toInt": "$year"},
                "competition": 1,
                "count_disciplines": {"$toInt": "$count_disciplines"}
            }
        },
        {"$sort": {"year": 1}}
    ]
    data = list(db.editions.aggregate(pipeline))
    return pd.DataFrame(data)

st.title("📈 Analyse de l'Évolution des Disciplines")

df = get_clean_discipline_evolution()

if not df.empty:
    # FILTRE : Permettre à l'utilisateur de choisir la compétition pour éviter les cumuls faux
    competitions = ["Toutes"] + sorted(df['competition'].unique().tolist())
    selected_comp = st.selectbox("Filtrer par type de compétition :", competitions)
    
    df_plot = df if selected_comp == "Toutes" else df[df['competition'] == selected_comp]

    # --- VISUALISATION PLUS MODERNE (Area Chart) ---
    fig = px.area(
        df_plot,
        x="year",
        y="count_disciplines",
        color="competition",
        line_group="competition",
        title="Croissance du programme d'athlétisme",
        labels={"count_disciplines": "Nb Disciplines", "year": "Année"},
        template="plotly_dark",
        markers=True
    )

    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # --- ANALYSE DES CHIFFRES ---
    col1, col2 = st.columns(2)
    with col1:
        latest_year = df_plot['year'].max()
        latest_count = df_plot[df_plot['year'] == latest_year]['count_disciplines'].sum()
        st.metric(f"Total Disciplines en {latest_year}", int(latest_count))
    
    with col2:
        st.info("💡 Si le chiffre paraît élevé, vérifiez si votre base ne compte pas séparément les épreuves paralympiques ou les catégories d'âge (U20, etc).")