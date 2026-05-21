# GOOSE Telegram Bot Integration

## 📋 Overview

Ce dossier contient les scripts pour intégrer GOOSE avec Telegram. Le bot **RG4YZClawRG4YZ_bot** permet de contrôler GOOSE directement depuis Telegram.

## 🤖 Bot Information

- **Bot Name**: RG4YZClawRG4YZ_bot
- **Bot ID**: 2025051518
- **Bot URL**: https://t.me/RG4YZClawRG4YZ_bot
- **Pairing Code**: YOUR_PAIRING_CODE_HERE (pour OpenClaw)

## ⚙️ Configuration

### Token de Bot

Le token est stocké dans `tool_gateway/config/telegram_config.py` et `tool_gateway/services/telegram_service.py`:

```python
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
```

> ⚠️ **IMPORTANT**: Si ce token ne fonctionne pas, vous devez en obtenir un nouveau depuis [@BotFather](https://t.me/BotFather) sur Telegram.

### Comment obtenir un nouveau token

1. Ouvrez Telegram et recherchez **@BotFather**
2. Envoyez `/newbot`
3. Suivez les instructions pour créer un nouveau bot
4. Copiez le token HTTP API qui vous est donné
5. Mettez à jour le token dans:
   - `tool_gateway/config/telegram_config.py`
   - `tool_gateway/services/telegram_service.py`

## 🚀 Démarrage du Bot

### Méthode 1: Exécution directe (foreground)

```bash
cd GOOSE/tool_gateway
python3 scripts/telegram_bot.py
```

Le bot démarrera et affichera les logs dans la console. Appuyez sur `Ctrl+C` pour arrêter.

### Méthode 2: Exécution en arrière-plan (daemon)

```bash
cd GOOSE/tool_gateway
python3 scripts/telegram_bot.py --daemon
```

Le bot tournera en arrière-plan. Les logs seront écrits dans `logs/telegram_bot.log`.

### Méthode 3: Mode test

```bash
cd GOOSE/tool_gateway
python3 scripts/telegram_bot.py --test
```

Vérifie la configuration sans démarrer le polling.

## 📚 Commandes Disponibles

### Commandes de Base

| Commande | Description |
|----------|-------------|
| `/start` | Afficher le message de bienvenue |
| `/help` | Aide détaillée avec toutes les commandes |
| `/ping` | Tester la connexion au bot |

### Gestion des Jobs

| Commande | Description | Exemple |
|----------|-------------|---------|
| `/jobs` | Lister tous les jobs | `/jobs` |
| `/jobs <n>` | Lister les n derniers jobs | `/jobs 5` |

### Mémoire Sémantique

| Commande | Description | Exemple |
|----------|-------------|---------|
| `/memory <requête>` | Rechercher dans la mémoire | `/memory Python AI` |
| `/memory <requête> <collection>` | Rechercher dans une collection spécifique | `/memory AI jobs_memory` |

**Collections disponibles:**
- `candidate_memory` (par défaut)
- `jobs_memory`
- `ats_keywords_memory`
- `prompts_memory`
- `workflow_memory`

### ATS Scoring

| Commande | Description | Exemple |
|----------|-------------|---------|
| `/ats <description> <skills>` | Calculer un score ATS | `/ats "Senior Python" Python,AI,Docker` |

**Format:** La description et les skills séparées par un espace. Les skills doivent être séparées par des virgules.

### Génération de CV

| Commande | Description | Exemple |
|----------|-------------|---------|
| `/cv <candidate> <role> <company>` | Générer un CV | `/cv "Jean Dupont" "Dev Python" "Google"` |

### Statistiques

| Commande | Description |
|----------|-------------|
| `/stats` | Afficher les statistiques du système |

## 💬 Recherche Naturelle

Vous pouvez envoyer des messages texte normaux pour :

- **Rechercher des jobs**: "Python developer jobs", "AI engineer positions"
- **Rechercher dans la mémoire**: "mon expérience en machine learning", "mes compétences en Python"

Le bot essaiera d'interpréter votre message et de trouver les informations pertinentes.

## 📦 Dépendances

Assurez-vous que les packages suivants sont installés :

```bash
pip install python-telegram-bot>=20.0 requests
```

## 🔧 Intégration avec GOOSE

Le bot Telegram communique avec le **FastAPI Tool Gateway** (port 8044). Assurez-vous que :

- FastAPI est en cours d'exécution : `uvicorn tool_gateway.api.main:app --reload --port 8044`
- PostgreSQL est accessible (port 5434)
- Qdrant est accessible (port 6334)
- Ollama est accessible (port 11434)

## 🔒 Sécurité

- Ne partagez **JAMAIS** le token de votre bot
- Le token permet à quiconque de contrôler votre bot
- Stockez le token dans des variables d'environnement en production

## 📝 Variables d'Environnement (Optionnel)

Pour plus de sécurité, vous pouvez utiliser des variables d'environnement :

```bash
export TELEGRAM_BOT_TOKEN="votre_token_ici"
```

Puis modifiez `telegram_service.py` pour lire depuis la variable d'environnement :

```python
import os
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
```

## 🐛 Dépannage

### Le bot ne répond pas

1. Vérifiez que le script est en cours d'exécution
2. Vérifiez les logs dans `logs/telegram_bot.log`
3. Vérifiez que le token est correct
4. Vérifiez que le FastAPI Gateway est accessible

### Erreur "Not Found" (404)

Cela signifie que le token est invalide. Obtenez un nouveau token depuis @BotFather.

### Erreur de connexion à l'API GOOSE

Vérifiez que FastAPI est démarré et accessible sur `http://localhost:8044/health`

## 📊 Exemples d'Utilisation

### Exemple 1: Lister les jobs

```
Utilisateur: /jobs
Bot: 📋 Liste des 10 derniers jobs (Total: 6)

1. **Senior Python Engineer** @ TechCorp
   Score ATS: 30
   Skills: Python, AI, automation

2. **Test** @ Test
   Score ATS: 10
   Skills: Python
...
```

### Exemple 2: Recherche ATS

```
Utilisateur: /ats "Senior Python Engineer" Python,AI,Machine Learning
Bot: 🎯 Score ATS calculé

**Description :** Senior Python Engineer
**Skills :** Python, AI, Machine Learning
**Score :** 20/30 (66.7%)
```

### Exemple 3: Recherche naturelle

```
Utilisateur: Python developer
Bot: 🔍 Jobs correspondant à "Python developer"

1. **Senior Python Engineer** @ TechCorp
   Score: 30

2. **Python Developer** @ TestCompany
   Score: 25
```

## 🎯 Prochaines Étapes

- [x] Service Telegram créé
- [x] Script de démarrage créé
- [x] Configuration créée
- [ ] Tester avec un token valide
- [ ] Documenter les commandes
- [ ] Ajouter plus de fonctionnalités (notification, workflows)

---

**Documentation générée par GOOSE**
**Dernière mise à jour**: 2026-05-21
