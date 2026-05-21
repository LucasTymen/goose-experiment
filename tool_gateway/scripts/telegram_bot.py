#!/usr/bin/env python3
# GOOSE Telegram Bot
# ===================
# Script pour démarrer le bot Telegram en arrière-plan
# Utilisation : python telegram_bot.py [--daemon]

import sys
import os
import argparse
import logging
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tool_gateway.services.telegram_service import TelegramService, TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_NAME

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/home/lucas/GOOSE/tool_gateway/logs/telegram_bot.log')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description=f'Démarrer le bot Telegram {TELEGRAM_BOT_NAME}'
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Exécuter en arrière-plan (mode daemon)'
    )
    parser.add_argument(
        '--token',
        type=str,
        default=TELEGRAM_BOT_TOKEN,
        help='Token du bot Telegram (par défaut: variable TELEGRAM_BOT_TOKEN)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Mode test (ne pas démarrer le polling)'
    )
    
    args = parser.parse_args()
    
    if args.test:
        logger.info("Mode test activé. Vérification de la configuration...")
        from tool_gateway.services.telegram_service import get_telegram_service
        service = get_telegram_service()
        logger.info(f"✅ Service Telegram initialisé avec token: {args.token[:5]}...")
        logger.info(f"✅ Bot name: {TELEGRAM_BOT_NAME}")
        logger.info(f"✅ Bot ID: {service.bot.id if service.bot else 'N/A'}")
        return
    
    if args.daemon:
        logger.info("Démarrage en mode daemon...")
        # Double fork pour le daemon
        try:
            pid = os.fork()
            if pid > 0:
                # Parent exit
                sys.exit(0)
        except OSError as e:
            logger.error(f"Fork #1 échoué: {e}")
            sys.exit(1)
        
        # Décrocher du terminal
        os.chdir('/')
        os.setsid()
        os.umask(0)
        
        try:
            pid = os.fork()
            if pid > 0:
                # Parent exit
                sys.exit(0)
        except OSError as e:
            logger.error(f"Fork #2 échoué: {e}")
            sys.exit(1)
        
        # Rediriger les flux
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
    
    # Démarrer le bot
    logger.info(f"Démarrage du bot Telegram {TELEGRAM_BOT_NAME}...")
    logger.info(f"Token: {args.token[:5]}...{args.token[-5:]}")
    
    try:
        service = TelegramService(token=args.token)
        service.start()
    except KeyboardInterrupt:
        logger.info("Arrêt du bot (Ctrl+C)")
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
