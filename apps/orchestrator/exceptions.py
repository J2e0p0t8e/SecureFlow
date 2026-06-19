"""Exceptions orchestrateur — reprise pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from apps.agents.base import AgentResult


@dataclass
class HumanReviewPending:
    """État sauvegardé lorsqu'une validation humaine est requise."""

    room_id: str
    project_content: str
    project_label: str
    resume_from_index: int
    reason: str
    results: list[AgentResult] = field(default_factory=list)
    ingestion_meta: dict[str, Any] | None = None
    locale: str = "fr"
    workflow_mode: str = "A"
    review_kind: str = "pre_remediation"
    branch: str = "remediation"
    decision: str = ""

    def results_as_dicts(self) -> list[dict[str, str]]:
        return [
            {"name": item.agent_name, "content": item.content}
            for item in self.results
        ]


class HumanReviewRequired(Exception):
    """Le pipeline s'arrête en attente d'une décision humaine (publiée dans Band)."""

    def __init__(self, pending: HumanReviewPending) -> None:
        self.pending = pending
        super().__init__(pending.reason)
