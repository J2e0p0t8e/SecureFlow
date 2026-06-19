"""Reproduit une analyse Audit-to-Fix et affiche l'exception réelle."""

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")

import django

django.setup()

SAMPLE = """
import os
API_KEY = "sk-secret123"
password = "admin123"
"""

if __name__ == "__main__":
    try:
        from apps.orchestrator.services import run_security_audit

        result = run_security_audit(SAMPLE, project_label="debug-test", locale="en")
        print("OK")
        print("room_id:", result.room_id)
        print("branch:", result.branch)
        print("decision:", result.decision)
        print("agents:", [r.agent_name for r in result.results])
    except Exception:
        traceback.print_exc()
        sys.exit(1)
