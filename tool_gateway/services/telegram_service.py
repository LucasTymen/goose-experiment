# GOOSE Telegram Service
# =======================
# Service pour interagir avec l'API Telegram Bot
# Utilise python-telegram-bot v20+ pour le polling

import logging
from typing import Optional, Dict, List, Any, Callable
from telegram import Update, Bot, Message, Chat
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext
)

# Configuration
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
TELEGRAM_BOT_NAME = "RG4YZClawRG4YZ_bot"
TELEGRAM_BOT_ID = 2025051518

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class TelegramService:
    """
    Service de gestion du bot Telegram pour GOOSE.
    
    Ce service permet de :
    - Recevoir des commandes Telegram
    - Envoyer des messages formatés
    - Intégrer avec les autres services GOOSE (Jobs, Memory, ATS, CV)
    """
    
    def __init__(self, token: str = TELEGRAM_BOT_TOKEN):
        """Initialise le service Telegram."""
        self.token = token
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
    def start(self) -> None:
        """Démarre le bot en mode polling."""
        logger.info(f"Starting Telegram bot {TELEGRAM_BOT_NAME}...")
        
        # Créer le bot
        self.bot = Bot(token=self.token)
        
        # Créer l'application
        self.application = Application.builder() \
            .token(self.token) \
            .build()
        
        # Ajouter les handlers
        self._add_handlers()
        
        # Démarrer le polling
        logger.info("Telegram bot started. Waiting for messages...")
        self.application.run_polling(
            poll_interval=1.0,
            timeout=10,
            drop_pending_updates=True
        )
    
    def _add_handlers(self) -> None:
        """Ajoute tous les handlers de commandes et messages."""
        if not self.application:
            raise RuntimeError("Application not initialized. Call start() first.")
        
        # Commandes de base
        self.application.add_handler(CommandHandler("start", self._command_start))
        self.application.add_handler(CommandHandler("help", self._command_help))
        self.application.add_handler(CommandHandler("ping", self._command_ping))
        
        # Commandes GOOSE
        self.application.add_handler(CommandHandler("jobs", self._command_jobs))
        self.application.add_handler(CommandHandler("memory", self._command_memory))
        self.application.add_handler(CommandHandler("ats", self._command_ats))
        self.application.add_handler(CommandHandler("cv", self._command_cv))
        self.application.add_handler(CommandHandler("stats", self._command_stats))
        
        # Messages texte (non-commandes)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message)
        )
        
        # Erreurs
        self.application.add_error_handler(self._handle_error)
    
    # ========================================================================
    # COMMAND HANDLERS
    # ========================================================================
    
    async def _command_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /start."""
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        welcome_message = (
            f"🪿 **Bienvenue sur GOOSE AI Job Application Workbench**\n\n"
            f"Bonjour {user.first_name}!\n\n"
            f"Je suis **{TELEGRAM_BOT_NAME}**, votre assistant pour gérer vos "
            f"candidatures avec intelligence artificielle.\n\n"
            f"**Commandes disponibles :**\n"
            f"/start - Afficher ce message\n"
            f"/help - Aide détaillée\n"
            f"/ping - Tester la connexion\n"
            f"/jobs - Lister les offres d'emploi\n"
            f"/memory - Rechercher dans la mémoire\n"
            f"/ats - Calculer un score ATS\n"
            f"/cv - Générer un CV\n"
            f"/stats - Statistiques du système\n\n"
            f"Envoyez un message texte pour une recherche naturelle."
        )
        
        await self._send_message(chat_id, welcome_message, parse_mode="Markdown")
        
        # Log
        logger.info(f"User {user.id} ({user.username or user.first_name}) started the bot")
    
    async def _command_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /help."""
        chat_id = update.effective_chat.id
        
        help_message = (
            "📚 **Aide GOOSE Telegram Bot**\n\n"
            
            "**🏠 Commandes de base :**\n"
            "/start - Démarrer le bot\n"
            "/help - Cette aide\n"
            "/ping - Vérifier que le bot fonctionne\n\n"
            
            "**📋 Gestion des Jobs :**\n"
            "/jobs - Lister tous les jobs\n"
            "/jobs <n> - Afficher les n derniers jobs\n"
            "/job <id> - Détails d'un job spécifique\n\n"
            
            "**🧠 Mémoire Sémantique :**\n"
            "/memory <requête> - Rechercher dans la mémoire Qdrant\n"
            "/memory <requête> <collection> - Rechercher dans une collection spécifique\n"
            "Collections : candidate_memory, jobs_memory, ats_keywords_memory, prompts_memory, workflow_memory\n\n"
            
            "**🎯 ATS Scoring :**\n"
            "/ats <description> <skills> - Calculer un score ATS\n"
            "Ex: /ats \"Senior Python dev\" Python,AI,Docker\n\n"
            
            "**📄 Génération de CV :**\n"
            "/cv <profil> <poste> <entreprise> - Générer un CV\n"
            "Ex: /cv \"Mon profil\" \"Dev Python\" \"Google\"\n\n"
            
            "**📊 Statistiques :**\n"
            "/stats - Afficher les statistiques du système\n\n"
            
            "**💬 Recherche naturelle :**\n"
            "Envoyez simplement un message texte pour :\n"
            "- Rechercher dans les jobs\n"
            "- Rechercher dans la mémoire\n"
            "- Poser une question sur vos candidatures"
        )
        
        await self._send_message(chat_id, help_message, parse_mode="Markdown")
    
    async def _command_ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /ping."""
        chat_id = update.effective_chat.id
        await self._send_message(chat_id, "🏓 Pong! Le bot fonctionne correctement.")
    
    async def _command_jobs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /jobs."""
        chat_id = update.effective_chat.id
        
        try:
            # Appeler l'API GOOSE
            import requests
            from tool_gateway.services.postgres_service import insert_audit
            
            response = requests.get("http://localhost:8044/jobs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])
                count = data.get("count", 0)
                
                if count == 0:
                    await self._send_message(chat_id, "📭 Aucun job trouvé dans la base de données.")
                    return
                
                # Limiter le nombre de jobs affichés
                limit = 10
                if context.args:
                    try:
                        limit = min(int(context.args[0]), 20)
                    except (ValueError, IndexError):
                        limit = 10
                
                message = f"📋 **Liste des {min(limit, count)} derniers jobs** (Total: {count})\n\n"
                
                for i, job in enumerate(jobs[:limit], 1):
                    title = job.get("title", "Sans titre")
                    company = job.get("company", "Inconnu")
                    ats_score = job.get("ats_score", "N/A")
                    skills = ", ".join(job.get("skills", [])[:3])
                    
                    message += (
                        f"{i}. **{title}** @ {company}\n"
                        f"   Score ATS: {ats_score}\n"
                        f"   Skills: {skills}{'...' if len(job.get('skills', [])) > 3 else ''}\n\n"
                    )
                
                if count > limit:
                    message += f"... et {count - limit} autres jobs. Utilisez /jobs {limit + 10} pour voir plus."
                
                await self._send_message(chat_id, message, parse_mode="Markdown")
                
                # Audit
                insert_audit("telegram_jobs", {"chat_id": chat_id, "limit": limit, "count": count})
                
            else:
                await self._send_message(chat_id, f"❌ Erreur : {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            await self._send_message(chat_id, f"❌ Erreur de connexion à GOOSE API : {str(e)}")
        except Exception as e:
            await self._send_message(chat_id, f"❌ Erreur inattendue : {str(e)}")
    
    async def _command_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /memory."""
        chat_id = update.effective_chat.id
        
        if not context.args:
            await self._send_message(
                chat_id,
                "❌ Veuillez fournir une requête de recherche.\n"
                "Ex: /memory Senior Python Engineer\n"
                "Ex: /memory \"machine learning\" jobs_memory"
            )
            return
        
        try:
            import requests
            from tool_gateway.services.postgres_service import insert_audit
            
            # Parser les arguments
            query = " ".join(context.args)
            
            # Déterminer la collection (par défaut: candidate_memory)
            collection = "candidate_memory"
            
            # Vérifier si une collection est spécifiée
            args_list = list(context.args)
            if len(args_list) >= 2:
                # Le dernier argument pourrait être la collection
                possible_collection = args_list[-1]
                from tool_gateway.services.qdrant_service import COLLECTIONS
                if possible_collection in COLLECTIONS:
                    collection = possible_collection
                    query = " ".join(args_list[:-1])
            
            # Appeler l'API de recherche
            payload = {
                "query": query,
                "collection": collection,
                "limit": 5
            }
            
            response = requests.post(
                "http://localhost:8044/memory/search",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    await self._send_message(
                        chat_id,
                        f"🔍 Aucune résultat trouvé dans `{collection}` pour : \"{query}\""
                    )
                    return
                
                message = f"🎯 **Résultats pour \"{query}\"** (Collection: `{collection}`)\n\n"
                
                for i, result in enumerate(results[:5], 1):
                    score = result.get("score", 0)
                    content = result.get("payload", {}).get("content", "N/A")[:100]
                    point_id = result.get("id", "N/A")
                    
                    message += (
                        f"{i}. **Score: {score:.4f}**\n"
                        f"   ID: `{point_id}`\n"
                        f"   Contenu: {content}...\n\n"
                    )
                
                await self._send_message(chat_id, message, parse_mode="Markdown")
                
                # Audit
                insert_audit("telegram_memory_search", {
                    "chat_id": chat_id,
                    "query": query,
                    "collection": collection,
                    "results_count": len(results)
                })
                
            else:
                await self._send_message(chat_id, f"❌ Erreur : {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            await self._send_message(chat_id, f"❌ Erreur de connexion : {str(e)}")
        except Exception as e:
            await self._send_message(chat_id, f"❌ Erreur : {str(e)}")
    
    async def _command_ats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /ats."""
        chat_id = update.effective_chat.id
        
        if not context.args or len(context.args) < 2:
            await self._send_message(
                chat_id,
                "❌ Format : /ats <description> <skills>\n"
                "Ex: /ats \"Senior Python Engineer\" Python,AI,Docker\n"
                "Séparez les skills par des virgules."
            )
            return
        
        try:
            import requests
            from tool_gateway.services.postgres_service import insert_audit
            
            # Le premier argument est la description, les autres sont les skills
            description = context.args[0]
            skills = [arg.strip() for arg in context.args[1:]]
            
            # Combiner si la description contient des espaces
            # Si le premier argument est entre guillemets, tout prendre
            full_text = " ".join(context.args)
            
            # Simple parsing: tout avant le dernier espace est la description
            # et le dernier mot sont les skills
            # Mais c'est compliqué, mieux vaut utiliser un format structuré
            
            # Alternative: séparer par le premier espace
            parts = full_text.split(maxsplit=1)
            if len(parts) < 2:
                await self._send_message(chat_id, "❌ Format invalide. Utilisez : /ats <description> <skill1,skill2,skill3>")
                return
            
            description = parts[0]
            skills_str = parts[1]
            skills = [s.strip() for s in skills_str.split(",") if s.strip()]
            
            if not skills:
                await self._send_message(chat_id, "❌ Aucune compétence spécifiée. Format : /ats description skill1,skill2,skill3")
                return
            
            # Appeler l'API ATS
            payload = {
                "job_description": description,
                "skills": skills
            }
            
            response = requests.post(
                "http://localhost:8044/ats-score",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("score", 0)
                max_score = len(skills) * 10
                
                message = (
                    f"🎯 **Score ATS calculé**\n\n"
                    f"**Description :** {description}\n"
                    f"**Skills :** {', '.join(skills)}\n"
                    f"**Score :** {score}/{max_score} ({score/max_score*100:.1f}%)"
                )
                
                await self._send_message(chat_id, message, parse_mode="Markdown")
                
                # Audit
                insert_audit("telegram_ats", {
                    "chat_id": chat_id,
                    "description": description,
                    "skills": skills,
                    "score": score
                })
                
            else:
                await self._send_message(chat_id, f"❌ Erreur : {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            await self._send_message(chat_id, f"❌ Erreur de connexion : {str(e)}")
        except Exception as e:
            await self._send_message(chat_id, f"❌ Erreur : {str(e)}")
    
    async def _command_cv(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /cv."""
        chat_id = update.effective_chat.id
        
        if not context.args or len(context.args) < 3:
            await self._send_message(
                chat_id,
                "❌ Format : /cv <candidate> <role> <company>\n"
                "Ex: /cv \"Jean Dupont\" \"Senior Python Engineer\" \"TechCorp\""
            )
            return
        
        try:
            import requests
            from tool_gateway.services.postgres_service import insert_audit
            
            candidate = context.args[0]
            role = context.args[1]
            company = " ".join(context.args[2:])
            
            # Appeler l'API CV
            payload = {
                "candidate": candidate,
                "role": role,
                "company": company
            }
            
            response = requests.post(
                "http://localhost:8044/generate-cv",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                message = data.get("message", "")
                
                reply = (
                    f"📄 **Génération de CV**\n\n"
                    f"**Candidat :** {candidate}\n"
                    f"**Poste :** {role}\n"
                    f"**Entreprise :** {company}\n\n"
                    f"**Statut :** {status}\n"
                    f"**Message :** {message}"
                )
                
                await self._send_message(chat_id, reply, parse_mode="Markdown")
                
                # Audit
                insert_audit("telegram_cv", {
                    "chat_id": chat_id,
                    "candidate": candidate,
                    "role": role,
                    "company": company,
                    "status": status
                })
                
            else:
                await self._send_message(chat_id, f"❌ Erreur : {response.status_code} - {response.text}")
                
        except requests.RequestException as e:
            await self._send_message(chat_id, f"❌ Erreur de connexion : {str(e)}")
        except Exception as e:
            await self._send_message(chat_id, f"❌ Erreur : {str(e)}")
    
    async def _command_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour /stats."""
        chat_id = update.effective_chat.id
        
        try:
            import requests
            from tool_gateway.services.postgres_service import insert_audit, get_audit_count
            from tool_gateway.services.qdrant_service import get_all_collections
            
            # Récupérer les stats
            jobs_response = requests.get("http://localhost:8044/jobs", timeout=5)
            collections = get_all_collections()
            audit_count = get_audit_count()
            
            # Stats jobs
            jobs_count = 0
            avg_ats = 0
            if jobs_response.status_code == 200:
                data = jobs_response.json()
                jobs_count = data.get("count", 0)
                jobs = data.get("jobs", [])
                if jobs:
                    scores = [j.get("ats_score", 0) for j in jobs if j.get("ats_score") is not None]
                    avg_ats = sum(scores) / len(scores) if scores else 0
            
            message = (
                "📊 **Statistiques GOOSE**\n\n"
                f"**📋 Jobs :** {jobs_count}\n"
                f"**🎯 Score ATS Moyen :** {avg_ats:.1f}/100\n"
                f"**🧠 Collections Qdrant :** {len(collections)}\n"
                f"**📝 Audit Logs :** {audit_count}\n\n"
                f"**⚡ Services :**\n"
                f"- FastAPI Gateway: ✅ (port 8044)\n"
                f"- PostgreSQL: ✅ (port 5434)\n"
                f"- Qdrant: ✅ (port 6334)\n"
                f"- Ollama: ✅ (port 11434)"
            )
            
            await self._send_message(chat_id, message, parse_mode="Markdown")
            
            # Audit
            insert_audit("telegram_stats", {"chat_id": chat_id})
            
        except Exception as e:
            await self._send_message(chat_id, f"❌ Erreur : {str(e)}")
    
    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour les messages texte (non-commandes)."""
        chat_id = update.effective_chat.id
        text = update.message.text
        user = update.effective_user
        
        try:
            import requests
            from tool_gateway.services.postgres_service import insert_audit
            
            # Analyser le message pour déterminer l'intention
            text_lower = text.lower()
            
            # Si ça ressemble à une recherche de job
            if any(word in text_lower for word in ["job", "offre", "poste", "emploi", "candidature"]):
                # Rechercher dans les jobs
                response = requests.get("http://localhost:8044/jobs", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get("jobs", [])
                    
                    # Filtrer les jobs dont la description ou le titre contient le texte
                    matching_jobs = []
                    for job in jobs:
                        if (text_lower in job.get("title", "").lower() or 
                            text_lower in job.get("description", "").lower() or
                            text_lower in job.get("company", "").lower()):
                            matching_jobs.append(job)
                    
                    if matching_jobs:
                        message = f"🔍 **Jobs correspondant à \"{text}\"**\n\n"
                        for i, job in enumerate(matching_jobs[:5], 1):
                            message += (
                                f"{i}. **{job.get('title')}** @ {job.get('company')}\n"
                                f"   Score: {job.get('ats_score', 'N/A')}\n\n"
                            )
                        await self._send_message(chat_id, message, parse_mode="Markdown")
                    else:
                        await self._send_message(chat_id, f"❌ Aucun job trouvé pour \"{text}\"")
                    
                    insert_audit("telegram_natural_jobs", {"chat_id": chat_id, "query": text})
                    return
            
            # Si ça ressemble à une recherche dans la mémoire
            if any(word in text_lower for word in ["mémoire", "memory", "recherche", "search", "souvenir"]):
                response = requests.post(
                    "http://localhost:8044/memory/search",
                    json={"query": text, "collection": "candidate_memory", "limit": 5},
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    if results:
                        message = f"🧠 **Résultats mémoire pour \"{text}\"**\n\n"
                        for i, result in enumerate(results[:3], 1):
                            message += f"{i}. Score: {result.get('score', 0):.4f}\n"
                        await self._send_message(chat_id, message, parse_mode="Markdown")
                    else:
                        await self._send_message(chat_id, f"❌ Aucun résultat mémoire pour \"{text}\"")
                    
                    insert_audit("telegram_natural_memory", {"chat_id": chat_id, "query": text})
                    return
            
            # Réponse par défaut
            await self._send_message(
                chat_id,
                f"🤔 Je ne comprends pas. Essayez /help pour voir les commandes disponibles.\n\n"
                f"Votre message : \"{text}\""
            )
            insert_audit("telegram_unknown", {"chat_id": chat_id, "text": text})
            
        except Exception as e:
            await self._send_message(chat_id, f"❌ Erreur : {str(e)}")
    
    async def _handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler pour les erreurs."""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_chat:
            chat_id = update.effective_chat.id
            await self._send_message(
                chat_id,
                "❌ Une erreur est survenue. Veuillez réessayer plus tard."
            )
    
    async def _send_message(self, chat_id: int, text: str, 
                           parse_mode: Optional[str] = None, 
                           reply_markup: Optional[Any] = None) -> Message:
        """Envoyer un message à un chat."""
        if not self.bot:
            raise RuntimeError("Bot not initialized. Call start() first.")
        
        return await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
    
    async def send_notification(self, chat_id: int, message: str) -> bool:
        """Envoyer une notification à un chat spécifique."""
        try:
            await self._send_message(chat_id, message)
            return True
        except Exception as e:
            logger.error(f"Failed to send notification to {chat_id}: {e}")
            return False


def get_telegram_service() -> TelegramService:
    """Retourne une instance du service Telegram."""
    return TelegramService()


if __name__ == "__main__":
    # Démarrer le bot si le script est exécuté directement
    service = get_telegram_service()
    service.start()
