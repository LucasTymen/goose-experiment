#!/usr/bin/env python3
# GOOSE AI Job Application Workbench
# ====================================
# Application Streamlit principale

import streamlit as st
from utils.api_client import APIClient
from utils.config import STREAMLIT_THEME

# Configuration de l'app
st.set_page_config(
    page_title="GOOSE Workbench",
    page_icon="🪿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thème
if STREAMLIT_THEME == "dark":
    st.markdown("""
    <style>
    .reportview-container .main .block-container {
        background-color: #1e1e1e;
        color: #f0f0f0;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialisation de l'API Client
api = APIClient()


def main():
    """Page principale avec navigation."""
    
    # Sidebar - Navigation
    st.sidebar.title("🪿 GOOSE Workbench")
    st.sidebar.markdown("---")
    
    # Vérification de l'API
    health_status = api.health()
    if health_status.get("status") == "healthy":
        st.sidebar.success("✅ FastAPI Gateway: Healthy")
    else:
        st.sidebar.error("❌ FastAPI Gateway: Inaccessible")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Navigation")
    
    page = st.sidebar.radio(
        "Aller à :",
        [
            "🏠 Accueil",
            "📋 Jobs",
            "👤 Candidate Profile",
            "📄 CV Generator",
            "🧠 Memory Explorer",
            "🔄 Workflows"
        ],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ Infos")
    st.sidebar.info(
        "**GOOSE AI Job Application Workbench**\n\n"
        "Un workbench local pour gérer vos candidatures avec IA."
    )
    
    # Affichage de la page sélectionnée
    if page == "🏠 Accueil":
        show_home()
    elif page == "📋 Jobs":
        st.warning("📌 Page en développement - Priorité 2")
        st.markdown("Cette page sera implémentée après Memory Explorer.")
    elif page == "👤 Candidate Profile":
        st.warning("📌 Page en développement - Priorité 3")
        st.markdown("Cette page sera implémentée après Jobs.")
    elif page == "📄 CV Generator":
        st.warning("📌 Page en développement - Priorité 4")
        st.markdown("Cette page sera implémentée après Candidate Profile.")
    elif page == "🧠 Memory Explorer":
        # Charger la page Memory Explorer
        from pages.Memory_Explorer import show as memory_explorer_show
        memory_explorer_show()
    elif page == "🔄 Workflows":
        st.warning("📌 Page en développement - Priorité 5")
        st.markdown("Cette page sera implémentée après CV Generator.")


def show_home():
    """Affiche la page d'accueil."""
    st.title("🪿 GOOSE AI Job Application Workbench")
    st.markdown("---")
    
    # Statut des services
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🔌 Services")
        health = api.health()
        if health.get("status") == "healthy":
            st.success("✅ FastAPI Gateway")
        else:
            st.error("❌ FastAPI Gateway")
        
        st.markdown("**Prochaines étapes :**")
        st.markdown("1. ✅ Memory Explorer (Terminé)")
        st.markdown("2. ⏳ Jobs Page")
        st.markdown("3. ⏳ Candidate Profile")
        st.markdown("4. ⏳ CV Generator")
    
    with col2:
        st.subheader("📊 Statistiques")
        
        # Récupérer les collections
        collections = api.list_collections()
        if collections.get("status") != "error":
            st.metric("Collections Qdrant", collections.get("count", 0))
        
        # Récupérer les infos root
        root_info = api.root()
        if root_info.get("status"):
            st.metric("Service", root_info.get("service", "N/A"))
    
    with col3:
        st.subheader("🎯 Objectifs")
        st.markdown("""
        - ✅ **Memory Explorer** : Explorer la mémoire Qdrant
        - 📋 **Jobs** : Gérer les offres d'emploi
        - 👤 **Profile** : profil candidat complet
        - 📄 **CV Generator** : Génération intelligente
        - 🔄 **Workflows** : Automatisation avec n8n
        """)
    
    st.markdown("---")
    st.markdown("### 📚 Documentation")
    st.markdown("""
    - [GOOSE Protocol](https://github.com/LucasTymen/goose-experiment/blob/main/tool_gateway/GOOSE_PROTOCOL.md)
    - [Genesis Log](https://github.com/LucasTymen/goose-experiment/blob/main/tool_gateway/logs/GOOSE_GENESIS_LOG.md)
    """)


if __name__ == "__main__":
    main()
