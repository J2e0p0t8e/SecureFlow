"""
Orchestrateur Mode A — pipeline unifié Audit-to-Fix.
"""

from __future__ import annotations

from typing import Callable

from apps.agents.base import AgentResult
from apps.core.agent_output import extract_audit_id, extract_decision, extract_metadata_json, generate_id
from apps.core.pipeline_context import get_ingestion_meta, get_locale
from apps.orchestrator.audit_to_fix import AUDIT_TO_FIX_BAND_AGENTS, AuditToFixOrchestrator, AuditToFixRunResult

MODE_A_BAND_AGENTS = AUDIT_TO_FIX_BAND_AGENTS


class ModeAOrchestrator(AuditToFixOrchestrator):
    """Alias — Mode A = Audit-to-Fix régulé (recrutement dynamique + remédiation)."""

    def run(
        self,
        project_content: str,
        *,
        task_id: str | None = None,
        project_label: str = "Projet",
        on_room_created: Callable[[str], None] | None = None,
        on_progress: Callable[[dict], None] | None = None,
        ingestion_meta: dict | None = None,
        locale: str | None = None,
        resume_from_index: int = 0,
        existing_results: list[AgentResult] | None = None,
        existing_room_id: str | None = None,
        skip_human_gate: bool = False,
        resume_branch: str | None = None,
    ) -> AuditToFixRunResult:
        branch = resume_branch
        if resume_from_index > 0 and existing_room_id and not branch:
            branch = "remediation"

        return super().run(
            project_content,
            task_id=task_id,
            initial_label=project_label,
            on_room_created=on_room_created,
            on_progress=on_progress,
            ingestion_meta=ingestion_meta,
            locale=locale,
            resume_branch=branch,
            existing_results=existing_results,
            existing_room_id=existing_room_id,
            skip_human_gate=skip_human_gate,
        )


# Compatibilité imports existants
ModeARunResult = AuditToFixRunResult
