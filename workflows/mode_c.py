"""Point d'entrée du workflow Audit-to-Fix (ex-Mode C supprimé)."""

from apps.orchestrator.mode_a import ModeAOrchestrator, ModeARunResult
from apps.orchestrator.services import run_security_audit

__all__ = ["ModeAOrchestrator", "ModeARunResult", "run_mode_c", "run_security_audit"]


def run_mode_c(project_content: str, **kwargs) -> ModeARunResult:
    """Compatibilité — redirige vers Audit-to-Fix (branche reporting → PDF)."""
    return run_security_audit(project_content, **kwargs)
