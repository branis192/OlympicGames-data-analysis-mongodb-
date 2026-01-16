import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="Fiche Athlète Olympique", page_icon="🏅")

# --- CONNEXION À MONGODB ---
@st.cache_resource
def init_connection():
    try:
        # Connexion locale à MongoDB
        client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
        client.server_info() # Test de connexion
        return client
    except Exception as e:
        st.error(f"❌ Erreur : Impossible de se connecter à MongoDB. Vérifiez que le serveur 'mongod' tourne dans votre terminal. {e}")
        return None

client = init_connection()
if not client:
    st.stop()

db = client.athle_db

# --- FONCTIONS DE RÉCUPÉRATION DE DONNÉES ---
@st.cache_data
def get_all_athlete_names():
    """Récupère la liste triée de tous les noms d'athlètes."""
    athletes = db.athletes.find({}, {"name": 1, "_id": 0}).sort("name", 1)
    return [athlete['name'] for athlete in athletes if 'name' in athlete]

@st.cache_data
def get_athlete_data(athlete_name):
    """Récupère la bio et les résultats d'un athlète spécifique."""
    athlete_bio = db.athletes.find_one({"name": athlete_name})
    athlete_results = list(db.results.find({"athlete_name": athlete_name}).sort("year", 1))
    return athlete_bio, athlete_results

# --- INTERFACE UTILISATEUR ---
st.title("👤 Fiche Athlète")
st.markdown("Analyse détaillée des performances et évolution du classement.")

# Sélection de l'athlète
athlete_names = get_all_athlete_names()
if athlete_names:
    # On cherche Kevin Mayer par défaut, sinon le premier de la liste
    default_idx = athlete_names.index("Kevin Mayer") if "Kevin Mayer" in athlete_names else 0
    selected_athlete = st.selectbox("Sélectionnez un athlète", athlete_names, index=default_idx)

    if selected_athlete:
        bio, results = get_athlete_data(selected_athlete)
        
        # Organisation en colonnes : Bio à gauche, Graphiques à droite
        col1, col2 = st.columns([1, 2.5])

        with col1:
            st.subheader("ℹ️ Informations")
            if bio:
                st.info(f"**Pays :** {bio.get('country_origin', 'N/A')}")
                st.write(f"**Sexe :** {bio.get('sex', 'N/A')}")
                st.write(f"**Date de naissance :** {bio.get('born', 'N/A')}")
                st.write(f"**Taille/Poids :** {bio.get('height', 'N/A')} cm / {bio.get('weight', 'N/A')} kg")
                
                st.divider()
                st.subheader("🏅 Bilan des Médailles")
                
                # Calcul dynamique des médailles à partir des résultats réels
                if results:
                    df_temp = pd.DataFrame(results)
                    # On normalise les noms des médailles (casse)
                    if 'medal' in df_temp.columns:
                        gold = len(df_temp[df_temp['medal'].str.lower() == 'gold'])
                        silver = len(df_temp[df_temp['medal'].str.lower() == 'silver'])
                        bronze = len(df_temp[df_temp['medal'].str.lower() == 'bronze'])
                    else:
                        gold = silver = bronze = 0
                else:
                    gold = silver = bronze = 0

                c1, c2, c3 = st.columns(3)
                c1.metric("🥇 Or", gold)
                c2.metric("🥈 Arg.", silver)
                c3.metric("🥉 Bron.", bronze)
                st.metric("Total Medals", gold + silver + bronze)

        with col2:
            if results:
                df_results = pd.DataFrame(results)
                
                # Nettoyage des données de position
                df_results['pos'] = pd.to_numeric(df_results['pos'], errors='coerce')
                df_clean = df_results.dropna(subset=['pos']).sort_values('year')

                # --- VISUALISATION 1 : METRIC CLASSEMENT ---
                st.subheader("📊 Performance Globale")
                best_rank = int(df_clean['pos'].min()) if not df_clean.empty else "N/A"
                st.system_note = f"Meilleure position enregistrée : {best_rank}"
                st.metric("Meilleur Classement Mondial", f"Rang n°{best_rank}")

                # --- VISUALISATION 2 : GRAPHE D'ÉVOLUTION ---
                if not df_clean.empty:
                    fig = px.line(
                        df_clean, 
                        x="year", 
                        y="pos", 
                        markers=True,
                        text="pos",
                        title=f"Évolution du classement de {selected_athlete} au fil des ans",
                        labels={"year": "Année", "pos": "Position"},
                        template="plotly_dark"
                    )
                    # Inversion de l'axe Y : le rang 1 doit être en haut
                    fig.update_yaxes(autorange="reversed", gridcolor='gray')
                    fig.update_traces(textposition="top center", line_color="#00CC96")
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # --- TABLEAU DÉTAILLÉ ---
                with st.expander("Voir le détail des compétitions"):
                    display_df = df_results[['year', 'competition', 'event', 'pos', 'medal']].rename(columns={
                        'year': 'Année', 'competition': 'Compétition', 'event': 'Épreuve',
                        'pos': 'Position', 'medal': 'Médaille'
                    })
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Aucune donnée de performance disponible pour cet athlète.")
else:
    st.error("La collection 'athletes' semble vide dans votre base MongoDB.")

# --- SECTION CHAMPIONNATS DU MONDE (WORLD ATHLETICS) ---
st.divider()
st.title("🌍 Championnats du Monde (IAAF)")
st.markdown("Résultats extraits de la base des Championnats du Monde d'Athlétisme.")

@st.cache_data
def get_world_championships_data(athlete_name):
    """Récupère les résultats depuis la nouvelle collection world_results."""
    # Note : On utilise 'athlete' car le script de conversion a renommé 'athelete' en 'athlete'
    results = list(db.world_results.find({"athlete": athlete_name}).sort("year", 1))
    return results

world_results = get_world_championships_data(selected_athlete)

if world_results:
    df_world = pd.DataFrame(world_results)
    
    # Prétraitement des colonnes (Gestion des types)
    # Dans les CSV mondiaux, 'position' est parfois une chaîne, on la convertit
    df_world['position'] = pd.to_numeric(df_world['position'], errors='coerce')
    df_world_clean = df_world.dropna(subset=['position']).sort_values('event_name') 

    w_col1, w_col2 = st.columns([1, 2.5])

    with w_col1:
        st.subheader("📊 Stats Mondiales")
        total_world = len(df_world)
        # Calcul des médailles (Position 1, 2 ou 3)
        w_gold = len(df_world[df_world['position'] == 1])
        w_silver = len(df_world[df_world['position'] == 2])
        w_bronze = len(df_world[df_world['position'] == 3])
        
        st.metric("Participations", total_world)
        st.write(f"🥇 Titres : {w_gold}")
        st.write(f"🥈 Argent : {w_silver}")
        st.write(f"🥉 Bronze : {w_bronze}")

    with w_col2:
        # --- VISUALISATION : GRAPHE DE POSITION AUX MONDIAUX ---
        # Note : On utilise 'event_name' pour l'axe X car l'année est dans l'index meeting
        fig_world = px.bar(
            df_world_clean,
            x="event_name", 
            y="position",
            color="position",
            title=f"Positions de {selected_athlete} aux Mondiaux par Meeting",
            labels={"event_name": "Édition", "position": "Rang"},
            template="plotly_white",
            color_continuous_scale="Viridis_r"
        )
        fig_world.update_yaxes(autorange="reversed") # Le rang 1 reste le meilleur
        st.plotly_chart(fig_world, use_container_width=True)

        # Tableau secondaire
        with st.expander("Voir le détail des résultats mondiaux"):
            st.dataframe(
                df_world[['event', 'event_name', 'position', 'mark', 'country']], 
                use_container_width=True,
                hide_index=True
            )
else:
    st.info(f"ℹ️ {selected_athlete} n'a pas de résultats enregistrés dans la base des Championnats du Monde.")