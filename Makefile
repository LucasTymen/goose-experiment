# Makefile pour GOOSE - Démarrage de tous les composants
# ==============================================================
# Ce Makefile permet de démarrer/arrêter tous les services nécessaires
# pour le projet GOOSE
#
# Utilisation:
#   make start       - Démarre tous les services
#   make stop        - Arrête tous les services
#   make status      - Vérifie l'état de tous les services
#   make help        - Affiche l'aide

# ==============================================================
# Configuration
# ==============================================================

# Ports par défaut
OLLAMA_PORT := 11434
QDRANT_PORT := 6334
POSTGRES_PORT := 5434
N8N_PORT := 5684
GOOSE_PORT := 8501

# Chemins (à adapter selon votre installation)
OLLAMA_BIN := ollama
QDRANT_BIN ?= qdrant
N8N_BIN ?= n8n

# Répertoires de données
QDRANT_DATA := ./qdrant_data
POSTGRES_DATA := ./postgres_data

# Couleurs pour l'affichage
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# ==============================================================
# Cibles principales
# ==============================================================

.PHONY: start
start: start-ollama start-qdrant start-postgres start-n8n start-goose
	@echo ""
	@echo "============================================================"
	@echo "  Tous les services devraient être démarrés"
	@echo "  Vérifiez avec: make status"
	@echo "============================================================"

.PHONY: stop
stop: stop-goose stop-n8n stop-postgres stop-qdrant stop-ollama
	@echo ""
	@echo "============================================================"
	@echo "  Tous les services devraient être arrêtés"
	@echo "============================================================"

.PHONY: restart
restart: stop start

.PHONY: status
status:
	@echo ""
	@echo "============================================================"
	@echo "  État des services GOOSE"
	@echo "============================================================"
	@make status-ollama 2>/dev/null
	@make status-qdrant 2>/dev/null
	@make status-postgres 2>/dev/null
	@make status-n8n 2>/dev/null
	@make status-goose 2>/dev/null
	@echo "============================================================"

.PHONY: help
help:
	@echo ""
	@echo "Commandes disponibles pour GOOSE:"
	@echo ""
	@echo "  Démarrage/Arrêt:"
	@echo "    make start   - Démarre tous les services"
	@echo "    make stop    - Arrête tous les services"
	@echo "    make restart - Redémarre tous les services"
	@echo ""
	@echo "  Vérification:"
	@echo "    make status - Affiche l'état de tous les services"
	@echo ""
	@echo "  Services individuels:"
	@echo "    make start-ollama     - Démarre Ollama"
	@echo "    make stop-ollama      - Arrête Ollama"
	@echo "    make start-qdrant     - Démarre Qdrant"
	@echo "    make stop-qdrant      - Arrête Qdrant"
	@echo "    make start-postgres   - Démarre PostgreSQL"
	@echo "    make stop-postgres    - Arrête PostgreSQL"
	@echo "    make start-n8n        - Démarre N8N"
	@echo "    make stop-n8n         - Arrête N8N"
	@echo "    make start-goose      - Démarre l'application GOOSE"
	@echo "    make stop-goose       - Arrête l'application GOOSE"
	@echo ""

# ==============================================================
# Ollama
# ==============================================================

.PHONY: start-ollama
start-ollama:
	@echo "Démarrage de Ollama sur port $(OLLAMA_PORT)..."
	@if pgrep -f "$(OLLAMA_BIN) serve" > /dev/null 2>&1; then \
		echo "  Ollama est déjà en cours d'exécution"; \
	else \
		$(OLLAMA_BIN) serve > /tmp/ollama.log 2>&1 &
		sleep 3
		if ! pgrep -f "$(OLLAMA_BIN) serve" > /dev/null 2>&1; then \
			echo "  ❌ Échec du démarrage de Ollama"; \
			echo "     Essayez: ollama serve"; \
			exit 1; \
		fi
		echo "  ✅ Ollama démarré"
	fi

.PHONY: stop-ollama
stop-ollama:
	@echo "Arrêt de Ollama..."
	@pkill -f "$(OLLAMA_BIN) serve" 2>/dev/null || true
	@sleep 2
	@if pgrep -f "$(OLLAMA_BIN) serve" > /dev/null 2>&1; then \
		echo "  ❌ Ollama n'a pas pu être arrêté"; \
		echo "     Essayez: pkill -9 -f ollama"; \
	else \
		echo "  ✅ Ollama arrêté"
	fi

.PHONY: status-ollama
status-ollama:
	@if pgrep -f "$(OLLAMA_BIN) serve" > /dev/null 2>&1; then \
		PID=$$(pgrep -f "$(OLLAMA_BIN) serve" | head -1); \
		echo "  ✅ Ollama: EN COURS (PID: $$PID, port $(OLLAMA_PORT))"; \
	else \
		echo "  ❌ Ollama: ARRÊTÉ"; \
	fi

# ==============================================================
# Qdrant
# ==============================================================

.PHONY: start-qdrant
start-qdrant:
	@echo "Démarrage de Qdrant sur port $(QDRANT_PORT)..."
	@if pgrep -x "$(QDRANT_BIN)" > /dev/null 2>&1; then \
		echo "  Qdrant est déjà en cours d'exécution"; \
	else \
		mkdir -p $(QDRANT_DATA)
		$(QDRANT_BIN) --data-dir $(QDRANT_DATA) > /tmp/qdrant.log 2>&1 &
		sleep 3
		if ! pgrep -x "$(QDRANT_BIN)" > /dev/null 2>&1; then \
			echo "  ❌ Échec du démarrage de Qdrant"; \
			echo "     Essayez: docker run -p 6334:6334 qdrant/qdrant"; \
			exit 1; \
		fi
		echo "  ✅ Qdrant démarré"
	fi

.PHONY: stop-qdrant
stop-qdrant:
	@echo "Arrêt de Qdrant..."
	@pkill -x "$(QDRANT_BIN)" 2>/dev/null || true
	@sleep 2
	@if pgrep -x "$(QDRANT_BIN)" > /dev/null 2>&1; then \
		echo "  ❌ Qdrant n'a pas pu être arrêté"; \
		echo "     Essayez: pkill -9 qdrant"; \
	else \
		echo "  ✅ Qdrant arrêté"
	fi

.PHONY: status-qdrant
status-qdrant:
	@if pgrep -x "$(QDRANT_BIN)" > /dev/null 2>&1; then \
		PID=$$(pgrep -x "$(QDRANT_BIN)" | head -1); \
		echo "  ✅ Qdrant: EN COURS (PID: $$PID, port $(QDRANT_PORT))"; \
	else \
		echo "  ❌ Qdrant: ARRÊTÉ"; \
	fi

# ==============================================================
# PostgreSQL
# ==============================================================

.PHONY: start-postgres
start-postgres:
	@echo "Démarrage de PostgreSQL sur port $(POSTGRES_PORT)..."
	@if pgrep -x "postgres" > /dev/null 2>&1; then \
		echo "  PostgreSQL est déjà en cours d'exécution"; \
	else \
		mkdir -p $(POSTGRES_DATA)
		@if command -v pg_ctl > /dev/null 2>&1; then \
			initdb -D $(POSTGRES_DATA) 2>/dev/null || true
			pg_ctl -D $(POSTGRES_DATA) -l $(POSTGRES_DATA)/postgres.log start 2>/dev/null || true
			sleep 3
		else \
			@if command -v systemctl > /dev/null 2>&1; then \
				sudo systemctl start postgresql@16-main 2>/dev/null || sudo systemctl start postgresql 2>/dev/null || true
				sleep 3
			else \
				echo "  ❌ Impossible de démarrer PostgreSQL"; \
				echo "     Essayez: docker run -p 5434:5432 -e POSTGRES_PASSWORD=goosepass postgres"; \
				exit 1; \
			fi
		fi
		if ! pgrep -x "postgres" > /dev/null 2>&1; then \
			echo "  ❌ Échec du démarrage de PostgreSQL"; \
			exit 1; \
		fi
		echo "  ✅ PostgreSQL démarré"
	fi

.PHONY: stop-postgres
stop-postgres:
	@echo "Arrêt de PostgreSQL..."
	@if command -v pg_ctl > /dev/null 2>&1; then \
		pg_ctl -D $(POSTGRES_DATA) stop 2>/dev/null || true
	else \
		@if command -v systemctl > /dev/null 2>&1; then \
			sudo systemctl stop postgresql@16-main 2>/dev/null || sudo systemctl stop postgresql 2>/dev/null || true
		else \
			pkill -x "postgres" 2>/dev/null || true
		fi
	fi
	@sleep 2
	@if pgrep -x "postgres" > /dev/null 2>&1; then \
		echo "  ❌ PostgreSQL n'a pas pu être arrêté"; \
		echo "     Essayez: sudo systemctl stop postgresql"; \
	else \
		echo "  ✅ PostgreSQL arrêté"
	fi

.PHONY: status-postgres
status-postgres:
	@if PGPASSWORD=goosepass pg_isready -h localhost -p $(POSTGRES_PORT) -U goose -d goose_ai > /dev/null 2>&1; then \
		echo "  ✅ PostgreSQL: EN COURS (port $(POSTGRES_PORT))"; \
	else \
		echo "  ❌ PostgreSQL: ARRÊTÉ ou inaccessible"; \
	fi

# ==============================================================
# N8N
# ==============================================================

.PHONY: start-n8n
start-n8n:
	@echo "Démarrage de N8N sur port $(N8N_PORT)..."
	@if pgrep -f "node.*n8n" > /dev/null 2>&1; then \
		echo "  N8N est déjà en cours d'exécution"; \
	else \
		@if command -v n8n > /dev/null 2>&1; then \
			n8n > /tmp/n8n.log 2>&1 &
			sleep 5
		else \
			@if [ -f /usr/local/bin/n8n ]; then \
				node /usr/local/bin/n8n > /tmp/n8n.log 2>&1 &
				sleep 5
			else \
				echo "  ❌ Impossible de démarrer N8N"; \
				echo "     Essayez: docker run -p 5684:5684 n8nio/n8n"; \
				exit 1; \
			fi
		fi
		if ! pgrep -f "node.*n8n" > /dev/null 2>&1; then \
			echo "  ❌ Échec du démarrage de N8N"; \
			exit 1; \
		fi
		echo "  ✅ N8N démarré"
	fi

.PHONY: stop-n8n
stop-n8n:
	@echo "Arrêt de N8N..."
	@pkill -f "node.*n8n" 2>/dev/null || true
	@sleep 2
	@if pgrep -f "node.*n8n" > /dev/null 2>&1; then \
		echo "  ❌ N8N n'a pas pu être arrêté"; \
		echo "     Essayez: pkill -9 -f n8n"; \
	else \
		echo "  ✅ N8N arrêté"
	fi

.PHONY: status-n8n
status-n8n:
	@if curl -s http://localhost:$(N8N_PORT)/healthz > /dev/null 2>&1; then \
		echo "  ✅ N8N: EN COURS (port $(N8N_PORT))"; \
	else \
		echo "  ❌ N8N: ARRÊTÉ ou inaccessible"; \
	fi

# ==============================================================
# GOOSE Application
# ==============================================================

.PHONY: start-goose
start-goose:
	@echo "Démarrage de l'application GOOSE sur port $(GOOSE_PORT)..."
	@if pgrep -f "streamlit run" > /dev/null 2>&1; then \
		echo "  GOOSE est déjà en cours d'exécution"; \
	else \
		cd /home/lucas/GOOSE && streamlit run app.py --server.port=$(GOOSE_PORT) > /tmp/goose.log 2>&1 &
		sleep 5
		if ! pgrep -f "streamlit run" > /dev/null 2>&1; then \
			echo "  ❌ Échec du démarrage de GOOSE"; \
			echo "     Vérifiez que app.py existe"; \
			exit 1; \
		fi
		echo "  ✅ GOOSE démarré"
	fi

.PHONY: stop-goose
stop-goose:
	@echo "Arrêt de l'application GOOSE..."
	@pkill -f "streamlit run" 2>/dev/null || true
	@sleep 2
	@if pgrep -f "streamlit run" > /dev/null 2>&1; then \
		echo "  ❌ GOOSE n'a pas pu être arrêté"; \
		echo "     Essayez: pkill -9 -f streamlit"; \
	else \
		echo "  ✅ GOOSE arrêté"
	fi

.PHONY: status-goose
status-goose:
	@if pgrep -f "streamlit run" > /dev/null 2>&1; then \
		echo "  ✅ GOOSE: EN COURS (port $(GOOSE_PORT))"; \
	else \
		echo "  ❌ GOOSE: ARRÊTÉ"; \
	fi

# ==============================================================
# Vérifications de santé (health checks)
# ==============================================================

.PHONY: health-check
health-check:
	@echo ""
	@echo "============================================================"
	@echo "  Vérification de santé des services"
	@echo "============================================================"
	@echo "Ollama:"
	@curl -s http://localhost:$(OLLAMA_PORT)/api/tags > /dev/null 2>&1 && echo "  ✅ OK" || echo "  ❌ INDISPONIBLE"
	@echo "Qdrant:"
	@curl -s http://localhost:$(QDRANT_PORT) > /dev/null 2>&1 && echo "  ✅ OK" || echo "  ❌ INDISPONIBLE"
	@echo "PostgreSQL:"
	@PGPASSWORD=goosepass pg_isready -h localhost -p $(POSTGRES_PORT) -U goose -d goose_ai > /dev/null 2>&1 && echo "  ✅ OK" || echo "  ❌ INDISPONIBLE"
	@echo "N8N:"
	@curl -s http://localhost:$(N8N_PORT)/healthz > /dev/null 2>&1 && echo "  ✅ OK" || echo "  ❌ INDISPONIBLE"
	@echo "GOOSE:"
	@curl -s http://localhost:$(GOOSE_PORT) > /dev/null 2>&1 && echo "  ✅ OK" || echo "  ❌ INDISPONIBLE"
	@echo "============================================================"

# ==============================================================
# Nettoyage
# ==============================================================

.PHONY: clean
clean: stop
	@echo ""
	@echo "Nettoyage des fichiers temporaires..."
	@rm -rf $(QDRANT_DATA) $(POSTGRES_DATA)
	@rm -f /tmp/ollama.log /tmp/qdrant.log /tmp/n8n.log /tmp/goose.log
	@echo "  ✅ Nettoyage terminé"
