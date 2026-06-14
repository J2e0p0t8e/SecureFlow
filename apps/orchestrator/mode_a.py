"""
Orchestrateur du Mode A — Security Audit.

5 agents Band distincts collaborent dans une Room partagée.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from apps.agents.base import AgentResult
from apps.agents.mode_a import MODE_A_AGENT_CLASSES
from apps.orchestrator.base import MultiAgentWorkflowRunner

logger = logging.getLogger(__name__)

AUDIT_ID_PATTERN = re.compile(r"SF-AUDIT-\d{8}-\d{4}", re.IGNORECASE)

MODE_A_BAND_AGENTS = [cls.name for cls in MODE_A_AGENT_CLASSES]


@dataclass
class ModeARunResult:
    """Résultat complet d'un audit Mode A."""

    room_id: str
    results: list[AgentResult] = field(default_factory=list)
    audit_id: str | None = None
    decision: str | None = None

    @property
    def final_report(self) -> str:
        if not self.results:
            return ""
        return self.results[-1].content

    def to_dict(self) -> dict:
        """Format JSON pour l'API Django (Personne 2)."""
        return {
            "mode": "A",
            "room_id": self.room_id,
            "decision": self.decision,
            "audit_id": self.audit_id,
            "final_report": self.final_report,
            "agents": [
                {"name": result.agent_name, "content": result.content}
                for result in self.results
            ],
        }


class ModeAOrchestrator(MultiAgentWorkflowRunner):
    """
    Pipeline Mode A : Scanner → Threat → Compliance → Risk → Decision.

    Chaque étape utilise son propre compte Band AI.
    """

    def __init__(self) -> None:
        super().__init__(MODE_A_AGENT_CLASSES)

    def run(
        self,
        project_content: str,
        *,
        task_id: str | None = None,
        project_label: str = "Projet",
    ) -> ModeARunResult:
        workflow = super().run(
            project_content,
            task_id=task_id,
            initial_label=project_label,
        )

        decision_result = workflow.results[-1] if workflow.results else None
        audit_id = _extract_audit_id(decision_result.content) if decision_result else None
        decision = _extract_decision(decision_result.content) if decision_result else None

        return ModeARunResult(
            room_id=workflow.room_id,
            results=workflow.results,
            audit_id=audit_id,
            decision=decision,
        )


def _extract_audit_id(text: str) -> str | None:
    match = AUDIT_ID_PATTERN.search(text)
    return match.group(0).upper() if match else None


def _extract_decision(text: str) -> str | None:
    for label in ("CRITIQUE", "CORRIGER", "SURVEILLER", "PROPRE"):
        if re.search(rf"\b{label}\b", text, re.IGNORECASE):
            return label
    return None
