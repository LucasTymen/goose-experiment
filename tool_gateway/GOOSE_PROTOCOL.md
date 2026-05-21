# 📜 GOOSE AGENT PROTOCOL

**Version :** 1.0  
**Date :** 2026-05-21  
**Auteur :** Mistral Vibe (adapté de Claude Code Protocol)  
**Statut :** ACTIF

---

## 🎯 PRÉAMBULE

Goose est un **orchestrateur IA local persistant**, pas un simple chatbot.
Ce protocole garantit des **modifications déterministes, auditables et sans hallucination**.

**Principe fondamental :**
> "Ne jamais prétendre qu'une action est terminée sans preuve d'exécution."

---

## 🔄 PROTOCOLE EN 5 PHASES (+ AUDIT)

```
THINK    → Analyser le contexte et les contraintes
PLAN     → Définir les étapes techniques précises
CRITIQUE → Identifier et vérifier les risques
EXECUTE  → Exécuter avec modifications minimales (Unified Diff)
AUDIT    → Consigner dans PostgreSQL, Qdrant et GOOSE_GENESIS_LOG.md
```

---

## Phase 1: THINK (Context Budgeting)

### 📌 Principe
**Ne PAS donner tout le code.** Donner **l'arborescence** et laisser Goose choisir les fichiers à modifier.

### ✅ Bon
```bash
# Demande à Goose
find ~/GOOSE/tool_gateway -type f -name "*.py" | grep -E "(service|api)"
```
→ Goose identifie les 4-5 fichiers pertinents.

### ❌ À éviter
```bash
# Demande à éviter
"Voici tout mon codebase : [10 000 lignes de paste]"
```
→ Risque d'hallucination, de confusion, de tokens gaspillés.

### 📋 Checklist THINK
- [ ] Arborescence fournie (`tree`, `find`, `ls -R`)
- [ ] Objectif clair en 1 phrase
- [ ] Contexte minimal (dépendances, contraintes)
- [ ] Pas de code complet collé

---

## Phase 2: PLAN (Planification Technique)

### 📌 Principe
**Définir les étapes AVANT de coder.**
Chaque étape doit être **testable individuellement**.

### 📝 Template PLAN

```markdown
## [TÂCHE N°] : [Nom]

### Objectif
[1 phrase claire et précise]

### Contexte
[2-3 phrases max : pourquoi cette tâche ?]

### Fichiers cibles
- `path/to/file1.py` → [modification A]
- `path/to/file2.py` → [modification B]

### Dépendances
| Service | Statut | Vérification |
|---------|--------|--------------|
| PostgreSQL | ✅/❌ | `docker ps \| grep postgres` |
| Qdrant | ✅/❌ | `curl http://localhost:6334/collections` |
| Ollama | ✅/❌ | `curl http://localhost:11434/api/tags` |

### Étapes techniques
1. [Action 1] → Test : [commande]
2. [Action 2] → Test : [commande]
3. [Action 3] → Test : [commande]

### Tests attendus
- [ ] `curl -X POST ...` → `{"status": "ok"}`
- [ ] `docker exec postgres psql -c "SELECT * FROM audit_logs"` → [nombre entrées]
- [ ] `curl http://localhost:6334/collections` → [collections list]
```

### ✅ Bon exemple (Tâche 2)
```markdown
## Tâche 2 : Advanced Retrieval System

### Objectif
Implémenter recherche sémantique dans Qdrant via embeddings Ollama.

### Contexte
On a Qdrant et Ollama fonctionnels, mais pas de recherche. Il manque l'endpoint /memory/search.

### Fichiers cibles
- `tool_gateway/services/qdrant_service.py` → Ajouter `search_memory()`
- `tool_gateway/api/main.py` → Ajouter `/memory/search` + `SearchRequest`

### Dépendances
| Service | Statut | Vérification |
|---------|--------|--------------|
| PostgreSQL | ✅ | 5 collections existantes |
| Qdrant | ✅ | `curl localhost:6334/collections` |
| Ollama | ✅ | `nomic-embed-text` disponible |

### Étapes techniques
1. Ajouter `search_memory(collection, vector, limit)` dans qdrant_service.py
2. Ajouter modèle `SearchRequest` dans main.py
3. Ajouter endpoint `/memory/search` dans main.py
4. Redémarrer uvicorn
5. Tester avec requête sémantique

### Tests attendus
- [ ] POST /memory/search → results avec scores > 0.7
- [ ] Collection inexistante → ValueError
- [ ] Audit dans PostgreSQL → 1 entrée
```

---

## Phase 3: CRITIQUE (Vérification des Risques)

### 📌 Principe
**Anticiper les problèmes AVANT d'exécuter.**

### 🔍 Checklist CRITIQUE

#### 🛡️ Sécurité
- [ ] On est bien en **LAB** (pas en PROD) ?
- [ ] Backup PostgreSQL avant modification ? (`pg_dump`)
- [ ] Backup Qdrant ? (`client.create_snapshot()`)
- [ ] Ports libérés ? (`lsof -i :PORT`)

#### 📦 Dépendances
- [ ] Modules Python installés ? (`pip list`)
- [ ] Services Docker en cours ? (`docker ps`)
- [ ] Connexions DB fonctionnelles ?

#### 💾 Données
- [ ] Les données existantes seront-elles affectées ?
- [ ] Y a-t-il des migrations nécessaires ?
- [ ] Format des données compatible ?

#### ⚡ Performances
- [ ] Complexité algorithmique acceptable ?
- [ ] Pas de boucles infinies ?
- [ ] Timeout gérés ?

### ✅ Exemple CRITIQUE (avant Tâche 1)
```markdown
### ⚠️ CRITIQUE pour Tâche 1 (CV Generator)

| Risque | Impact | Vérification | Solution |
|--------|--------|--------------|----------|
| Dépendance manquante | ❌ | `pip list \| grep weasyprint` | `pip install weasyprint` |
| Données utilisateur manquantes | ❌ | `GET /memory/collections` | Stocker données d'abord |
| Template non trouvé | ❌ | `ls tool_gateway/templates/` | Créer dossier |
| Conflit de nom | ❌ | `grep -r "generate_cv" api/` | Renommer si nécessaire |
```

---

## Phase 4: EXECUTE (Unified Diff)

### 📌 Principe
**Modifications MINIMALES et PRÉCISES.**
Utiliser **uniquement** le format SEARCH/REPLACE.

### ✅ Format obligatoire

```python
# DANS main.py
<<<<<<< SEARCH
@app.post("/old-endpoint")
def old_function():
    return {"status": "old"}
=======
@app.post("/old-endpoint")
def old_function():
    return {"status": "old"}

@app.post("/new-endpoint")  # NOUVEAU
def new_function():
    # Logique minimale
    return {"status": "new"}
>>>>>>> REPLACE
```

### ❌ À ÉVITER ABSOLUMENT

```python
# ❌ NE JAMAIS FAIRE ÇA
# Réécrire tout le fichier main.py avec 200 lignes de code
# → Risque d'hallucination, de perte de code, de conflits

# ❌ NE JAMAIS FAIRE ÇA
# "Voici le fichier complet modifié : [200 lignes]"
# → Impossible à reviewer, risque d'erreurs
```

### 📝 Règles EXECUTE
1. **1 modification = 1 SEARCH/REPLACE block**
2. **Max 15 lignes par block** (sauf exception justifiée)
3. **Toujours inclure le contexte** (3-5 lignes avant/après)
4. **Ne PAS modifier plusieurs fichiers en même temps** (sauf si dépendants)

---

## Phase 5: AUDIT (Spécifique Goose)

### 📌 Principe
**TOUTE action doit être traçable.**

### 🗃️ 3 Niveaux d'audit

#### 1. PostgreSQL (audit_logs table)
**Obligatoire pour TOUTE action utilisateur.**

```python
from tool_gateway.services.postgres_service import insert_audit

event = {
    "timestamp": str(datetime.utcnow()),
    "action": "nom_action",
    "details": {"key": "value"}  # Truncated si nécessaire
}
insert_audit("nom_action", event)
```

**Exemples :**
- `/memory/search` → `{"query": "...", "results_count": 3}`
- `/generate-cv` → `{"candidate": "...", "status": "generated"}`
- `/memory/store` → `{"point_id": "...", "collection": "..."}`

#### 2. Qdrant (si applicable)
**Pour toute opération de mémoire vectorielle.**

```python
# Stockage
client.upsert(collection_name=..., points=[...])

# Recherche
results = client.query_points(collection_name=..., query=...)
```

#### 3. GOOSE_GENESIS_LOG.md
**Journal humain des modifications majeures.**

```markdown
## Tâche X : [Nom] - TERMINÉE ✅

**Date:** 2026-05-21 HH:MM UTC
**Agent:** Mistral Vibe / Lucas

### Actions:
1. ✅ [Action 1]
2. ✅ [Action 2]

### Fichiers modifiés:
- `path/to/file.py`

### Tests:
- [ ] Test 1 → ✅ Résultat
- [ ] Test 2 → ✅ Résultat

### Commit:
- Hash: [commit hash]
- Message: [commit message]

### Prochaine révision:
[Quand ?]
```

---

## 📜 TEMPLATE COMPLET POUR NOUVELLE TÂCHE

```markdown
# [TÂCHE N°] : [Nom de la tâche]

**Créé par :** [Nom]  
**Date :** [YYYY-MM-DD HH:MM UTC]  
**Statut :** ⏳ EN COURS / ✅ TERMINÉE / ❌ BLOQUÉE

---

## 1️⃣ THINK : Contexte

### Objectif
[1 phrase claire]

### Contexte
[2-3 phrases max]

### Arborescence
```bash
$(tree path/to/target -L 2)
```

---

## 2️⃣ PLAN : Étapes Techniques

### Fichiers cibles
| Fichier | Modification | Priorité |
|---------|--------------|----------|
| `path/file.py` | [Description] | Haute |
| `path/other.py` | [Description] | Moyenne |

### Dépendances
| Service | Statut | Vérification | Résultat |
|---------|--------|--------------|---------|
| PostgreSQL | ? | `docker ps` | ✅/❌ |
| Qdrant | ? | `curl localhost:6334` | ✅/❌ |
| Ollama | ? | `curl localhost:11434` | ✅/❌ |

### Étapes
1. [Action 1]
   - Commande : `...`
   - Résultat attendu : `...`
2. [Action 2]
   - Commande : `...`
   - Résultat attendu : `...`

---

## 3️⃣ CRITIQUE : Risques

| Risque | Impact | Vérification | Solution | Statut |
|--------|--------|--------------|----------|--------|
| [Risque 1] | [Haut/Moyen/Faible] | [Commande] | [Solution] | ✅/❌ |
| [Risque 2] | [Haut/Moyen/Faible] | [Commande] | [Solution] | ✅/❌ |

---

## 4️⃣ EXECUTE : Modifications

### Modification 1
**Fichier :** `path/to/file.py`

<<<<<<< SEARCH
[code existant]
=======
[code modifié]
>>>>>>> REPLACE

### Modification 2
**Fichier :** `path/to/other.py`

<<<<<<< SEARCH
[code existant]
=======
[code modifié]
>>>>>>> REPLACE

---

## 5️⃣ AUDIT : Vérification

### Tests exécutés
- [ ] Test 1 : `commande` → **Résultat** ✅/❌
- [ ] Test 2 : `commande` → **Résultat** ✅/❌

### Audit PostgreSQL
```bash
# Commande de vérification
docker exec goose-postgres psql -U goose -d goose_ai -c "SELECT * FROM audit_logs WHERE action = 'nom_action' ORDER BY created_at DESC;"
```

### Audit Qdrant
```bash
# Commande de vérification
curl http://localhost:6334/collections/[collection_name]/points/scroll -d '{"limit": 5}'
```

### Mise à jour du log
- [ ] GOOSE_GENESIS_LOG.md mis à jour
- [ ] Commit git créé
- [ ] Push sur GitHub/GitLab

---

## 📊 STATUT FINAL

| Critère | Statut | Date |
|---------|--------|------|
| THINK | ✅ | [date] |
| PLAN | ✅ | [date] |
| CRITIQUE | ✅ | [date] |
| EXECUTE | ✅ | [date] |
| AUDIT | ✅ | [date] |

**Durée totale :** [XX minutes]  
**Prochaine tâche :** [lien/numéro]
```

---

## 🎯 RÈGLES D'OR GOOSE

1. **Jamais de code sans test** → Chaque modification doit être testée immédiatement
2. **Jamais de test sans audit** → Chaque test réussi doit être consigné
3. **Jamais d'audit sans preuve** → Chaque entrée d'audit doit correspondre à une action réelle
4. **Jamais de "ça devrait marcher"** → Toujours vérifier avec des commandes concrètes
5. **Toujours documenter** → GOOSE_GENESIS_LOG.md est la source de vérité

---

## 📚 ANNEXES

### Commandes utiles

#### Vérification infrastructure
```bash
# Tous les services Docker
docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"

# Ports utilisés
ss -tlnp | grep -E "(3004|5434|6374|6334|11434|8044|5684)"

# Logs uvicorn
tail -f /tmp/uvicorn.log
```

#### Vérification données
```bash
# PostgreSQL audit
docker exec goose-postgres psql -U goose -d goose_ai -c "SELECT COUNT(*) FROM audit_logs;"

# Qdrant collections
curl http://localhost:6334/collections | python3 -m json.tool

# Qdrant points dans une collection
curl -X POST http://localhost:6334/collections/[name]/points/scroll -H "Content-Type: application/json" -d '{"limit": 10}'
```

#### Tests endpoints
```bash
# Health check
curl http://localhost:8044/health

# Test endpoint générique
curl -X POST http://localhost:8044/[endpoint] -H "Content-Type: application/json" -d '{"key": "value"}'
```

---

**Document maintenu par :** Mistral Vibe + Lucas  
**Dernière mise à jour :** 2026-05-21  
**Prochaine révision :** Après chaque tâche majeure