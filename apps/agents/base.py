"""
Classe de base pour tous les agents SecureFlow AI.
"""

from __future__ import annotations

import logging
from abc import ABC
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings

from apps.agents.band_client import BandClient
from apps.agents.band_registry import get_band_client_for
from apps.agents.llm import LLMClient, get_llm_client_for_agent
from apps.agents.prompts import get_prompt
from apps.core.agent_output import get_required_prefix, split_discussion_and_report, validate_prefix
from apps.core.pipeline_context import add_warning, get_disagreement_context, get_locale, get_workflow_mode
from apps.core.text_limits import truncate_text

logger = logging.getLogger(__name__)

_CONVERSATION_RULES = {
    "fr": (
        "\n\nTON DANS LE FIL BAND (OBLIGATOIRE)\n"
        "Tu es un collègue humain en équipe sécurité, pas un robot. "
        "Réagis au dernier message du fil : accord, doute, question, nuance.\n"
        "Utilise « je », des phrases courtes, parfois une question directe à un collègue.\n"
        "Exemples : « Franchement le SQLi me inquiète », « @Threat tu confirmes ? », "
        "« Je ne suis pas sûr pour le XSS ».\n"
        "Pas de listes à puces dans DISCUSSION — garde ça pour RAPPORT."
    ),
    "en": (
        "\n\nBAND THREAD TONE (MANDATORY)\n"
        "You are a human teammate on a security squad, not a bot. "
        "React to the latest Band message: agree, push back, ask a question.\n"
        "Use « I », short sentences, occasionally a direct question to a colleague.\n"
        "Examples: « That SQLi worries me », « @Threat can you confirm? », "
        "« Not sold on the XSS finding ».\n"
        "No bullet lists in DISCUSSION — save those for REPORT."
    ),
}

_OUTPUT_FORMAT = {
    "fr": (
        "\n\nFORMAT DE SORTIE (DEUX PARTIES)\n"
        "1) DISCUSSION : (3 à 6 phrases naturelles, ton humain, réaction au fil Band)\n"
        "2) RAPPORT : (analyse structurée avec le préfixe obligatoire de ton rôle)\n\n"
        "Exemple de structure :\n"
        "DISCUSSION :\n"
        "Salut @Threat, j'ai parcouru le repo. Honnêtement la surface d'attaque est large — "
        "le paiement me fait surtout peur. Tu valides quand tu auras lu ?\n\n"
        "RAPPORT :\n"
        "SCAN TERMINÉ :\n"
        "• …"
    ),
    "en": (
        "\n\nOUTPUT FORMAT (TWO PARTS)\n"
        "1) DISCUSSION: (3–6 natural sentences, human tone, react to the Band thread)\n"
        "2) REPORT: (structured analysis with your mandatory role prefix)\n\n"
        "Example structure:\n"
        "DISCUSSION:\n"
        "Hey @Threat, I went through the repo. Honestly the attack surface is wide — "
        "payment code worries me most. Can you confirm once you've read?\n\n"
        "REPORT:\n"
        "SCAN COMPLETE:\n"
        "• …"
    ),
}


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
    """Moule commun pour tous les agents SecureFlow."""

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
        if self._llm is None:
            self._llm = get_llm_client_for_agent(self.name)
        return self._llm

    @property
    def required_prefix(self) -> str | None:
        return get_required_prefix(self.name, get_locale())

    def build_system_prompt(self) -> str:
        locale = get_locale()
        mode = get_workflow_mode()
        if mode:
            base = get_prompt(self.name, mode, locale)
        else:
            base = get_prompt(self.name, "A", locale) if locale == "en" else self.role_description.strip()
        return base + _CONVERSATION_RULES.get(locale, _CONVERSATION_RULES["fr"]) + _OUTPUT_FORMAT.get(
            locale, _OUTPUT_FORMAT["fr"]
        ) + (
            "\n\nRÈGLE RAPPORT : pas de Markdown (#, ```). Titres MAJUSCULES + « : », puces « • »."
            if locale != "en"
            else "\n\nREPORT RULE: no Markdown (#, ```). UPPERCASE headings + « : », bullets « • »."
        )

    def build_user_prompt(
        self,
        room_context: str,
        extra_input: str | None = None,
        *,
        from_band_history: bool = False,
    ) -> str:
        locale = get_locale()
        if locale == "en":
            context_label = "WORK CONTEXT"
            history_label = "BAND ROOM HISTORY"
            empty_label = "(empty)"
            truncate_agent = "agent context"
            truncate_room = "Band Room"
            mission = (
                "YOUR MISSION\n"
                f"Act as {self.name}. Write DISCUSSION like a teammate in chat, "
                "then REPORT with actionable findings.\n"
                "Read the Band Room history and react to what colleagues actually said — "
                "agree, disagree, or ask them something specific.\n"
                "Do NOT write handoff / @mention to the next agent — SecureFlow posts that after you."
            )
            band_note = (
                "The Band Room history above is the collaboration source of truth "
                "(agent messages, escalations, human validation)."
            )
        else:
            context_label = "CONTEXTE DE TRAVAIL"
            history_label = "HISTORIQUE BAND ROOM"
            empty_label = "(vide)"
            truncate_agent = "contexte agent"
            truncate_room = "Band Room"
            mission = (
                "TA MISSION\n"
                f"Agis en tant que {self.name}. Écris DISCUSSION comme un collègue dans le chat, "
                "puis RAPPORT avec les findings actionnables.\n"
                "Lis l'historique Band et réagis à ce que les collègues ont vraiment dit — "
                "accord, désaccord ou question précise.\n"
                "N'écris PAS de relais / @mention vers l'agent suivant — SecureFlow le publie après toi."
            )
            band_note = (
                "L'historique Band Room ci-dessus est la source de vérité collaborative "
                "(messages agents, escalades, validation humaine)."
            )

        if extra_input and extra_input.strip():
            limit = None
            if self.name == "ScannerAgent":
                limit = getattr(settings, "LLM_INITIAL_CONTENT_CHARS", None)
            sections = [
                context_label,
                truncate_text(extra_input.strip(), max_chars=limit, label=truncate_agent),
            ]
        else:
            sections = [
                history_label,
                truncate_text(room_context.strip() or empty_label, label=truncate_room),
            ]
            if from_band_history:
                sections.append(band_note)

        sections.append(mission)

        disagreement = get_disagreement_context()
        if disagreement and self.name == "DecisionAgent":
            scores = disagreement.get("scores") or {}
            if locale == "en":
                sections.append(
                    "DISAGREEMENT IN BAND ROOM\n"
                    f"Agent scores diverge ({disagreement.get('spread', '?')} pt spread): "
                    f"{scores}. Your final verdict MUST state which signal prevailed and why."
                )
            else:
                sections.append(
                    "DÉSACCORD DANS LA BAND ROOM\n"
                    f"Scores agents divergents (écart {disagreement.get('spread', '?')} pts): "
                    f"{scores}. Ton verdict DOIT indiquer quel signal prime et pourquoi."
                )

        return "\n\n".join(sections)

    def _complete_with_validation(self, system_prompt: str, user_prompt: str) -> tuple[str, str]:
        raw = self.llm.complete(system=system_prompt, user=user_prompt)
        discussion, report = split_discussion_and_report(raw)
        if not report:
            report = raw
        prefix = self.required_prefix
        locale = get_locale()
        if prefix and not validate_prefix(report, prefix):
            if locale == "en":
                retry_prompt = (
                    f"{user_prompt}\n\n"
                    f"MANDATORY FIX: the REPORT section MUST start with « {prefix} »."
                )
            else:
                retry_prompt = (
                    f"{user_prompt}\n\n"
                    f"CORRECTION OBLIGATOIRE : la section RAPPORT DOIT commencer par « {prefix} »."
                )
            raw = self.llm.complete(system=system_prompt, user=retry_prompt)
            discussion, report = split_discussion_and_report(raw)
            if not report:
                report = raw
            if not validate_prefix(report, prefix):
                msg = (
                    f"{self.name}: expected format not respected (missing prefix « {prefix} »)."
                    if locale == "en"
                    else (
                        f"{self.name} : le format attendu n'a pas été respecté "
                        f"(préfixe « {prefix} » manquant)."
                    )
                )
                add_warning(msg)
        if not discussion.strip():
            if locale == "en":
                discussion = (
                    f"I've reviewed the Band thread and finished my pass as {self.name}. "
                    "Sharing my structured report below."
                )
            else:
                discussion = (
                    f"J'ai relu le fil Band et terminé mon tour en tant que {self.name}. "
                    "Je partage mon rapport structuré ci-dessous."
                )
        return discussion.strip(), report.strip()

    def run(
        self,
        room_id: str,
        extra_input: str | None = None,
        next_agent: BaseAgent | None = None,
        prior_agent: BaseAgent | None = None,
        *,
        prefer_band_context: bool = True,
    ) -> AgentResult:
        messages = self.band.get_context(room_id)
        if prefer_band_context and messages:
            room_context = self.band.format_context_as_text(messages)
        elif extra_input and extra_input.strip():
            locale = get_locale()
            room_context = (
                "(fallback orchestrator context — Band history empty)"
                if locale == "en"
                else "(contexte de repli — historique Band vide)"
            )
            room_context = f"{room_context}\n\n{extra_input.strip()}"
        else:
            room_context = self.band.format_context_as_text(messages)

        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(
            room_context,
            extra_input,
            from_band_history=bool(prefer_band_context and messages and not extra_input),
        )
        content_discussion, content_report = self._complete_with_validation(system_prompt, user_prompt)
        locale = get_locale()

        reply_to = prior_agent.name if prior_agent else None
        try:
            self.band.post_agent_discussion(
                room_id,
                agent_name=self.name,
                content=content_discussion,
                reply_to_agent_name=reply_to,
                locale=locale,
            )
        except Exception as exc:
            logger.warning("%s — discussion Band ignorée: %s", self.name, exc)

        try:
            band_response = self.band.post_agent_report(
                room_id,
                agent_name=self.name,
                content=content_report,
            )
        except Exception as exc:
            logger.warning("%s — publication rapport Band ignorée: %s", self.name, exc)
            locale = get_locale()
            suffix = f"{self.name}: Band Room publish failed ({exc})."
            if locale != "en":
                suffix = f"{self.name} : publication Band Room échouée ({exc})."
            add_warning(suffix)
            band_response = {}

        return AgentResult(
            agent_name=self.name,
            room_id=room_id,
            content=content_report,
            band_response=band_response,
        )
