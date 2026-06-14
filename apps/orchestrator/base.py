"""
Orchestrateur générique — Room Band multi-agents (13 identités distinctes).

Flux :
1. Le premier agent crée la Room
2. Les autres agents sont ajoutés comme participants
3. Chaque agent publie avec @mention vers le suivant
4. Le contexte LLM est cumulé côté orchestrateur (fiabilité)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from apps.agents.band_registry import load_credentials
from apps.agents.base import AgentResult, BaseAgent
from apps.agents.band_client import BandRoom

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


class MultiAgentWorkflowRunner:
    """Enchaîne des agents SecureFlow, chacun avec son propre compte Band."""

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

        for agent in self.agents[1:]:
            creds = load_credentials(agent.name)
            if not creds.agent_id:
                raise ValueError(f"Agent ID manquant pour {agent.name}")
            lead.band.add_participant(room.id, creds.agent_id)
            logger.info("Participant ajouté : %s", agent.name)

        return room

    @staticmethod
    def _build_team_context(initial_content: str, results: list[AgentResult]) -> str:
        sections = [f"## Contenu initial\n{initial_content.strip()}"]
        for result in results:
            sections.append(f"## {result.agent_name}\n{result.content.strip()}")
        return "\n\n".join(sections)

    def run(
        self,
        initial_content: str,
        *,
        task_id: str | None = None,
        initial_label: str = "Projet",
    ) -> WorkflowRunResult:
        room = self._setup_room(task_id)
        self.agents[0].band.seed_room(room.id, initial_content, label=initial_label)

        results: list[AgentResult] = []
        for index, agent in enumerate(self.agents):
            team_context = self._build_team_context(initial_content, results)
            next_agent = self.agents[index + 1] if index + 1 < len(self.agents) else None

            logger.info("Exécution de %s...", agent.name)
            result = agent.run(room.id, extra_input=team_context, next_agent=next_agent)
            results.append(result)
            logger.info("%s terminé.", agent.name)

        return WorkflowRunResult(room_id=room.id, results=results)
