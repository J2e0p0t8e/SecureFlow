"""
Orchestrateur générique — Room Band multi-agents (13 identités distinctes).

Flux Band-first :
1. Le premier agent crée la Room et y dépose le contenu initial (seed multi-parties)
2. Chaque agent lit l'historique Band via get_context() avant d'appeler le LLM
3. Chaque agent publie avec @mention vers le suivant
4. Escalades non linéaires et validation humaine passent par des events Band
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Callable

from apps.agents.band_registry import load_credentials, resolve_handle
from apps.agents.base import AgentResult, BaseAgent
from apps.agents.band_client import BandRoom
from apps.core.pipeline_context import (
    add_warning,
    get_ingestion_meta,
    get_locale,
    init_pipeline_context,
)
from apps.orchestrator.exceptions import HumanReviewPending, HumanReviewRequired

logger = logging.getLogger(__name__)


@dataclass
class WorkflowRunResult:
    """Résultat générique d'un pipeline multi-agents."""

    room_id: str
    results: list[AgentResult] = field(default_factory=list)

    @property
    def final_report(self) -> str:
        if not self.results:
            return ""
        return self.results[-1].content


def threat_needs_rescan(threat_content: str) -> bool:
    """Escalade non linéaire : Threat demande un second passage Scanner."""
    if not threat_content:
        return False
    upper = threat_content.upper()
    if "RE-SCAN" in upper or "RESCAN" in upper or "RESCANNER" in upper:
        return True
    p1_count = len(re.findall(r"\bP1\b", threat_content, flags=re.IGNORECASE))
    return p1_count >= 2


class MultiAgentWorkflowRunner:
    """Enchaîne des agents SecureFlow, chacun avec son propre compte Band."""

    human_gate_index: int | None = None
    enable_threat_rescan: bool = False

    def __init__(self, agent_classes: list[type[BaseAgent]]) -> None:
        self.agent_classes = agent_classes
        self.agents: list[BaseAgent] = [cls() for cls in agent_classes]

    @property
    def required_band_agent_names(self) -> list[str]:
        return [agent.name for agent in self.agents]

    def _setup_room(self, task_id: str | None = None) -> BandRoom:
        if not self.agents:
            raise ValueError("Aucun agent dans le pipeline.")

        lead = self.agents[0]
        room = lead.band.create_room(task_id=task_id)
        logger.info("Room %s créée par %s", room.id, lead.name)
        lead.band.ensure_owner_participant(room.id)

        for agent in self.agents[1:]:
            creds = load_credentials(agent.name)
            if not creds.agent_id:
                raise ValueError(f"Agent ID manquant pour {agent.name}")
            lead.band.add_participant(room.id, creds.agent_id)
            logger.info("Participant ajouté : %s", agent.name)

        return room

    def _human_gate_reason(self) -> str:
        locale = get_locale()
        if locale == "en":
            return (
                "Threat analysis is complete. Regulated workflow requires human "
                "confirmation before the final GO/NO-GO decision."
            )
        return (
            "L'analyse des menaces est terminée. Le workflow régulé exige une "
            "validation humaine avant la décision finale GO/NO-GO."
        )

    def _trigger_human_gate(
        self,
        *,
        room_id: str,
        results: list[AgentResult],
        resume_from_index: int,
        initial_content: str,
        initial_label: str,
        ingestion_meta: dict | None,
        workflow_mode: str | None,
    ) -> None:
        lead = self.agents[0]
        locale = get_locale()
        reason = self._human_gate_reason()
        try:
            lead.band.ensure_owner_participant(room_id)
            lead.band.post_human_review_request(room_id, reason=reason, locale=locale)
        except Exception as exc:
            logger.warning("post_human_review_request: %s", exc)
            add_warning(f"Band human review event failed: {exc}")

        pending = HumanReviewPending(
            room_id=room_id,
            project_content=initial_content,
            project_label=initial_label,
            resume_from_index=resume_from_index,
            reason=reason,
            results=list(results),
            ingestion_meta=ingestion_meta,
            locale=locale,
            workflow_mode=(workflow_mode or "A").upper(),
        )
        raise HumanReviewRequired(pending)

    def _maybe_rescan_after_threat(
        self,
        room: BandRoom,
        threat_result: AgentResult,
        *,
        rescan_done: bool,
    ) -> tuple[AgentResult | None, bool]:
        if rescan_done or not self.enable_threat_rescan:
            return None, rescan_done
        if not threat_needs_rescan(threat_result.content):
            return None, rescan_done

        scanner = self.agents[0]
        locale = get_locale()
        if locale == "en":
            msg = (
                "ThreatAgent requests a targeted re-scan: multiple P1 findings or "
                "explicit RE-SCAN in the threat report. @mention Scanner for confirmation."
            )
        else:
            msg = (
                "ThreatAgent demande un second scan ciblé : plusieurs P1 ou mention "
                "RE-SCAN explicite dans le rapport menaces. @mention Scanner pour confirmation."
            )

        scanner_creds = load_credentials(scanner.name)
        try:
            scanner.band.post_escalation(
                room.id,
                from_agent=threat_result.agent_name,
                message=msg,
                target_agent_id=scanner_creds.agent_id,
                target_handle=resolve_handle(scanner.name) or scanner_creds.handle,
                target_name=scanner.name,
            )
        except Exception as exc:
            logger.warning("post_escalation: %s", exc)

        logger.info("Escalade Band → second passage ScannerAgent")
        rescan = scanner.run(room.id, next_agent=self.agents[1] if len(self.agents) > 1 else None)
        return rescan, True

    def run(
        self,
        initial_content: str,
        *,
        task_id: str | None = None,
        initial_label: str = "Projet",
        on_room_created: Callable[[str], None] | None = None,
        on_progress: Callable[[dict], None] | None = None,
        ingestion_meta: dict | None = None,
        workflow_mode: str | None = None,
        locale: str | None = None,
        resume_from_index: int = 0,
        existing_results: list[AgentResult] | None = None,
        existing_room_id: str | None = None,
        skip_human_gate: bool = False,
    ) -> WorkflowRunResult:
        init_pipeline_context(ingestion_meta, workflow_mode=workflow_mode, locale=locale)

        if existing_room_id and resume_from_index > 0:
            room = BandRoom(id=existing_room_id, raw={})
            results: list[AgentResult] = list(existing_results or [])
        else:
            room = self._setup_room(task_id)
            if on_room_created:
                on_room_created(room.id)
            try:
                self.agents[0].band.seed_room(
                    room.id, initial_content, label=initial_label, locale=get_locale()
                )
            except Exception as exc:
                logger.warning("seed_room non bloquant ignoré: %s", exc)
                from apps.core.locale import api_message

                add_warning(api_message("band_seed_partial", get_locale()))
            results = []

        rescan_done = any(r.agent_name == "ScannerAgent" for r in results) and len(
            [r for r in results if r.agent_name == "ScannerAgent"]
        ) > 1

        index = resume_from_index
        while index < len(self.agents):
            if (
                not skip_human_gate
                and self.human_gate_index is not None
                and index == self.human_gate_index
            ):
                self._trigger_human_gate(
                    room_id=room.id,
                    results=results,
                    resume_from_index=index,
                    initial_content=initial_content,
                    initial_label=initial_label,
                    ingestion_meta=ingestion_meta,
                    workflow_mode=workflow_mode,
                )

            agent = self.agents[index]
            next_agent = self.agents[index + 1] if index + 1 < len(self.agents) else None

            if on_progress:
                on_progress(
                    {
                        "phase": "started",
                        "agent": agent.name,
                        "index": index,
                        "next_agent": next_agent.name if next_agent else None,
                    }
                )

            logger.info("Exécution de %s (contexte Band Room)...", agent.name)
            result = agent.run(room.id, next_agent=next_agent)
            results.append(result)
            logger.info("%s terminé.", agent.name)

            if on_progress:
                on_progress(
                    {
                        "phase": "completed",
                        "agent": result.agent_name,
                        "index": index,
                        "next_agent": next_agent.name if next_agent else None,
                        "agents": [
                            {"name": item.agent_name, "content": item.content}
                            for item in results
                        ],
                    }
                )

            if (
                self.enable_threat_rescan
                and agent.name == "ThreatAgent"
                and index + 1 < len(self.agents)
            ):
                rescan_result, rescan_done = self._maybe_rescan_after_threat(
                    room, result, rescan_done=rescan_done
                )
                if rescan_result is not None:
                    results.append(rescan_result)
                    if on_progress:
                        on_progress(
                            {
                                "phase": "completed",
                                "agent": rescan_result.agent_name,
                                "index": index,
                                "next_agent": next_agent.name if next_agent else None,
                                "agents": [
                                    {"name": item.agent_name, "content": item.content}
                                    for item in results
                                ],
                                "escalation": "threat_rescan",
                            }
                        )

            index += 1

        return WorkflowRunResult(room_id=room.id, results=results)
