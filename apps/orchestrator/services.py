"""
Point d'entrée métier pour l'orchestrateur.

Personne 2 (API Django) doit appeler ces fonctions — pas les agents directement.
"""

from __future__ import annotations

from apps.core.config import check_runtime_config
from apps.orchestrator.mode_a import MODE_A_BAND_AGENTS, ModeAOrchestrator, ModeARunResult


def run_security_audit(
    project_content: str,
    *,
    project_label: str = "Projet",
    task_id: str | None = None,
) -> ModeARunResult:
    """
    Lance un audit sécurité Mode A complet.

    Args:
        project_content: Texte du projet (code, arborescence, README…).
        project_label: Titre affiché dans la Band Room.
        task_id: Identifiant de tâche Band optionnel.

    Returns:
        ModeARunResult avec room_id, decision, audit_id, rapports agents.
    """
    check_runtime_config(required_band_agents=MODE_A_BAND_AGENTS)
    orchestrator = ModeAOrchestrator()
    return orchestrator.run(
        project_content,
        task_id=task_id,
        project_label=project_label,
    )


def run_security_audit_json(
    project_content: str,
    **kwargs,
) -> dict:
    """Même chose que run_security_audit, format dict pour réponse API JSON."""
    return run_security_audit(project_content, **kwargs).to_dict()
