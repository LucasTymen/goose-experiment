# GOOSE Memory Explorer
# =====================
# Page pour explorer et interagir avec la mémoire Qdrant

import streamlit as st
from utils.api_client import APIClient
from utils.config import QDRANT_COLLECTIONS
from datetime import datetime

# Initialisation
api = APIClient()


def show():
    """Affiche la page Memory Explorer."""
    st.title("🧠 Memory Explorer")
    st.markdown("""
    Explorez et gérez la mémoire vectorielle de Goose.
    **Collections disponibles :** Qdrant avec embeddings Ollama (nomic-embed-text, 768D).
    """)
    st.markdown("---")
    
    # === SECTION 1: STATUT DES COLLECTIONS ===
    st.header("📊 Collections Qdrant")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Récupérer les collections
        collections_result = api.list_collections()
        
        if collections_result.get("status") == "error":
            st.error(f"❌ Erreur : {collections_result.get('error', 'Inconnu')}")
        else:
            collections = collections_result.get("collections", [])
            count = collections_result.get("count", 0)
            
            st.metric("Nombre de collections", count)
            
            if count > 0:
                st.markdown("**Liste des collections :**")
                for i, collection in enumerate(collections, 1):
                    st.markdown(f"{i}. `{collection}`")
            else:
                st.warning("Aucune collection trouvée. Initialisez-les avec le bouton ci-dessous.")
    
    with col2:
        st.markdown("### ⚡ Actions")
        if st.button("🔄 Initialiser toutes les collections"):
            with st.spinner("Initialisation en cours..."):
                init_result = api.init_collections()
                if init_result.get("status") == "initialized":
                    st.success("✅ Collections initialisées avec succès !")
                    st.json(init_result)
                    st.rerun()  # Rafraîchir la page
                else:
                    st.error(f"❌ Erreur : {init_result.get('error', 'Inconnu')}")
    
    st.markdown("---")
    
    # === SECTION 2: RECHERCHE SÉMANTIQUE ===
    st.header("🔍 Recherche Sémantique")
    
    with st.form("search_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input(
                "Requête de recherche :",
                placeholder="Ex: Python AI engineer with 5 years experience",
                label_visibility="collapsed"
            )
        
        with col2:
            collection = st.selectbox(
                "Collection :",
                options=QDRANT_COLLECTIONS,
                index=0  # candidate_memory par défaut
            )
        
        limit = st.slider("Nombre de résultats :", 1, 10, 5)
        
        submitted = st.form_submit_button("🔎 Rechercher")
    
    if submitted and query:
        with st.spinner(f"Recherche dans {collection}..."):
            result = api.search_memory(
                query=query,
                collection=collection,
                limit=limit
            )
            
            if result.get("status") == "completed":
                display_results(result, query, collection)
            elif result.get("status") == "error":
                st.error(f"❌ Erreur : {result.get('error', 'Inconnu')}")
            else:
                st.warning(f"⚠️ Réponse inattendue : {result}")
    
    st.markdown("---")
    
    # === SECTION 3: STOCKER EN MÉMOIRE ===
    st.header("💾 Stockage en Mémoire")
    
    with st.form("store_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            content = st.text_area(
                "Contenu à stocker :",
                placeholder="Ex: Mon expérience en Python et machine learning...",
                label_visibility="collapsed",
                height=100
            )
        
        with col2:
            store_collection = st.selectbox(
                "Collection :",
                options=QDRANT_COLLECTIONS,
                index=0,
                key="store_collection"
            )
        
        submitted_store = st.form_submit_button("💾 Stockage")
    
    if submitted_store and content:
        with st.spinner(f"Stockage dans {store_collection}..."):
            result = api.store_memory(content)
            
            if result.get("status") == "stored":
                st.success(f"✅ Contenu stocké avec succès !")
                st.code(f"Point ID: {result.get('point_id')}", language="text")
                
                # Audit
                insert_audit("streamlit_memory_store", {
                    "point_id": result.get("point_id"),
                    "collection": store_collection,
                    "content_length": len(content)
                })
                
                st.rerun()
            elif result.get("status") == "error":
                st.error(f"❌ Erreur : {result.get('error', 'Inconnu')}")
            else:
                st.warning(f"⚠️ Réponse inattendue : {result}")
    
    st.markdown("---")
    
    # === SECTION 4: STATISTIQUES ===
    st.header("📈 Statistiques")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("FastAPI Status", "✅ Healthy" if api.health().get("status") == "healthy" else "❌ Down")
    
    with col2:
        collections = api.list_collections()
        st.metric("Collections", collections.get("count", 0))
    
    with col3:
        root = api.root()
        st.metric("Service", root.get("service", "N/A"))


def display_results(result: dict, query: str, collection: str):
    """Affiche les résultats de recherche."""
    st.subheader(f"🎯 Résultats pour : \"{query}\"")
    st.markdown(f"**Collection :** `{collection}` | **Nombre :** {len(result.get('results', []))}")
    
    if not result.get("results"):
        st.info("Aucun résultat trouvé. Essayez une requête différente ou stockez d'abord du contenu.")
        return
    
    for i, item in enumerate(result["results"], 1):
        with st.expander(f"📌 Résultat {i} - Score: {item['score']:.4f}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**Contenu :**")
                content = item.get("payload", {}).get("content", "N/A")
                st.code(content, language="text")
            
            with col2:
                st.markdown("**Métadonnées :**")
                st.json({
                    "ID": item.get("id", "N/A"),
                    "Score": f"{item['score']:.4f}"
                })
    
    # Audit
    insert_audit("streamlit_memory_search", {
        "query": query[:100],  # Truncated for audit
        "collection": collection,
        "results_count": len(result.get("results", []))
    })


def insert_audit(action: str, details: dict):
    """
    Consigne une action dans l'audit (pour l'instant, juste un log local).
    À terme, appel à FastAPI /audit ou directement PostgreSQL.
    """
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "source": "streamlit",
        **details
    }
    
    # Pour l'instant, on affiche dans la console
    # Plus tard: appel à FastAPI ou insertion directe en PostgreSQL
    print(f"[AUDIT] {audit_entry}")
    
    # Stocker dans une session Streamlit pour affichage
    if "audit_logs" not in st.session_state:
        st.session_state.audit_logs = []
    st.session_state.audit_logs.append(audit_entry)


# Appel direct depuis main.py
if __name__ == "__main__":
    show()
