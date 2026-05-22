"""
Prompt Augmenter for GOOSE Agent Runtime
=======================================

Augments LLM prompts with retrieved context and memory.
Handles prompt engineering for different use cases.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import re
import logging
from datetime import datetime

from .context_assembler import AssembledContext, MemoryContext
from .memory_taxonomy import MemoryType

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Template for generating prompts"""
    name: str
    system_prompt: str
    user_prompt: str
    memory_injection_point: str = "{memory_context}"
    
    def render(self, memory_context: str = "", user_input: str = "", **kwargs) -> Tuple[str, str]:
        """Render the full prompt"""
        system = self.system_prompt.format(
            memory_context=memory_context,
            **kwargs
        )
        user = self.user_prompt.format(
            user_input=user_input,
            **kwargs
        )
        return system, user


class PromptAugmenter:
    """
    Augments LLM prompts with memory context.
    
    Features:
    - Multiple prompt templates for different use cases
    - Memory context injection
    - Conversation history integration
    - Intent-specific prompting
    - Token-aware truncation
    """
    
    def __init__(self):
        # Define prompt templates
        self.templates = {
            "default": PromptTemplate(
                name="default",
                system_prompt="""
You are GOOSE, an advanced AI assistant specialized in job search, CV optimization, and career development.

You have access to the user's memory and preferences. Use them to provide personalized, context-aware responses.

{memory_context}

Guidelines:
- Always respond in the user's preferred language
- Use retrieved memories to personalize your responses
- Be concise and direct
- Provide actionable advice
- If no relevant memory is found, respond generically but helpfully
""",
                user_prompt="{user_input}"
            ),
            
            "language_preference": PromptTemplate(
                name="language_preference",
                system_prompt="""
You are GOOSE, an AI assistant that adapts to user preferences.

The user has expressed a language preference. Respond in that language.

User's language preference: {language}

{memory_context}

Guidelines:
- Respond ONLY in the user's preferred language
- Maintain a helpful and professional tone
- Acknowledge the language preference
- If language is not specified, respond in English
""",
                user_prompt="{user_input}"
            ),
            
            "cv_generation": PromptTemplate(
                name="cv_generation",
                system_prompt="""
You are GOOSE, an expert CV generator and career coach.

You have access to the user's profile, skills, and experience from memory.

{memory_context}

Guidelines:
- Generate a professional CV based on the user's profile
- Include all relevant skills and experience
- Optimize for ATS (Applicant Tracking Systems)
- Use standard CV format
- If information is missing, ask the user to provide it
""",
                user_prompt="Generate a CV for me. {user_input}"
            ),
            
            "job_match": PromptTemplate(
                name="job_match",
                system_prompt="""
You are GOOSE, a career matching expert.

You have access to the user's profile and job listings from memory.

{memory_context}

Guidelines:
- Match the user's skills and experience to relevant job listings
- Explain WHY each job is a good match
- Highlight missing skills or requirements
- Provide recommendations for improvement
- Be specific and actionable
""",
                user_prompt="{user_input}"
            ),
            
            "ats_optimization": PromptTemplate(
                name="ats_optimization",
                system_prompt="""
You are GOOSE, an ATS optimization specialist.

You have access to ATS best practices, keywords, and optimization patterns from memory.

{memory_context}

Guidelines:
- Provide specific, actionable ATS optimization advice
- Reference retrieved keywords and patterns
- Explain the reasoning behind each recommendation
- Tailor advice to the user's industry and role
- Focus on what will get past ATS filters
""",
                user_prompt="{user_input}"
            ),
            
            "web_scraping": PromptTemplate(
                name="web_scraping",
                system_prompt="""
You are GOOSE, an automation and web scraping assistant.

You can help create workflows to extract job postings from websites.

{memory_context}

Guidelines:
- Help the user create effective scraping workflows
- Focus on job-related data extraction
- Provide code examples for N8N workflows
- Explain what data should be extracted
- Warn about legal and ethical considerations
""",
                user_prompt="{user_input}"
            ),
            
            "conversation": PromptTemplate(
                name="conversation",
                system_prompt="""
You are GOOSE, a conversational AI with long-term memory.

Previous conversation context:
{conversation_history}

{memory_context}

Guidelines:
- Maintain consistency with previous responses
- Reference earlier parts of the conversation when relevant
- Use memory to provide context-aware responses
- Be natural and conversational
""",
                user_prompt="{user_input}"
            ),
            
            "minimal": PromptTemplate(
                name="minimal",
                system_prompt="{memory_context}",
                user_prompt="{user_input}"
            ),
        }
        
        # Default template
        self.default_template_name = "default"
        
        # Conversation history storage
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history_length = 10
    
    def augment(
        self,
        user_input: str,
        memory_context: Optional[AssembledContext] = None,
        intent: Optional[str] = None,
        template: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Augment a user input with memory context and generate system/user prompts.
        
        Args:
            user_input: The raw user input
            memory_context: Assembled context from retrieval
            intent: The extracted intent
            template: Template name to use (defaults based on intent)
            conversation_history: Optional conversation history
            **kwargs: Additional template variables
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Select template
        if template:
            selected_template = self.templates.get(template, self.templates[self.default_template_name])
        elif intent:
            selected_template = self._select_template_by_intent(intent)
        else:
            selected_template = self.templates[self.default_template_name]
        
        # Set default language if not provided
        kwargs.setdefault("language", "English")
        
        # Prepare memory context string
        memory_context_str = ""
        if memory_context and memory_context.memories:
            # Extract language preference if present (override default)
            language = self._extract_language_preference(memory_context)
            if language:
                kwargs["language"] = language
            
            memory_context_str = memory_context.to_string()
            
            # Truncate if too long
            if len(memory_context_str) > 4000:
                memory_context_str = memory_context_str[:4000] + "\n\n[... context truncated ...]"
        
        # Prepare conversation history
        if conversation_history:
            history_str = self._format_conversation_history(conversation_history)
            kwargs["conversation_history"] = history_str
        
        # Render prompts
        system_prompt, user_prompt = selected_template.render(
            memory_context=memory_context_str,
            user_input=user_input,
            **kwargs
        )
        
        return system_prompt, user_prompt
    
    def _select_template_by_intent(self, intent: str) -> PromptTemplate:
        """Select the best template based on intent"""
        intent_template_map = {
            "language_preference": "language_preference",
            "cv_generation": "cv_generation",
            "cv_review": "cv_generation",
            "job_search": "job_match",
            "job_application": "job_match",
            "job_match": "job_match",
            "ats_optimization": "ats_optimization",
            "ats_keywords": "ats_optimization",
            "n8n_workflow": "web_scraping",
            "web_scraping": "web_scraping",
            "recruiter_info": "default",
            "help": "default",
        }
        
        template_name = intent_template_map.get(intent, self.default_template_name)
        return self.templates.get(template_name, self.templates[self.default_template_name])
    
    def _extract_language_preference(self, memory_context: AssembledContext) -> Optional[str]:
        """Extract language preference from memory context"""
        for memory in memory_context.memories:
            if memory.collection == "preferences_memory":
                pref_type = memory.metadata.get("preference_type", "")
                if pref_type.lower() == "language":
                    return memory.metadata.get("value")
        return None
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for prompt injection"""
        if not history:
            return ""
        
        lines = []
        for i, turn in enumerate(history[-self.max_history_length:], 1):
            role = turn.get("role", "user")
            content = turn.get("content", "")
            lines.append(f"Turn {i} ({role}): {content[:200]}")
        
        return "\n".join(lines[-self.max_history_length:])
    
    def extract_intent(self, user_input: str) -> str:
        """
        Extract the primary intent from user input.
        
        This uses a combination of keyword matching and pattern recognition.
        For more accuracy, this could be replaced with a proper intent classification model.
        
        Args:
            user_input: The raw user input text
            
        Returns:
            The extracted intent string
        """
        input_lower = user_input.lower()
        
        # Check for language preferences first
        language_patterns = [
            ("language_preference", ["parlons", "en français", "in english", "hablamos", 
                                  "auf deutsch", "langue", "language", "idioma", "sprache"])
        ]
        
        for intent, keywords in language_patterns:
            for keyword in keywords:
                if keyword.lower() in input_lower:
                    return intent
        
        # Check for CV/profile intents
        cv_patterns = [
            ("cv_generation", ["génère mon cv", "generate cv", "mon curriculum", 
                              "my resume", "créer cv", "create resume"]),
            ("cv_review", ["revue cv", "review cv", "améliorer cv", "improve cv",
                           "optimiser cv", "optimize cv"])
        ]
        
        for intent, keywords in cv_patterns:
            for keyword in keywords:
                if keyword.lower() in input_lower:
                    return intent
        
        # Check for job intents
        job_patterns = [
            ("job_search", ["trouver un job", "find a job", "recherche emploi", 
                            "job search", "chercher emploi"]),
            ("job_application", ["postuler", "apply", "candidature", "application",
                                 "candidater", "envoyer cv"]),
            ("job_match", ["quels jobs correspondent", "which jobs fit", 
                          "meilleur match", "best fit", "correspondance"])
        ]
        
        for intent, keywords in job_patterns:
            for keyword in keywords:
                if keyword.lower() in input_lower:
                    return intent
        
        # Check for ATS intents
        ats_patterns = [
            ("ats_optimization", ["ats", "applicant tracking", "optimiser", 
                                 "score ats", "passer les ats"]),
            ("ats_keywords", ["mots-clés", "keywords", "ats keywords", 
                              "cv keywords", "resume keywords"])
        ]
        
        for intent, keywords in ats_patterns:
            for keyword in keywords:
                if keyword.lower() in input_lower:
                    return intent
        
        # Check for workflow intents
        workflow_patterns = [
            ("n8n_workflow", ["n8n", "workflow", "automatiser", "automate"]),
            ("web_scraping", ["scraper", "scrape", "extraire", "extract",
                             "url", "lien", "site web", "annonce", "scrapping"])
        ]
        
        for intent, keywords in workflow_patterns:
            for keyword in keywords:
                if keyword.lower() in input_lower:
                    return intent
        
        # Check for recruiter intents
        recruiter_patterns = [
            ("recruiter_info", ["recruteur", "recruiter", "contact", 
                                "entreprise", "company", "suivi", "follow up"])
        ]
        
        for intent, keywords in recruiter_patterns:
            for keyword in keywords:
                if keyword.lower() in input_lower:
                    return intent
        
        # Default intents
        if any(word in input_lower for word in ["aide", "help", "?"]):
            return "help"
        
        return "general_query"
    
    def get_system_prompt(
        self,
        memory_context: Optional[AssembledContext] = None,
        intent: Optional[str] = None,
        template: Optional[str] = None,
        **kwargs
    ) -> str:
        """Get just the system prompt"""
        system, _ = self.augment(
            user_input="",
            memory_context=memory_context,
            intent=intent,
            template=template,
            **kwargs
        )
        return system
    
    def get_user_prompt(
        self,
        user_input: str,
        intent: Optional[str] = None,
        template: Optional[str] = None,
        **kwargs
    ) -> str:
        """Get just the user prompt"""
        _, user = self.augment(
            user_input=user_input,
            intent=intent,
            template=template,
            **kwargs
        )
        return user
    
    def add_template(self, template: PromptTemplate) -> None:
        """Add a new template"""
        self.templates[template.name] = template
    
    def remove_template(self, name: str) -> None:
        """Remove a template"""
        if name in self.templates:
            del self.templates[name]
    
    def list_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.templates.keys())
    
    def update_conversation_history(
        self,
        user_input: str,
        ai_response: str,
        intent: Optional[str] = None
    ) -> None:
        """Update the conversation history"""
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "intent": intent,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": ai_response,
            "intent": intent,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Trim history if too long
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]
    
    def clear_conversation_history(self) -> None:
        """Clear the conversation history"""
        self.conversation_history = []
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation"""
        if not self.conversation_history:
            return "No previous conversation"
        
        last_user = None
        for turn in reversed(self.conversation_history):
            if turn["role"] == "user":
                last_user = turn["content"][:200]
                break
        
        return f"Current conversation: {len(self.conversation_history) // 2} exchanges. Last user input: {last_user}"
