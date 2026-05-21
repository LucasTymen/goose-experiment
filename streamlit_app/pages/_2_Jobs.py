# GOOSE Jobs Management
# ======================
# Page pour gérer les offres d'emploi avec calcul ATS

import streamlit as st
from typing import Optional, List, Dict, Any
from utils.api_client import APIClient
from datetime import datetime

# Initialisation
api = APIClient()


def show():
    """Affiche la page Jobs Management."""
    st.title("📋 Jobs Management")
    st.markdown("""
    Gérez vos offres d'emploi, calculez les scores ATS et suivez vos candidatures.
    **Fonctionnalités :** Liste des jobs, création avec scoring automatique, recalcul ATS.
    """)
    st.markdown("---")
    
    # === SECTION 1: STATISTIQUES ET FILTRES ===
    st.header("📊 Statistiques")
    
    # Récupérer tous les jobs
    jobs_result = api.list_jobs()
    
    if jobs_result.get("status") == "error":
        st.error(f"❌ Erreur lors de la récupération des jobs : {jobs_result.get('error', 'Inconnu')}")
        st.stop()
    
    jobs = jobs_result.get("jobs", [])
    count = jobs_result.get("count", 0)
    
    # Métriques globales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", count)
    
    with col2:
        # Calculer la moyenne des scores ATS
        scores = [job.get("ats_score", 0) for job in jobs if job.get("ats_score") is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        st.metric("Score ATS Moyen", f"{avg_score:.1f}")
    
    with col3:
        # Compter les jobs avec skills
        jobs_with_skills = sum(1 for job in jobs if job.get("skills") and len(job.get("skills", [])) > 0)
        st.metric("Jobs avec Skills", jobs_with_skills)
    
    with col4:
        # Statut API
        health = api.health()
        st.metric("API Status", "✅ Healthy" if health.get("status") == "healthy" else "❌ Down")
    
    st.markdown("---")
    
    # === SECTION 2: LISTE DES JOBS ===
    st.header("📋 Liste des Jobs")
    
    if count == 0:
        st.info("Aucun job trouvé. Utilisez le formulaire ci-dessous pour en créer un.")
    else:
        # Options de filtrage
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtre par score minimum
            min_score_filter = st.slider(
                "Score ATS minimum :",
                0, 100, 0,
                help="Filtrer les jobs avec un score ATS supérieur ou égal à cette valeur"
            )
        
        with col2:
            # Filtre par source
            sources = list(set(job.get("source", "unknown") for job in jobs))
            selected_source = st.selectbox(
                "Filtrer par source :",
                ["Toutes"] + sorted(sources),
                index=0
            )
        
        with col3:
            # Tri
            sort_by = st.selectbox(
                "Trier par :",
                ["Date (récent d'abord)", "Score ATS (descendant)", "Score ATS (ascendant)", "Titre (A-Z)"],
                index=0
            )
        
        # Appliquer les filtres
        filtered_jobs = []
        for job in jobs:
            # Filtre par score
            if job.get("ats_score") is not None and job.get("ats_score") < min_score_filter:
                continue
            # Filtre par source
            if selected_source != "Toutes" and job.get("source") != selected_source:
                continue
            filtered_jobs.append(job)
        
        # Appliquer le tri
        if sort_by == "Date (récent d'abord)":
            filtered_jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        elif sort_by == "Score ATS (descendant)":
            filtered_jobs.sort(key=lambda x: x.get("ats_score", 0) or 0, reverse=True)
        elif sort_by == "Score ATS (ascendant)":
            filtered_jobs.sort(key=lambda x: x.get("ats_score", 0) or 0)
        elif sort_by == "Titre (A-Z)":
            filtered_jobs.sort(key=lambda x: x.get("title", "").lower())
        
        st.markdown(f"**{len(filtered_jobs)} jobs affichés**")
        
        # Afficher les jobs
        for i, job in enumerate(filtered_jobs, 1):
            display_job_card(job, i)
    
    st.markdown("---")
    
    # === SECTION 3: CRÉATION DE NOUVEAU JOB ===
    st.header("➕ Créer un Nouveau Job")
    
    with st.form("create_job_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input(
                "Titre *",
                placeholder="Ex: Senior Python Engineer",
                label_visibility="collapsed"
            )
            company = st.text_input(
                "Entreprise *",
                placeholder="Ex: TechCorp",
                label_visibility="collapsed"
            )
            location = st.text_input(
                "Localisation",
                placeholder="Ex: Paris, France (Remote)",
                label_visibility="collapsed"
            )
            url = st.text_input(
                "URL de l'offre",
                placeholder="Ex: https://techcorp.com/jobs/senior-python",
                label_visibility="collapsed"
            )
        
        with col2:
            source = st.selectbox(
                "Source",
                ["manual", "linkedin", "indeed", "glassdoor", "company_website", "email", "other"],
                index=0
            )
            skills_input = st.text_input(
                "Compétences (séparées par des virgules)",
                placeholder="Ex: Python, AI, Docker, FastAPI",
                label_visibility="collapsed"
            )
        
        # Description (pleine largeur)
        description = st.text_area(
            "Description *",
            placeholder="Collez ici la description complète de l'offre d'emploi...",
            height=150,
            label_visibility="collapsed"
        )
        
        submitted = st.form_submit_button("💾 Créer le Job", type="primary")
    
    if submitted:
        # Validation
        if not title or not company or not description:
            st.error("❌ Les champs Titre, Entreprise et Description sont obligatoires.")
            st.stop()
        
        # Parser les skills
        skills = [s.strip() for s in skills_input.split(",") if s.strip()] if skills_input else []
        
        with st.spinner("Création du job et calcul du score ATS..."):
            result = api.create_job(
                title=title,
                company=company,
                description=description,
                location=location or None,
                url=url or None,
                source=source,
                skills=skills
            )
        
        if result.get("status") == "created":
            st.success("✅ Job créé avec succès !")
            st.markdown(f"**ID du Job :** `{result.get('job_id')}`")
            st.markdown(f"**Score ATS :** `{result.get('ats_score')}` / {len(skills) * 10 if skills else 'N/A'}")
            
            # Audit
            insert_audit("streamlit_job_create", {
                "job_id": result.get("job_id"),
                "title": title,
                "company": company,
                "ats_score": result.get("ats_score")
            })
            
            # Rafraîchir la page
            st.rerun()
        else:
            st.error(f"❌ Erreur : {result.get('message', result.get('error', 'Inconnu'))}")
    
    st.markdown("---")
    
    # === SECTION 4: RECALCULER LE SCORE ATS ===
    st.header("🔄 Recalculer le Score ATS")
    
    if count > 0:
        with st.form("rescore_form"):
            job_id_to_score = st.selectbox(
                "Sélectionnez un job :",
                [f"{job.get('title')} - {job.get('company')}" for job in jobs],
                index=0
            )
            
            # Extraire l'ID du job sélectionné
            # Le format est "titre - entreprise", il faut trouver le job correspondant
            selected_title, selected_company = job_id_to_score.split(" - ", 1)
            selected_job = next((j for j in jobs 
                               if j.get("title") == selected_title and j.get("company") == selected_company), 
                              None)
            
            if selected_job:
                st.markdown(f"**Job sélectionné :** {selected_job.get('title')} chez {selected_job.get('company')}")
                st.markdown(f"**Score actuel :** {selected_job.get('ats_score', 'N/A')}")
                
                new_skills_input = st.text_input(
                    "Nouvelle liste de compétences (séparées par des virgules)",
                    placeholder="Ex: Python, Machine Learning, FastAPI",
                    value=", ".join(selected_job.get("skills", [])) if selected_job.get("skills") else ""
                )
            
            submitted_rescore = st.form_submit_button("🔄 Recalculer le Score")
        
        if submitted_rescore and selected_job:
            # Parser les nouvelles skills
            new_skills = [s.strip() for s in new_skills_input.split(",") if s.strip()]
            
            with st.spinner("Recalcul du score ATS..."):
                result = api.score_job(selected_job.get("id"), new_skills)
            
            if result.get("status") == "scored":
                st.success("✅ Score ATS recalculé avec succès !")
                st.markdown(f"**Nouveau score :** `{result.get('score')}` / {len(new_skills) * 10 if new_skills else 'N/A'}")
                
                # Audit
                insert_audit("streamlit_job_rescore", {
                    "job_id": selected_job.get("id"),
                    "old_score": selected_job.get("ats_score"),
                    "new_score": result.get("score"),
                    "new_skills": new_skills
                })
                
                st.rerun()
            else:
                st.error(f"❌ Erreur : {result.get('message', result.get('error', 'Inconnu'))}")
    else:
        st.info("Aucun job disponible pour le rescoring. Créez d'abord un job.")


def display_job_card(job: Dict, index: int):
    """Affiche une carte pour un job."""
    with st.expander(f"📌 {index}. {job.get('title', 'Sans titre')} - {job.get('company', 'Inconnu')}"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Titre et entreprise
            st.markdown(f"### {job.get('title', 'Sans titre')}")
            st.markdown(f"**Entreprise :** {job.get('company', 'Inconnu')}")
            
            # Localisation et URL
            if job.get("location"):
                st.markdown(f"**Localisation :** {job.get('location')}")
            if job.get("url"):
                st.markdown(f"**URL :** [{job.get('url')}]({job.get('url')})")
            
            st.markdown("**Source :**")
            st.code(job.get("source", "unknown"), language="text")
            
            # Description (extraits)
            description = job.get("description", "")
            if description:
                st.markdown("**Description :**")
                # Afficher les 200 premiers caractères
                preview = description[:200] + "..." if len(description) > 200 else description
                st.text_area("", preview, height=100, key=f"desc_{index}", label_visibility="collapsed")
        
        with col2:
            # Score ATS
            ats_score = job.get("ats_score")
            if ats_score is not None:
                st.metric("Score ATS", f"{ats_score}/100")
                
                # Barre de progression
                st.progress(min(ats_score / 100, 1.0))
            else:
                st.metric("Score ATS", "Non calculé")
            
            # Skills
            skills = job.get("skills", [])
            if skills and len(skills) > 0:
                st.markdown("**Compétences :**")
                for skill in skills[:5]:  # Afficher max 5 skills
                    st.markdown(f"- {skill}")
                if len(skills) > 5:
                    st.caption(f"+ {len(skills) - 5} autres")
            else:
                st.markdown("*Aucune compétence définie*")
            
            # Métadonnées
            st.markdown("**Créé le :**")
            st.code(job.get("created_at", "N/A"), language="text")
            
            st.markdown("**ID :**")
            st.code(job.get("id", "N/A"), language="text")


def insert_audit(action: str, details: Dict):
    """
    Consigne une action dans l'audit.
    Pour l'instant, affichage dans la console et stockage dans session_state.
    """
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "source": "streamlit",
        **details
    }
    
    print(f"[AUDIT] {audit_entry}")
    
    if "audit_logs" not in st.session_state:
        st.session_state.audit_logs = []
    st.session_state.audit_logs.append(audit_entry)


# Appel direct depuis main.py
if __name__ == "__main__":
    show()
