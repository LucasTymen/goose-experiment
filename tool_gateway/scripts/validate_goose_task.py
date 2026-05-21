#!/usr/bin/env python3
"""
GOOSE Task Validator
====================

Vérifie qu'une tâche suit le protocole Goose en 5 phases.

Usage:
    python validate_goose_task.py --task "Tâche 2: Advanced Retrieval"
    python validate_goose_task.py --task-id 2
    python validate_goose_task.py --check-all

Options:
    --task, -t    Nom ou description de la tâche
    --task-id, -i  Numéro de la tâche
    --check-all, -a Vérifier toutes les tâches documentées
    --verbose, -v   Mode verbeux
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class TaskValidator:
    """Valide une tâche Goose selon le protocole en 5 phases."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.log_file = "~/GOOSE/tool_gateway/logs/GOOSE_GENESIS_LOG.md"
        self.protocol_file = "~/GOOSE/tool_gateway/GOOSE_PROTOCOL.md"
        
    def log(self, message: str, level: str = "INFO"):
        """Affiche un message si verbose est activé."""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command: str) -> Tuple[bool, str]:
        """Exécute une commande et retourne (success, output)."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            success = result.returncode == 0
            output = result.stdout.strip() or result.stderr.strip()
            return success, output
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def check_service(self, service_name: str, port: int, check_cmd: str) -> Dict:
        """Vérifie qu'un service est actif."""
        success, output = self.run_command(check_cmd)
        return {
            "service": service_name,
            "port": port,
            "status": "✅ ACTIF" if success else "❌ INACTIF",
            "details": output[:100] if output else "Aucun détail"
        }
    
    def check_postgres_audit(self, action: str, expected_count: int = 1) -> Dict:
        """Vérifie qu'une action est dans audit_logs."""
        cmd = f"docker exec goose-postgres psql -U goose -d goose_ai -c \"SELECT COUNT(*) as count FROM audit_logs WHERE action = '{action}'\""
        success, output = self.run_command(cmd)
        
        if success and "count" in output:
            try:
                # Parse the output to get the count
                count = int(output.split("|")[-1].strip())
                return {
                    "action": action,
                    "status": "✅ TROUVÉ" if count >= expected_count else "⚠️ PEU D'ENTRÉES",
                    "count": count,
                    "expected": expected_count
                }
            except:
                return {"action": action, "status": "⚠️ ERREUR PARSING", "details": output[:100]}
        else:
            return {"action": action, "status": "❌ NON TROUVÉ", "details": output[:100]}
    
    def check_qdrant_collection(self, collection_name: str) -> Dict:
        """Vérifie qu'une collection existe dans Qdrant."""
        cmd = f"curl -s http://localhost:6334/collections | python3 -c \"import sys, json; data=json.load(sys.stdin); print('1' if '{collection_name}' in [c['name'] for c in data['result']['collections']] else '0')\""
        success, output = self.run_command(cmd)
        
        return {
            "collection": collection_name,
            "status": "✅ EXISTE" if output.strip() == "1" else "❌ MANQUANTE"
        }
    
    def check_endpoint(self, endpoint: str, method: str = "GET", data: str = "" ) -> Dict:
        """Vérifie qu'un endpoint FastAPI répond correctement."""
        base_url = "http://localhost:8044"
        full_url = f"{base_url}{endpoint}"
        
        if method.upper() == "GET":
            cmd = f"curl -s -w '\nHTTP_CODE:%{{http_code}}' {full_url}"
        else:
            cmd = f"curl -s -X {method} -H 'Content-Type: application/json' -d '{data}' -w '\nHTTP_CODE:%{{http_code}}' {full_url}"
        
        success, output = self.run_command(cmd)
        
        # Separate body and HTTP code
        if "HTTP_CODE:" in output:
            body, code = output.rsplit("HTTP_CODE:", 1)
            code = code.strip()
            body = body.strip()
            
            try:
                # Try to parse as JSON
                json.loads(body)
                status = "✅ 200 OK" if code == "200" else f"⚠️ HTTP {code}"
            except:
                status = f"⚠️ HTTP {code} (non-JSON)"
            
            return {
                "endpoint": endpoint,
                "method": method,
                "status": status,
                "http_code": code,
                "response_preview": body[:100] if body else "Aucune réponse"
            }
        else:
            return {
                "endpoint": endpoint,
                "method": method,
                "status": "❌ INACCESSIBLE",
                "details": output[:100]
            }
    
    def validate_phase_think(self, task_info: Dict) -> Dict:
        """Valide la phase THINK."""
        checks = []
        
        # Vérifier qu'une arborescence a été fournie
        if "arborescence" in task_info.get("think", {}):
            checks.append({"check": "Arborescence fournie", "status": "✅"})
        else:
            checks.append({"check": "Arborescence fournie", "status": "❌ MANQUANTE"})
        
        # Vérifier objectif clair
        if "objectif" in task_info.get("think", {}):
            checks.append({"check": "Objectif clair", "status": "✅"})
        else:
            checks.append({"check": "Objectif clair", "status": "❌ MANQUANT"})
        
        return {"phase": "THINK", "checks": checks}
    
    def validate_phase_plan(self, task_info: Dict) -> Dict:
        """Valide la phase PLAN."""
        checks = []
        plan = task_info.get("plan", {})
        
        if "fichiers_cibles" in plan:
            checks.append({"check": "Fichiers cibles définis", "status": "✅"})
        else:
            checks.append({"check": "Fichiers cibles définis", "status": "❌ MANQUANTS"})
        
        if "etapes" in plan:
            steps_count = len(plan["etapes"])
            checks.append({"check": f"Étapes définies ({steps_count})", "status": "✅" if steps_count > 0 else "❌ MANQUANTES"})
        else:
            checks.append({"check": "Étapes définies", "status": "❌ MANQUANTES"})
        
        if "dependances" in plan:
            checks.append({"check": "Dépendances vérifiées", "status": "✅"})
        else:
            checks.append({"check": "Dépendances vérifiées", "status": "❌ MANQUANTES"})
        
        return {"phase": "PLAN", "checks": checks}
    
    def validate_phase_critique(self, task_info: Dict) -> Dict:
        """Valide la phase CRITIQUE."""
        checks = []
        critique = task_info.get("critique", {})
        
        if "risques" in critique:
            risks_count = len(critique["risques"])
            checks.append({"check": f"Risques identifiés ({risks_count})", "status": "✅" if risks_count > 0 else "❌ MANQUANTS"})
        else:
            checks.append({"check": "Risques identifiés", "status": "❌ MANQUANTS"})
        
        return {"phase": "CRITIQUE", "checks": checks}
    
    def validate_phase_execute(self, task_info: Dict) -> Dict:
        """Valide la phase EXECUTE."""
        checks = []
        execute = task_info.get("execute", {})
        
        if "modifications" in execute:
            mods_count = len(execute["modifications"])
            checks.append({"check": f"Modifications définies ({mods_count})", "status": "✅" if mods_count > 0 else "❌ MANQUANTES"})
        else:
            checks.append({"check": "Modifications définies", "status": "❌ MANQUANTES"})
        
        # Vérifier format SEARCH/REPLACE
        if "modifications" in execute:
            for mod in execute["modifications"]:
                if "SEARCH" in mod and "REPLACE" in mod:
                    checks.append({"check": "Format SEARCH/REPLACE utilisé", "status": "✅"})
                    break
            else:
                checks.append({"check": "Format SEARCH/REPLACE utilisé", "status": "⚠️ FORMAT INCONNU"})
        
        return {"phase": "EXECUTE", "checks": checks}
    
    def validate_phase_audit(self, task_info: Dict) -> Dict:
        """Valide la phase AUDIT."""
        checks = []
        audit = task_info.get("audit", {})
        
        # Vérifier PostgreSQL
        if "postgres_actions" in audit:
            for action in audit["postgres_actions"]:
                result = self.check_postgres_audit(action)
                checks.append({
                    "check": f"Audit PostgreSQL pour '{action}'",
                    "status": result["status"]
                })
        
        # Vérifier Qdrant
        if "qdrant_collections" in audit:
            for collection in audit["qdrant_collections"]:
                result = self.check_qdrant_collection(collection)
                checks.append({
                    "check": f"Collection Qdrant '{collection}'",
                    "status": result["status"]
                })
        
        # Vérifier endpoints
        if "endpoints" in audit:
            for endpoint_info in audit["endpoints"]:
                result = self.check_endpoint(
                    endpoint_info["path"],
                    endpoint_info.get("method", "GET"),
                    endpoint_info.get("data", "")
                )
                checks.append({
                    "check": f"Endpoint {endpoint_info['path']} ({endpoint_info.get('method', 'GET')})",
                    "status": result["status"]
                })
        
        # Vérifier log humain
        if audit.get("log_updated", False):
            checks.append({"check": "GOOSE_GENESIS_LOG.md mis à jour", "status": "✅"})
        else:
            checks.append({"check": "GOOSE_GENESIS_LOG.md mis à jour", "status": "⚠️ À VÉRIFIER"})
        
        return {"phase": "AUDIT", "checks": checks}
    
    def validate_task(self, task_info: Dict) -> Dict:
        """Valide toutes les phases d'une tâche."""
        results = {
            "task": task_info.get("name", "Inconnue"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "phases": {}
        }
        
        # Valider chaque phase
        results["phases"]["THINK"] = self.validate_phase_think(task_info)
        results["phases"]["PLAN"] = self.validate_phase_plan(task_info)
        results["phases"]["CRITIQUE"] = self.validate_phase_critique(task_info)
        results["phases"]["EXECUTE"] = self.validate_phase_execute(task_info)
        results["phases"]["AUDIT"] = self.validate_phase_audit(task_info)
        
        # Calculer score global
        total_checks = 0
        passed_checks = 0
        
        for phase_name, phase_data in results["phases"].items():
            for check in phase_data["checks"]:
                total_checks += 1
                if "✅" in check["status"]:
                    passed_checks += 1
                elif "⚠️" in check["status"]:
                    passed_checks += 0.5  # Warning = moitié des points
        
        results["score"] = {
            "total": total_checks,
            "passed": passed_checks,
            "percentage": round((passed_checks / total_checks) * 100, 1) if total_checks > 0 else 0
        }
        
        # Déterminer statut global
        if results["score"]["percentage"] >= 90:
            results["status"] = "✅ VALIDÉ"
        elif results["score"]["percentage"] >= 70:
            results["status"] = "⚠️ AVEC AVERTOIREMENTS"
        elif results["score"]["percentage"] >= 50:
            results["status"] = "❌ INCOMPLET"
        else:
            results["status"] = "❌ NON CONFORME"
        
        return results
    
    def validate_infrastructure(self) -> Dict:
        """Valide que l'infrastructure Goose est opérationnelle."""
        services = [
            ("OpenWebUI", 3004, "curl -s http://localhost:3004 >/dev/null"),
            ("PostgreSQL", 5434, "docker exec goose-postgres pg_isready -U goose -d goose_ai"),
            ("Redis", 6374, "docker exec goose-redis redis-cli ping"),
            ("Qdrant", 6334, "curl -s http://localhost:6334/collections >/dev/null"),
            ("Ollama", 11434, "curl -s http://localhost:11434/api/tags >/dev/null"),
            ("FastAPI", 8044, "curl -s http://localhost:8044/health >/dev/null"),
            ("n8n", 5684, "curl -s http://localhost:5684/healthz >/dev/null"),
        ]
        
        results = []
        for name, port, check_cmd in services:
            results.append(self.check_service(name, port, check_cmd))
        
        active_count = sum(1 for r in results if "✅" in r["status"])
        
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "services": results,
            "summary": {
                "total": len(results),
                "active": active_count,
                "status": "✅ TOUS ACTIFS" if active_count == len(results) else f"⚠️ {active_count}/{len(results)} ACTIFS"
            }
        }


def main():
    parser = argparse.ArgumentParser(
        description="Valide une tâche Goose selon le protocole en 5 phases.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--task", "-t",
        type=str,
        help="Nom ou description de la tâche à valider"
    )
    parser.add_argument(
        "--task-id", "-i",
        type=int,
        help="Numéro de la tâche à valider"
    )
    parser.add_argument(
        "--check-infra", "-c",
        action="store_true",
        help="Vérifier l'infrastructure Goose"
    )
    parser.add_argument(
        "--check-all", "-a",
        action="store_true",
        help="Vérifier toutes les tâches documentées"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mode verbeux"
    )
    
    args = parser.parse_args()
    validator = TaskValidator(verbose=args.verbose)
    
    if args.check_infra:
        print("\n" + "="*60)
        print("🔍 VÉRIFICATION INFRASTRUCTURE GOOSE")
        print("="*60 + "\n")
        
        infra_result = validator.validate_infrastructure()
        
        print(f"Statut: {infra_result['summary']['status']}")
        print(f"Actifs: {infra_result['summary']['active']}/{infra_result['summary']['total']}\n")
        
        for service_info in infra_result['services']:
            print(f"  {service_info['service']:15} (port {service_info['port']:5}) : {service_info['status']}")
        
        print()
        sys.exit(0 if infra_result['summary']['active'] == infra_result['summary']['total'] else 1)
    
    # Pour l'instant, on implémente juste la vérification infrastructure
    # et on affiche un exemple pour les tâches
    
    if not args.task and not args.task_id and not args.check_all:
        print("\n" + "="*60)
        print("📋 GOOSE TASK VALIDATOR")
        print("="*60)
        print("\nUsage:")
        print("  python validate_goose_task.py --check-infra      # Vérifie l'infrastructure")
        print("  python validate_goose_task.py --task \"Tâche 2\"   # Valide une tâche spécifique")
        print("\nOptions:")
        print("  --verbose, -v    Mode verbeux")
        print("\nExemple de fichier de tâche:")
        print("  Voir GOOSE_PROTOCOL.md pour le format attendu")
        
        # Vérifier l'infrastructure par défaut
        print("\n" + "="*60)
        print("Vérification infrastructure par défaut:")
        print("="*60 + "\n")
        
        infra_result = validator.validate_infrastructure()
        
        print(f"Statut: {infra_result['summary']['status']}")
        print(f"Actifs: {infra_result['summary']['active']}/{infra_result['summary']['total']}\n")
        
        for service_info in infra_result['services']:
            print(f"  {service_info['service']:15} (port {service_info['port']:5}) : {service_info['status']}")
        
        print()
        sys.exit(0 if infra_result['summary']['active'] == infra_result['summary']['total'] else 1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
