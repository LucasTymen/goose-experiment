# 📁 Scripts Goose

Ce dossier contient les scripts d'automatisation et de validation pour le projet Goose.

---

## 📜 Scripts Disponibles

### 1. `validate_goose_task.py` - Validateur de Tâches Goose

**Description :** Valide qu'une tâche suit le protocole Goose en 5 phases (THINK, PLAN, CRITIQUE, EXECUTE, AUDIT).

**Usage :**
```bash
# Vérifier l'infrastructure complète
python validate_goose_task.py --check-infra

# Vérifier une tâche spécifique (à implémenter)
python validate_goose_task.py --task "Tâche 2: Advanced Retrieval"

# Afficher l'aide
python validate_goose_task.py --help
```

**Fonctionnalités actuelles :**
- ✅ Vérification infrastructure (7 services)
- ✅ Vérification PostgreSQL audit
- ✅ Vérification Qdrant collections
- ✅ Vérification endpoints FastAPI
- ⏳ Validation complète des tâches (à implémenter)

**Exemple de sortie :**
```
============================================================
🔍 VÉRIFICATION INFRASTRUCTURE GOOSE
============================================================

Statut: ✅ TOUS ACTIFS
Actifs: 7/7

  OpenWebUI       (port  3004) : ✅ ACTIF
  PostgreSQL      (port  5434) : ✅ ACTIF
  Redis           (port  6374) : ✅ ACTIF
  Qdrant          (port  6334) : ✅ ACTIF
  Ollama          (port 11434) : ✅ ACTIF
  FastAPI         (port  8044) : ✅ ACTIF
  n8n             (port  5684) : ✅ ACTIF
```

**Code de sortie :**
- `0` : Tous les services sont actifs
- `1` : Au moins un service est inactif

---

## 📦 Structure du Dossier

```
scripts/
├── validate_goose_task.py    # Validateur principal
├── README.md                # Ce fichier
└── [futurs scripts]         # À ajouter
```

---

## 🚀 Intégration avec le Protocole Goose

Ce script fait partie intégrante du **GOOSE_PROTOCOL.md** et doit être utilisé pour valider chaque phase des tâches.

### Workflow Recommandé :

```
1. THINK     → Analyser le contexte
2. PLAN      → Définir les étapes
3. CRITIQUE  → Vérifier les risques
4. EXECUTE   → Exécuter avec modifications minimales
5. AUDIT     → Valider avec ce script
```

**Exemple complet :**
```bash
# Après avoir exécuté une tâche
python scripts/validate_goose_task.py --check-infra

# Vérifier qu'un endpoint fonctionne
curl http://localhost:8044/health

# Vérifier l'audit PostgreSQL
docker exec goose-postgres psql -U goose -d goose_ai -c "SELECT COUNT(*) FROM audit_logs;"
```

---

## 🔧 Développement

Pour ajouter un nouveau script :
1. Créer le fichier dans `scripts/`
2. Ajouter une description dans ce README
3. S'assurer qu'il suit le protocole Goose (5 phases)
4. Tester avec l'infrastructure réelle

---

**Maintenu par :** Mistral Vibe + Lucas  
**Dernière mise à jour :** 2026-05-21