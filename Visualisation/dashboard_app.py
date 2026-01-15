import streamlit as st

st.set_page_config(
    page_title="Accueil - Dashboard Athlétisme",
    page_icon="🏠",
    layout="wide"
)

st.title("🏅 Dashboard de l'Athlétisme Mondial")
st.sidebar.success("Sélectionnez une analyse ci-dessus.")

st.markdown("---")
st.image("https://images.unsplash.com/photo-1594381898411-846e7d193883?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8fHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
         caption="Photo by sporlab on Unsplash", use_column_width=True)

st.subheader("Bienvenue !")
st.markdown("""
Cette application interactive permet d'explorer les données des **Jeux Olympiques (1896-2022)** et des **Championnats du Monde d'athlétisme (depuis 1983)**.

### Explorez les données via le menu de navigation sur la gauche pour découvrir :
- **Les fiches détaillées** par athlète et par discipline.
- **Des analyses globales** sur la répartition des médailles, l'évolution historique et plus encore.
- **Des statistiques approfondies** sur les profils des athlètes et les points forts de chaque nation.

Cette application a été construite en Python avec Streamlit et est alimentée par une base de données MongoDB.
""")