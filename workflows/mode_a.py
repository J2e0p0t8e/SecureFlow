"""
Point d'entrée du workflow Mode A.

Utilisé par l'API (Personne 2) ou les scripts de test.
"""

from apps.orchestrator.mode_a import ModeAOrchestrator, ModeARunResult
from apps.orchestrator.services import run_security_audit

__all__ = ["ModeAOrchestrator", "ModeARunResult", "run_mode_a", "run_security_audit"]


def run_mode_a(project_content: str, **kwargs) -> ModeARunResult:
    """Lance un audit sécurité Mode A."""
    return run_security_audit(project_content, **kwargs)
