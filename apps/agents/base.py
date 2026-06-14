"""
Classe de base pour tous les agents SecureFlow AI.

Chaque agent concret hérite de BaseAgent et définit :
- son nom (affiché dans la Band Room)
- sa consigne métier via apps/agents/prompts.py

Cycle de vie d'un agent :
    1. Lire le contexte cumulé de la Band Room
    2. Construire le prompt utilisateur (contexte + input optionnel)
    3. Appeler le LLM
    4. Publier la réponse dans la Band Room
    5. Retourner un AgentResult à l'orchestrateur

Exemple (Personne 3 / 4) :

    class FeasibilityAgent(BaseAgent):
        name = "FeasibilityAgent"
        role_description = '''Tu es un expert en cadrage de projet...'''

        def run(self, room_id: str, project_description: str | None = None) -> AgentResult:
            return super().run(room_id, extra_input=project_description)
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any

from apps.agents.band_client import BandClient
from apps.agents.band_registry import get_band_client_for, load_credentials, resolve_handle
from apps.agents.llm import LLMClient, get_llm_client


@dataclass
class AgentResult:
    """Résultat standard renvoyé par un agent à l'orchestrateur."""

    agent_name: str
    room_id: str
    content: str
    band_response: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        preview = self.content[:120].replace("\n", " ")
        return f"{self.agent_name} @ {self.room_id}: {preview}..."


class BaseAgent(ABC):
    """
    Moule commun pour ScannerAgent, ThreatAgent, FeasibilityAgent, etc.

    Attributes:
        name: Nom affiché dans la Band Room (ex: "ScannerAgent").
        role_description: Consigne système — la "fiche de poste" de l'agent.
    """

    name: str = "BaseAgent"
    role_description: str = "Tu es un agent SecureFlow AI."

    def __init__(
        self,
        llm: LLMClient | None = None,
        band: BandClient | None = None,
    ) -> None:
        self._llm = llm
        self.band = band or get_band_client_for(self.name)

    @property
    def llm(self) -> LLMClient:
        """Charge le client LLM à la demande (évite une erreur à l'import sans .env)."""
        if self._llm is None:
            self._llm = get_llm_client()
        return self._llm

    # ------------------------------------------------------------------
    # Points d'extension pour les agents concrets
    # ------------------------------------------------------------------

    def build_system_prompt(self) -> str:
        """Prompt système envoyé au LLM."""
        return self.role_description.strip()

    def build_user_prompt(self, room_context: str, extra_input: str | None = None) -> str:
        """
        Prompt utilisateur : historique Band + données spécifiques à l'étape.

        Les sous-classes peuvent surcharger cette méthode pour reformater
        l'input (ex: ne passer qu'une partie du projet au ThreatAgent).
        """
        sections = [
            "## Historique de la Band Room",
            room_context.strip() or "(vide)",
        ]

        if extra_input and extra_input.strip():
            sections.extend(["## Input complémentaire pour cette étape", extra_input.strip()])

        sections.append(
            "## Ta mission\n"
            f"Agis en tant que {self.name}. Produis une réponse structurée, "
            "actionnable, en français. Réfère-toi explicitement au travail des "
            "agents précédents quand il est pertinent."
        )
        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Exécution
    # ------------------------------------------------------------------

    def run(
        self,
        room_id: str,
        extra_input: str | None = None,
        next_agent: BaseAgent | None = None,
    ) -> AgentResult:
        """
        Exécute l'agent dans une Band Room existante.

        Args:
            room_id: Identifiant de la Band Room (créée par l'orchestrateur).
            extra_input: Contexte cumulé (projet + travail des agents précédents).
            next_agent: Agent suivant — déclenche une @mention Band.

        Returns:
            AgentResult avec le texte produit et la réponse Band brute.
        """
        messages = self.band.get_context(room_id)
        room_context = self.band.format_context_as_text(messages)

        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(room_context, extra_input)

        content = self.llm.complete(system=system_prompt, user=user_prompt)

        next_agent_id = None
        next_agent_handle = None
        next_agent_name = None
        if next_agent is not None:
            next_creds = load_credentials(next_agent.name)
            next_agent_id = next_creds.agent_id
            next_agent_handle = resolve_handle(next_agent.name)
            next_agent_name = next_agent.name

        band_response = self.band.post_agent_output(
            room_id,
            agent_name=self.name,
            content=content,
            next_agent_id=next_agent_id,
            next_agent_handle=next_agent_handle,
            next_agent_name=next_agent_name,
        )

        return AgentResult(
            agent_name=self.name,
            room_id=room_id,
            content=content,
            band_response=band_response,
        )
