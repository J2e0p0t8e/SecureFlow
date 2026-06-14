"""
Test manuel du pipeline Mode A complet (5 agents).

Prérequis : .env configuré (BAND_API_KEY + GROQ_API_KEY ou AIMLAPI_API_KEY)

Usage :
    .venv\\Scripts\\python scripts/test_mode_a.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")

import django

django.setup()

from workflows.mode_a import run_mode_a

SAMPLE_FILE = ROOT / "scripts" / "sample_flask.py"


def main() -> None:
    print("=== SecureFlow AI — Mode A (Security Audit) ===\n")
    print("Lancement du pipeline (5 agents)... Cela peut prendre 1-3 minutes.\n")

    project_content = SAMPLE_FILE.read_text(encoding="utf-8")
    result = run_mode_a(project_content, project_label="mini_app Flask")

    print(f"Room Band  : {result.room_id}")
    print(f"Décision   : {result.decision or 'non détectée'}")
    print(f"Audit ID   : {result.audit_id or 'non détecté'}")
    print("\n--- Agents exécutés ---")
    for step in result.results:
        preview = step.content[:80].replace("\n", " ")
        print(f"  [OK] {step.agent_name} — {preview}...")

    print("\n--- Rapport final (DecisionAgent) ---\n")
    print(result.final_report)


if __name__ == "__main__":
    main()
