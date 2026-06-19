"""
Point d'entrée métier pour l'orchestrateur Audit-to-Fix.
"""

from __future__ import annotations

from typing import Any, Callable

from apps.core.config import check_runtime_config
from apps.orchestrator.mode_a import MODE_A_BAND_AGENTS, ModeAOrchestrator, ModeARunResult


def run_security_audit(
    project_content: str,
    *,
    project_label: str = "Projet",
    task_id: str | None = None,
    on_room_created: Callable[[str], None] | None = None,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
    ingestion_meta: dict[str, Any] | None = None,
    locale: str | None = None,
    resume_from_index: int = 0,
    existing_results: list | None = None,
    existing_room_id: str | None = None,
    skip_human_gate: bool = False,
    resume_branch: str | None = None,
) -> ModeARunResult:
    check_runtime_config(required_band_agents=MODE_A_BAND_AGENTS)
    orchestrator = ModeAOrchestrator()
    return orchestrator.run(
        project_content,
        task_id=task_id,
        project_label=project_label,
        on_room_created=on_room_created,
        on_progress=on_progress,
        ingestion_meta=ingestion_meta,
        locale=locale,
        resume_from_index=resume_from_index,
        existing_results=existing_results,
        existing_room_id=existing_room_id,
        skip_human_gate=skip_human_gate,
        resume_branch=resume_branch,
    )


def run_security_audit_json(project_content: str, **kwargs) -> dict:
    return run_security_audit(project_content, **kwargs).to_dict()
