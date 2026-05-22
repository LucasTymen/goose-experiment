"""
Memory Policy Engine for GOOSE Agent Runtime
===========================================

Determines WHEN and WHAT to retrieve from memory based on user input and context.
This is the "decision layer" that connects user intent to memory retrieval.
"""

from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime

from .memory_taxonomy import MemoryType, MEMORY_COLLECTIONS, get_collection


class PolicyType(Enum):
    """Types of retrieval policies"""
    INTENT_BASED = "intent_based"      # Triggered by specific intents
    KEYWORD_BASED = "keyword_based"    # Triggered by keywords in input
    CONTEXTUAL = "contextual"          # Triggered by conversation context
    TEMPORAL = "temporal"            # Triggered by time-based rules
    WORKFLOW_BASED = "workflow_based"  # Triggered by workflow state


@dataclass
class RetrievalPolicy:
    """
    Defines a policy for when and how to retrieve memory.
    
    A policy answers:
    - WHEN should we retrieve? (triggers)
    - WHAT should we retrieve? (collection, filters)
    - HOW should we retrieve? (parameters)
    """
    name: str
    policy_type: PolicyType = PolicyType.INTENT_BASED
    
    # Triggers: when to activate this policy
    intents: List[str] = field(default_factory=list)  # For INTENT_BASED
    keywords: List[str] = field(default_factory=list)  # For KEYWORD_BASED
    regex_patterns: List[str] = field(default_factory=list)  # For pattern matching
    
    # Target: what to retrieve
    collection: str = ""
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    
    # Retrieval parameters
    limit: int = 5
    confidence_threshold: float = 0.7
    
    # Priority (higher = executed first)
    priority: int = 1
    
    # Contextual conditions
    requires_context: bool = False
    context_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Post-retrieval processing
    post_processor: Optional[Callable] = None
    
    def __post_init__(self):
        # Validate collection exists
        if self.collection and self.collection not in MEMORY_COLLECTIONS:
            raise ValueError(f"Unknown collection: {self.collection}")
    
    def matches(self, user_input: str, intent: Optional[str] = None, 
                context: Optional[Dict] = None) -> bool:
        """Check if this policy should be triggered"""
        
        # Check intent-based triggers
        if self.intents and intent:
            if intent.lower() in [i.lower() for i in self.intents]:
                return True
        
        # Check keyword-based triggers
        if self.keywords:
            input_lower = user_input.lower()
            for keyword in self.keywords:
                if keyword.lower() in input_lower:
                    return True
        
        # Check regex patterns
        if self.regex_patterns:
            for pattern in self.regex_patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return True
        
        # Check contextual conditions
        if self.requires_context and context:
            for key, value in self.context_conditions.items():
                if context.get(key) != value:
                    return False
            return True
        
        return False
    
    def get_retrieval_params(self, user_id: str) -> Dict[str, Any]:
        """Get parameters for retrieval"""
        return {
            "collection": self.collection,
            "limit": self.limit,
            "confidence_threshold": self.confidence_threshold,
            "metadata_filters": {**self.metadata_filters, "user_id": user_id},
        }


class MemoryPolicyEngine:
    """
    Main engine for determining memory retrieval policies.
    
    This is the core of the "memory loop" - it decides:
    1. Should we retrieve memory for this input?
    2. What type of memory should we retrieve?
    3. From which collections?
    4. With what parameters?
    """
    
    def __init__(self):
        self.policies = self._initialize_policies()
    
    def _initialize_policies(self) -> Dict[str, RetrievalPolicy]:
        """Initialize all retrieval policies"""
        return {
            # ========================================================================
            # LANGUAGE & COMMUNICATION POLICIES
            # ========================================================================
            
            "language_preference": RetrievalPolicy(
                name="language_preference",
                policy_type=PolicyType.KEYWORD_BASED,
                intents=["language", "langue", "français", "english", "spanish", "german"],
                keywords=["parlons", "en français", "in english", "hablamos", "auf deutsch",
                         "langue", "language", "idioma", "sprache"],
                regex_patterns=[r"parlons\s+(\w+)", r"en\s+(\w+)", r"in\s+(\w+)"],
                collection="preferences_memory",
                metadata_filters={"preference_type": "language"},
                limit=3,
                confidence_threshold=0.8,
                priority=10,
            ),
            
            "communication_style": RetrievalPolicy(
                name="communication_style",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["formel", "informel", "professionnel", "détendu", 
                         "formal", "casual", "professional", "relaxed",
                         "style", "ton", "tone"],
                collection="preferences_memory",
                metadata_filters={"preference_type": "style"},
                limit=3,
                confidence_threshold=0.75,
                priority=8,
            ),
            
            # ========================================================================
            # CANDIDATE PROFILE POLICIES
            # ========================================================================
            
            "cv_generation": RetrievalPolicy(
                name="cv_generation",
                policy_type=PolicyType.INTENT_BASED,
                intents=["cv", "curriculum", "resume"],
                keywords=["génère mon cv", "generate cv", "mon curriculum", "my resume",
                         "créer cv", "create resume", "mettre à jour cv", "update resume"],
                regex_patterns=[r"(génère|générer|créer|create)\s+(mon|un)?\s*(CV|cv|curriculum|resume)",
                               r"(update|mettre à jour)\s+(mon|le)?\s*(CV|cv)"],
                collection="candidate_memory",
                metadata_filters={"memory_type": "profile"},
                limit=5,
                confidence_threshold=0.8,
                priority=10,
            ),
            
            "skills_review": RetrievalPolicy(
                name="skills_review",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["compétences", "skills", "expertise", "savoir-faire",
                         "quelles sont mes compétences", "what are my skills"],
                collection="candidate_memory",
                metadata_filters={"memory_type": "skills"},
                limit=5,
                confidence_threshold=0.75,
                priority=8,
            ),
            
            "experience_review": RetrievalPolicy(
                name="experience_review",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["expérience", "experience", "parcours", "career",
                         "mon expérience", "my experience", "histoire professionnelle"],
                collection="candidate_memory",
                metadata_filters={"memory_type": "experience"},
                limit=5,
                confidence_threshold=0.75,
                priority=8,
            ),
            
            # ========================================================================
            # JOB SEARCH & APPLICATION POLICIES
            # ========================================================================
            
            "job_search": RetrievalPolicy(
                name="job_search",
                policy_type=PolicyType.INTENT_BASED,
                intents=["job_search", "find_jobs"],
                keywords=["trouver un job", "find a job", "recherche emploi", "job search",
                         "quels jobs", "what jobs", "offres", "offers",
                         "correspond", "correspondent", "match", "fits"],
                regex_patterns=[r"(trouver|trouve|find)\s+(un|des)?\s*(job|emploi|offre)",
                               r"(quels|quelles|which)\s+(jobs|offres|offers)",
                               r"(correspond|match|fit)\s+(à|my)\s+(profil|profile)"],
                collection="jobs_memory",
                metadata_filters={"status": "saved"},
                limit=10,
                confidence_threshold=0.7,
                priority=10,
            ),
            
            "job_application": RetrievalPolicy(
                name="job_application",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["postuler", "apply", "candidature", "application",
                         "candidater", "envoyer cv", "send cv", "submit application"],
                regex_patterns=[r"(postuler|apply|envoyer|candidater)\s+(à|for|to)\s+",
                               r"(envoyer|send)\s+(mon|le)?\s*(CV|cv)"],
                collection="jobs_memory",
                metadata_filters={"status": "applied"},
                limit=8,
                confidence_threshold=0.75,
                priority=9,
            ),
            
            "job_match": RetrievalPolicy(
                name="job_match",
                policy_type=PolicyType.INTENT_BASED,
                intents=["job_match", "profile_match"],
                keywords=["quels jobs correspondent", "which jobs fit", "jobs matching",
                         "meilleur match", "best fit", "correspondance", "matching"],
                regex_patterns=[r"(quels|which|what)\s+(jobs|offres)?\s*(correspond|match|fit)",
                               r"(meilleur|best|top)\s+(match|fit|correspondance)"],
                collection="jobs_memory",
                # This policy retrieves BOTH jobs and candidate profile
                limit=15,
                confidence_threshold=0.7,
                priority=10,
            ),
            
            # ========================================================================
            # ATS OPTIMIZATION POLICIES
            # ========================================================================
            
            "ats_optimization": RetrievalPolicy(
                name="ats_optimization",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["ats", "applicant tracking", "optimiser", "optimize",
                         "score ats", "ats score", "mots-clés", "keywords",
                         "passer les ats", "beat ats", "ats friendly"],
                collection="ats_memory",
                limit=8,
                confidence_threshold=0.8,
                priority=9,
            ),
            
            "ats_keywords": RetrievalPolicy(
                name="ats_keywords",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["mots-clés", "keywords", "compétences clés", "key skills",
                         "ats keywords", "cv keywords", "resume keywords"],
                collection="ats_memory",
                metadata_filters={"category": "keywords"},
                limit=10,
                confidence_threshold=0.75,
                priority=8,
            ),
            
            "ats_best_practices": RetrievalPolicy(
                name="ats_best_practices",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["bonnes pratiques", "best practices", "conseils ats", "ats tips",
                         "comment optimiser", "how to optimize", "ats guide"],
                collection="ats_memory",
                metadata_filters={"category": "best_practice"},
                limit=5,
                confidence_threshold=0.8,
                priority=7,
            ),
            
            # ========================================================================
            # WORKFLOW & TOOL POLICIES
            # ========================================================================
            
            "n8n_workflow": RetrievalPolicy(
                name="n8n_workflow",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["n8n", "workflow", "automatiser", "automate",
                         "scraper", "scrape", "extraire", "extract",
                         "url", "lien", "site web", "website",
                         "annonce", "job posting", "offre d'emploi"],
                regex_patterns=[r"(scraper|scrape|extraire|extract)\s+(une|an|a)?\s*(annonce|url|lien|site)",
                               r"(crée|create|génère|generate)\s+(un|a)?\s*(workflow|n8n)",
                               r"(exécuter|run|lancer|start)\s+(un|a)?\s*(workflow)"],
                collection="workflow_memory",
                limit=5,
                confidence_threshold=0.7,
                priority=10,
            ),
            
            "web_scraping": RetrievalPolicy(
                name="web_scraping",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["scraper", "scrape", "extraire", "extract",
                         "url", "lien", "page web", "web page",
                         "annonce", "job posting", "offre"],
                regex_patterns=[r"(scraper?|extraire|extract)\s+(?:une|an|a)?\s*(?:annonce|offre|page|url|lien)",
                               r"(récupérer|get|fetch)\s+(?:le|la|les)?\s*(?:contenu|content)\s+(?:de|from)?\s*(?:une|an|a)?\s*(?:url|lien)"],
                collection="workflow_memory",
                metadata_filters={"workflow_name": {"$contains": "scrap"}},
                limit=5,
                confidence_threshold=0.75,
                priority=9,
            ),
            
            # ========================================================================
            # RECRUITER & INTERACTION POLICIES
            # ========================================================================
            
            "recruiter_info": RetrievalPolicy(
                name="recruiter_info",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["recruteur", "recruiter", "contact", "entreprise", "company",
                         "suivi", "follow up", "relance", "follow-up",
                         "interview", "entretien"],
                collection="recruiter_memory",
                limit=5,
                confidence_threshold=0.75,
                priority=8,
            ),
            
            # ========================================================================
            # INFRA & DOCUMENTATION POLICIES
            # ========================================================================
            
            "infra_documentation": RetrievalPolicy(
                name="infra_documentation",
                policy_type=PolicyType.KEYWORD_BASED,
                keywords=["comment ça marche", "how it works", "configuration", "setup",
                         "installer", "install", "démarrer", "start",
                         "problème", "problem", "erreur", "error",
                         "aide", "help", "documentation", "doc"],
                collection="infra_memory",
                limit=5,
                confidence_threshold=0.7,
                priority=7,
            ),
            
            # ========================================================================
            # GENERAL CONTEXT POLICIES
            # ========================================================================
            
            "conversation_context": RetrievalPolicy(
                name="conversation_context",
                policy_type=PolicyType.CONTEXTUAL,
                requires_context=True,
                context_conditions={"has_previous_turns": True},
                collection="conversation_memory",
                limit=10,
                confidence_threshold=0.6,
                priority=5,
            ),
        }
    
    def get_policies_for_input(
        self, 
        user_input: str, 
        intent: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[RetrievalPolicy]:
        """
        Get all policies that match the current input and context.
        
        Args:
            user_input: The raw user input text
            intent: The extracted intent (if available)
            context: Additional context (conversation state, etc.)
            
        Returns:
            List of matching RetrievalPolicy objects, sorted by priority
        """
        matching_policies = []
        
        for policy_name, policy in self.policies.items():
            if policy.matches(user_input, intent, context):
                matching_policies.append(policy)
        
        # Sort by priority (descending)
        return sorted(matching_policies, key=lambda p: p.priority, reverse=True)
    
    def should_retrieve(
        self,
        user_input: str,
        intent: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Determine if we should retrieve memory for this input.
        
        Args:
            user_input: The raw user input text
            intent: The extracted intent (if available)
            context: Additional context
            
        Returns:
            True if at least one policy matches
        """
        policies = self.get_policies_for_input(user_input, intent, context)
        return len(policies) > 0
    
    def get_retrieval_plan(
        self,
        user_input: str,
        user_id: str,
        intent: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a complete retrieval plan for the given input.
        
        Args:
            user_input: The raw user input text
            user_id: The user ID for personalization
            intent: The extracted intent (if available)
            context: Additional context
            
        Returns:
            List of retrieval operations to perform, each containing:
            - collection: The collection to query
            - params: Retrieval parameters
            - policy: The policy that triggered this retrieval
        """
        policies = self.get_policies_for_input(user_input, intent, context)
        retrieval_plan = []
        
        for policy in policies:
            retrieval_plan.append({
                "policy": policy.name,
                "collection": policy.collection,
                "params": policy.get_retrieval_params(user_id),
                "priority": policy.priority,
            })
        
        return retrieval_plan
    
    def extract_intent(self, user_input: str) -> str:
        """
        Extract the primary intent from user input.
        
        This is a simple implementation - can be replaced with a proper
        intent classification model.
        
        Args:
            user_input: The raw user input text
            
        Returns:
            The extracted intent string
        """
        # Define intent patterns
        intent_patterns = [
            # Language intents
            ("language_preference", ["langue", "language", "parlons", "français", "english"]),
            
            # CV/Profile intents
            ("cv_generation", ["cv", "curriculum", "resume", "profil", "profile"]),
            ("cv_review", ["revue cv", "review cv", "améliorer cv", "improve cv"]),
            
            # Job search intents
            ("job_search", ["trouver job", "find job", "recherche emploi", "job search"]),
            ("job_application", ["postuler", "apply", "candidature", "application"]),
            ("job_match", ["correspond", "match", "fit", "compatible"]),
            
            # ATS intents
            ("ats_optimization", ["ats", "applicant tracking", "optimiser", "score ats"]),
            ("ats_keywords", ["mots-clés", "keywords", "ats keywords"]),
            
            # Workflow intents
            ("n8n_workflow", ["n8n", "workflow", "automatiser", "automate"]),
            ("web_scraping", ["scraper", "scrape", "extraire", "url"]),
            
            # Recruiter intents
            ("recruiter_info", ["recruteur", "recruiter", "contact", "entreprise"]),
            
            # General intents
            ("general_query", ["comment", "how", "quoi", "what", "pourquoi", "why"]),
            ("help", ["aide", "help", "?"]),
        ]
        
        input_lower = user_input.lower()
        
        for intent_name, keywords in intent_patterns:
            for keyword in keywords:
                if keyword.lower() in input_lower:
                    return intent_name
        
        # Default intent
        return "general_query"
    
    def add_policy(self, policy: RetrievalPolicy) -> None:
        """Add a new policy to the engine"""
        self.policies[policy.name] = policy
    
    def remove_policy(self, policy_name: str) -> None:
        """Remove a policy from the engine"""
        if policy_name in self.policies:
            del self.policies[policy_name]
