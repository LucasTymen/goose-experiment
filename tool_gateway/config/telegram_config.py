# Telegram Bot Configuration for GOOSE
# ========================================

# Token du bot (à garder SECRET)
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# Nom du bot
TELEGRAM_BOT_NAME = "RG4YZClawRG4YZ_bot"

# ID du bot
TELEGRAM_BOT_ID = 2025051518

# Pairing code (pour OpenClaw)
TELEGRAM_PAIRING_CODE = "YOUR_PAIRING_CODE_HERE"

# Configuration du polling
TELEGRAM_POLL_INTERVAL = 1.0  # secondes
TELEGRAM_TIMEOUT = 10  # secondes
TELEGRAM_DROP_PENDING = True

# Chat IDs autorisés (optionnel, pour restreindre l'accès)
# Si vide, tous les chats sont autorisés
ALLOWED_CHAT_IDS = []

# Commandes activées
ENABLED_COMMANDS = [
    "start",
    "help", 
    "ping",
    "jobs",
    "memory",
    "ats",
    "cv",
    "stats"
]

# Messages
WELCOME_MESSAGE = """
🪿 Bienvenue sur GOOSE AI Job Application Workbench!

Utilisez /help pour voir toutes les commandes disponibles.
"""

ERROR_MESSAGE = "❌ Une erreur est survenue. Veuillez réessayer plus tard."

# API Configuration
GOOSE_API_URL = "http://localhost:8044"
GOOSE_API_TIMEOUT = 10  # secondes

# Logging
TELEGRAM_LOG_FILE = "/home/lucas/GOOSE/tool_gateway/logs/telegram_bot.log"
TELEGRAM_LOG_LEVEL = "INFO"
