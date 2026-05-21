#!/usr/bin/env python3
# Test Script for Telegram Bot Integration
# ========================================
# Vérifie que le service Telegram peut se connecter à l'API Telegram
# et que toutes les dépendances sont installées

import sys
from pathlib import Path

# Ajouter le répertoire tool_gateway au path
tool_gateway_path = str(Path(__file__).parent.parent)
if tool_gateway_path not in sys.path:
    sys.path.insert(0, tool_gateway_path)

def test_imports():
    """Teste que toutes les dépendances peuvent être importées."""
    print("🧪 Testing imports...")
    
    try:
        from telegram import Update, Bot, Message
        print("  ✅ telegram")
    except ImportError as e:
        print(f"  ❌ telegram: {e}")
        return False
    
    try:
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
        print("  ✅ telegram.ext")
    except ImportError as e:
        print(f"  ❌ telegram.ext: {e}")
        return False
    
    try:
        import requests
        print("  ✅ requests")
    except ImportError as e:
        print(f"  ❌ requests: {e}")
        return False
    
    try:
        from tool_gateway.services.telegram_service import TelegramService
        print("  ✅ telegram_service")
    except ImportError as e:
        print(f"  ❌ telegram_service: {e}")
        return False
    
    try:
        from tool_gateway.config.telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_NAME
        print("  ✅ telegram_config")
    except ImportError as e:
        print(f"  ❌ telegram_config: {e}")
        return False
    
    return True


def test_bot_initialization():
    """Teste que le bot peut être initialisé."""
    print("\n🤖 Testing bot initialization...")
    
    try:
        import asyncio
        from telegram import Bot
        from tool_gateway.config.telegram_config import TELEGRAM_BOT_TOKEN
        
        async def test_bot():
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            # Tester la connexion
            me = await bot.get_me()
            return me
        
        # Exécuter la coroutine
        me = asyncio.run(test_bot())
        print(f"  ✅ Bot connected: {me.username} (ID: {me.id})")
        
        return True
    except Exception as e:
        print(f"  ❌ Bot initialization failed: {e}")
        return False


def test_api_connections():
    """Teste les connexions aux APIs GOOSE."""
    print("\n🔌 Testing API connections...")
    
    apis = [
        ("FastAPI Gateway", "http://localhost:8044/health"),
        ("Jobs API", "http://localhost:8044/jobs"),
        ("Memory API", "http://localhost:8044/memory/collections"),
    ]
    
    all_ok = True
    for name, url in apis:
        try:
            import requests
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {name} ({url})")
            else:
                print(f"  ⚠️  {name} returned {response.status_code}")
                all_ok = False
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            all_ok = False
    
    return all_ok


def test_telegram_service():
    """Teste le service Telegram sans démarrer le polling."""
    print("\n📡 Testing TelegramService...")
    
    try:
        from tool_gateway.services.telegram_service import TelegramService
        
        # Créer le service mais ne pas démarrer le polling
        service = TelegramService()
        print(f"  ✅ TelegramService instantiated")
        
        # Vérifier les attributs
        assert hasattr(service, 'token'), "Missing token attribute"
        assert hasattr(service, 'start'), "Missing start method"
        assert hasattr(service, '_command_start'), "Missing _command_start method"
        assert hasattr(service, '_command_jobs'), "Missing _command_jobs method"
        assert hasattr(service, '_command_memory'), "Missing _command_memory method"
        assert hasattr(service, '_command_ats'), "Missing _command_ats method"
        assert hasattr(service, '_command_cv'), "Missing _command_cv method"
        assert hasattr(service, '_command_stats'), "Missing _command_stats method"
        
        print(f"  ✅ All methods present")
        return True
    except Exception as e:
        print(f"  ❌ TelegramService test failed: {e}")
        return False


def main():
    """Exécute tous les tests."""
    print("=" * 60)
    print("GOOSE Telegram Bot - Integration Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Bot Initialization
    results.append(("Bot Initialization", test_bot_initialization()))
    
    # Test 3: API Connections
    results.append(("API Connections", test_api_connections()))
    
    # Test 4: Telegram Service
    results.append(("Telegram Service", test_telegram_service()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("RESUME DES TESTS")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("=" * 60)
    if all_passed:
        print("✅ TOUS LES TESTS ONT REUSSI !")
        print("\nVous pouvez démarrer le bot avec :")
        print("  python scripts/telegram_bot.py")
        print("\nOu en arrière-plan :")
        print("  python scripts/telegram_bot.py --daemon")
        return 0
    else:
        print("❌ CERTAINS TESTS ONT ECHOUE")
        return 1


if __name__ == "__main__":
    sys.exit(main())
