# Makefile GOOSE - Guide d'utilisation

Ce document explique comment utiliser le Makefile pour gérer tous les composants de GOOSE.

## 📋 Composants gérés

| Service | Port | Commande de démarrage | Commande d'arrêt |
|---------|------|----------------------|------------------|
| Ollama | 11434 | `make start-ollama` | `make stop-ollama` |
| Qdrant | 6334 | `make start-qdrant` | `make stop-qdrant` |
| PostgreSQL | 5434 | `make start-postgres` | `make stop-postgres` |
| N8N | 5684 | `make start-n8n` | `make stop-n8n` |
| GOOSE (Streamlit) | 8501 | `make start-goose` | `make stop-goose` |

---

## 🚀 Commandes principales

### Démarrer tout
```bash
make start
```
Démarre tous les services dans l'ordre: Ollama → Qdrant → PostgreSQL → N8N → GOOSE

### Arrêter tout
```bash
make stop
```
Arrête tous les services dans l'ordre inverse: GOOSE → N8N → PostgreSQL → Qdrant → Ollama

### Redémarrer tout
```bash
make restart
```
Équivalent à `make stop && make start`

### Vérifier l'état
```bash
make status
```
Affiche l'état de chaque service avec son PID et son port.

Exemple de sortie:
```
============================================================
  État des services GOOSE
============================================================
  ✅ Ollama: EN COURS (PID: 619, port 11434)
  ✅ Qdrant: EN COURS (PID: 4033, port 6334)
  ✅ PostgreSQL: EN COURS (port 5434)
  ✅ N8N: EN COURS (port 5684)
  ❌ GOOSE: ARRÊTÉ
============================================================
```

### Vérifier la santé (Health Check)
```bash
make health-check
```
Vérifie que chaque service répond correctement sur son endpoint HTTP.

Exemple de sortie:
```
============================================================
  Vérification de santé des services
============================================================
Ollama:
  ✅ OK
Qdrant:
  ✅ OK
PostgreSQL:
  ✅ OK
N8N:
  ✅ OK
GOOSE:
  ❌ INDISPONIBLE
============================================================
```

---

## 🎯 Commandes par service

### Ollama (Embeddings et LLM)
```bash
# Démarrer
make start-ollama

# Arrêter
make stop-ollama

# Vérifier l'état
make status-ollama
```

**Note:** Ollama doit être installé (`ollama serve`). Si non trouvé, le Makefile affiche une erreur avec des suggestions.

### Qdrant (Vector Database)
```bash
# Démarrer
make start-qdrant

# Arrêter
make stop-qdrant

# Vérifier l'état
make status-qdrant
```

**Note:** Qdrant peut être démarré via binaire local ou Docker. Le Makefile essaie les deux méthodes.

### PostgreSQL (Audit Logging)
```bash
# Démarrer
make start-postgres

# Arrêter
make stop-postgres

# Vérifier l'état
make status-postgres
```

**Note:** PostgreSQL peut être démarré via `pg_ctl`, `systemctl`, ou Docker.

### N8N (Workflow Automation)
```bash
# Démarrer
make start-n8n

# Arrêter
make stop-n8n

# Vérifier l'état
make status-n8n
```

**Note:** N8N nécessite une API key pour les requêtes. Le service démarre mais les workflows nécessitent une configuration supplémentaire.

### GOOSE Application (Streamlit)
```bash
# Démarrer
make start-goose

# ArrêteR
make stop-goose

# Vérifier l'état
make status-goose
```

**Note:** GOOSE nécessite que `app.py` existe dans le répertoire `/home/lucas/GOOSE`.

---

## 🧹 Nettoyage

### Nettoyer les fichiers temporaires
```bash
make clean
```
- Arrête tous les services
- Supprime les répertoires de données (qdrant_data, postgres_data)
- Supprime les fichiers de log temporaires

### Aide
```bash
make help
```
Affiche toutes les commandes disponibles.

---

## 🛠️ Configuration

Le Makefile utilise des variables que vous pouvez surcharger :

```bash
# Démarrer avec des ports personnalisés
make start OLLAMA_PORT=11435 QDRANT_PORT=6335

# Démarrer avec un binaire Qdrant personnalisé
make start QDRANT_BIN=/chemin/vers/qdrant
```

### Variables configurables

| Variable | Valeur par défaut | Description |
|----------|-------------------|-------------|
| `OLLAMA_PORT` | 11434 | Port Ollama |
| `QDRANT_PORT` | 6334 | Port Qdrant |
| `POSTGRES_PORT` | 5434 | Port PostgreSQL |
| `N8N_PORT` | 5684 | Port N8N |
| `GOOSE_PORT` | 8501 | Port application GOOSE |
| `OLLAMA_BIN` | ollama | Binaire Ollama |
| `QDRANT_BIN` | qdrant | Binaire Qdrant |
| `N8N_BIN` | n8n | Binaire N8N |
| `QDRANT_DATA` | ./qdrant_data | Répertoire données Qdrant |
| `POSTGRES_DATA` | ./postgres_data | Répertoire données PostgreSQL |

---

## 🐳 Utilisation avec Docker

Si vous préférez utiliser Docker, utilisez les cibles Docker :

```bash
# Démarrer tous les services avec Docker
make start-docker

# Arrêter tous les services Docker
make stop-docker
```

**Note:** Les cibles Docker tentent de démarrer des conteneurs avec les configurations par défaut.

---

## ⚠️ Dépannage

### "Command not found"
Si vous voyez cette erreur, le binaire n'est pas dans votre PATH. Solutions :

1. **Ollama**: Installez-le via [ollama.ai](https://ollama.ai)
2. **Qdrant**: Utilisez Docker: `docker run -p 6334:6334 qdrant/qdrant`
3. **PostgreSQL**: Utilisez Docker: `docker run -p 5434:5432 -e POSTGRES_PASSWORD=goosepass postgres`
4. **N8N**: Utilisez Docker: `docker run -p 5684:5684 n8nio/n8n`

### "Port already in use"
Un autre service utilise déjà le port. Solutions :

```bash
# Trouver le processus utilisant le port
sudo lsof -i :11434

# Tuer le processus
kill -9 <PID>
```

### "Permission denied"
Certaines commandes nécessitent sudo. Vous pouvez :

1. Exécuter `sudo make start`
2. Configurer sudo pour ne pas demander de mot de passe pour ces commandes
3. Démarrer les services manuellement avec sudo

---

## 📊 Vérification rapide

Pour vérifier que tout fonctionne :

```bash
# Démarrer tous les services
make start

# Vérifier l'état
make status

# Vérifier la santé
make health-check

# Tester l'application
demo_basic.py
```

---

## 📝 Notes

- Le Makefile gère les erreurs de manière gracieuse et affiche des suggestions si un service échoue à démarrer
- Les logs des services sont redirigés vers `/tmp/` (ollama.log, qdrant.log, n8n.log, goose.log)
- Les services déjà en cours ne sont pas redémarrés (detection automatique)
- L'ordre de démarrage est optimisé pour les dépendances (Ollama et Qdrant avant GOOSE)

---

## 🔗 Liens utiles

- [Ollama Documentation](https://github.com/jmorganca/ollama)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [N8N Documentation](https://docs.n8n.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
