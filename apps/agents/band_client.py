"""
Client HTTP pour l'API Agent de Band AI.

Documentation : https://docs.thenvoi.com/api/agent-api

Dans SecureFlow, **13 Remote Agents Band** collaborent dans la même Room.
Chaque agent Python utilise sa propre clé API et @mentionne le suivant.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Limite Band Room (évite 403 WAF sur gros dépôts GitHub)
DEFAULT_BAND_CONTENT_LIMIT = 6_000


@dataclass
class BandRoom:
    """Room Band créée pour une session d'analyse."""

    id: str
    raw: dict[str, Any]


class BandClient:
    """Wrapper minimal autour de l'API REST Agent de Band."""

    def __init__(
        self,
        api_key: str | None = None,
        agent_id: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or ""
        self.agent_id = agent_id or ""
        self.base_url = (base_url or settings.BAND_BASE_URL).rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("Clé API Band manquante pour cet agent.")

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api/v1/agent{path}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> dict[str, Any]:
        response = requests.request(
            method,
            self._url(path),
            headers=self._headers,
            json=json,
            params=params,
            timeout=self.timeout,
        )
        if not response.ok:
            raise BandAPIError(
                f"Band API {method} {path} → {response.status_code}: {response.text}"
            )
        if not response.content:
            return {}
        return response.json()

    @staticmethod
    def _unwrap(data: dict[str, Any]) -> dict[str, Any]:
        """Band enveloppe souvent les réponses dans {\"data\": {...}}."""
        inner = data.get("data")
        if isinstance(inner, dict):
            return inner
        chat = data.get("chat")
        if isinstance(chat, dict):
            return chat
        return data

    def create_room(self, task_id: str | None = None) -> BandRoom:
        """Crée une nouvelle Band Room pour un workflow."""
        payload: dict[str, Any] = {"chat": {}}
        if task_id:
            payload["chat"]["task_id"] = task_id

        data = self._request("POST", "/chats", json=payload)
        chat = self._unwrap(data)
        room_id = chat.get("id") or chat.get("chat_id")
        if not room_id:
            raise BandAPIError(f"Réponse Band inattendue lors de create_room: {data}")

        return BandRoom(id=str(room_id), raw=data)

    def get_me(self) -> dict[str, Any]:
        """Profil de l'agent connecté (handle, nom…)."""
        return self._request("GET", "/me")

    def resolve_owner_user_id(self) -> str | None:
        """UUID du compte humain propriétaire (pour l'ajouter à la Room)."""
        configured = getattr(settings, "BAND_OWNER_USER_ID", "").strip()
        if configured:
            return configured

        try:
            payload = self._unwrap(self.get_me())
            candidates: list[Any] = [payload]
            for key in ("agent", "data", "profile", "user", "owner"):
                nested = payload.get(key) if isinstance(payload, dict) else None
                if isinstance(nested, dict):
                    candidates.append(nested)

            for item in candidates:
                if not isinstance(item, dict):
                    continue
                for key in ("owner_id", "owner_user_id", "user_id", "owner"):
                    value = item.get(key)
                    if isinstance(value, dict):
                        value = value.get("id")
                    if value:
                        return str(value)
        except Exception as exc:
            logger.debug("resolve_owner_user_id: %s", exc)
        return None

    def ensure_owner_participant(self, room_id: str) -> bool:
        """
        Ajoute le compte humain Band à la Room pour qu'il puisse répondre APPROUVE/REJETE.
        Les agents Band peuvent inviter leur propriétaire (voir Agent API participants).
        """
        owner_id = self.resolve_owner_user_id()
        if not owner_id:
            logger.warning(
                "BAND_OWNER_USER_ID manquant — l'opérateur ne pourra pas écrire dans la Room."
            )
            return False
        try:
            self.add_participant(room_id, owner_id, role="member")
            logger.info("Opérateur humain ajouté à la Room %s", room_id)
            return True
        except BandAPIError as exc:
            if "409" in str(exc) or "already" in str(exc).lower():
                return True
            logger.warning("ensure_owner_participant: %s", exc)
            return False
        except Exception as exc:
            logger.warning("ensure_owner_participant: %s", exc)
            return False

    def add_participant(
        self,
        room_id: str,
        participant_id: str,
        role: str = "member",
    ) -> dict[str, Any]:
        """Recrute un autre agent Band dans la Room."""
        return self._request(
            "POST",
            f"/chats/{room_id}/participants",
            json={
                "participant": {
                    "participant_id": participant_id,
                    "role": role,
                }
            },
        )

    def post_message(
        self,
        room_id: str,
        *,
        content: str,
        mentions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Envoie un message texte avec @mentions (collaboration multi-agents Band)."""
        text = self._truncate_for_band(content)
        mention_list = list(mentions or [])
        if not mention_list:
            return self.post_event(
                room_id,
                event_type="message",
                content=text,
                metadata={"source": "secureflow", "kind": "agent_message"},
            )
        return self._request(
            "POST",
            f"/chats/{room_id}/messages",
            json={"message": {"content": text, "mentions": mention_list}},
        )

    def get_context(self, room_id: str, page_size: int = 100) -> list[dict[str, Any]]:
        """
        Récupère l'historique pertinent pour l'agent (messages envoyés + @mentions).
        """
        data = self._request(
            "GET",
            f"/chats/{room_id}/context",
            params={"page": 1, "page_size": page_size},
        )

        inner = data.get("data")
        if isinstance(inner, list):
            return list(inner)

        unwrapped = self._unwrap(data)
        if isinstance(unwrapped, list):
            return list(unwrapped)

        messages = (
            unwrapped.get("messages")
            or data.get("messages")
            or data.get("context")
            or []
        )
        if isinstance(messages, dict):
            messages = messages.get("messages", [])
        return list(messages)

    def format_context_as_text(self, messages: list[dict[str, Any]]) -> str:
        """Transforme l'historique Band en texte lisible pour le LLM."""
        if not messages:
            return "(Aucun message précédent dans la Band Room.)"

        lines: list[str] = []
        for msg in messages:
            author = (
                msg.get("sender_name")
                or msg.get("author")
                or msg.get("sender", {}).get("name")
                or "Inconnu"
            )
            msg_type = msg.get("message_type") or msg.get("type") or "text"
            content = msg.get("content") or msg.get("body") or ""
            lines.append(f"[{author} | {msg_type}]\n{content}".strip())

        return "\n\n---\n\n".join(lines)

    def _truncate_for_band(self, content: str, limit: int | None = None) -> str:
        max_chars = limit or getattr(
            settings, "BAND_MAX_EVENT_CHARS", DEFAULT_BAND_CONTENT_LIMIT
        )
        text = content.strip()
        if len(text) <= max_chars:
            return text
        return (
            f"{text[:max_chars]}\n\n"
            f"[… suite dans les messages Band suivants — {len(text):,} caractères au total]"
        )

    def _chunk_for_band(self, content: str, limit: int | None = None) -> list[str]:
        max_chars = limit or getattr(
            settings, "BAND_MAX_EVENT_CHARS", DEFAULT_BAND_CONTENT_LIMIT
        )
        text = (content or "").strip()
        if not text:
            return []
        if len(text) <= max_chars:
            return [text]
        chunks: list[str] = []
        start = 0
        while start < len(text):
            chunks.append(text[start : start + max_chars])
            start += max_chars
        return chunks

    def post_event(
        self,
        room_id: str,
        *,
        event_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Publie un événement dans la Room (thought, task, error…).

        Les événements apparaissent dans l'historique et sont visibles
        côté interface quand on interroge la Room.
        """
        payload: dict[str, Any] = {
            "event": {
                "content": self._truncate_for_band(content),
                "message_type": event_type,
            }
        }
        if metadata:
            payload["event"]["metadata"] = metadata

        return self._request("POST", f"/chats/{room_id}/events", json=payload)

    def post_agent_output(
        self,
        room_id: str,
        *,
        agent_name: str,
        content: str,
        next_agent_id: str | None = None,
        next_agent_handle: str | None = None,
        next_agent_name: str | None = None,
        event_type: str = "thought",
    ) -> dict[str, Any]:
        """
        Publie le travail d'un agent dans la Band Room.

        Si un agent suivant est fourni, envoie un message texte @mention
        (requis par Band pour la collaboration multi-agents).
        Sinon, publie un événement (dernier agent du pipeline).
        """
        formatted = f"**{agent_name}**\n\n{content.strip()}"
        band_content = self._truncate_for_band(formatted)

        if next_agent_id and next_agent_handle:
            mention_content = f"@{next_agent_handle.lstrip('@')}\n\n{band_content}"
            mentions = [
                {
                    "id": next_agent_id,
                    "handle": next_agent_handle.lstrip("@"),
                    "name": next_agent_name or next_agent_handle,
                }
            ]
            return self.post_message(room_id, content=mention_content, mentions=mentions)

        return self.post_event(
            room_id,
            event_type="thought",
            content=band_content,
            metadata={"source": "secureflow", "agent": agent_name},
        )

    def post_agent_discussion(
        self,
        room_id: str,
        *,
        agent_name: str,
        content: str,
        reply_to_agent_name: str | None = None,
        locale: str = "fr",
    ) -> dict[str, Any]:
        """Message conversationnel — ton humain, @mention du collègue précédent."""
        label = "discussion" if locale == "en" else "discussion"
        body = f"**{agent_name} — {label}**\n\n{content.strip()}"
        text = self._truncate_for_band(body)

        if reply_to_agent_name:
            _, handle, mention = self._mention_for(reply_to_agent_name)
            if mention:
                mention_body = f"@{mention['handle']}\n\n{text}"
                return self.post_message(
                    room_id,
                    content=mention_body,
                    mentions=[mention],
                )
        return self.post_event(
            room_id,
            event_type="message",
            content=text,
            metadata={"source": "secureflow", "agent": agent_name, "kind": "discussion"},
        )

    def _post_report_message(
        self, room_id: str, *, agent_name: str, content: str
    ) -> dict[str, Any]:
        """Publie un (morceau de) rapport comme message Band, repli event si refus."""
        try:
            return self._request(
                "POST",
                f"/chats/{room_id}/messages",
                json={"message": {"content": content, "mentions": []}},
            )
        except BandAPIError as exc:
            logger.warning(
                "%s — rapport en message refusé (%s), repli sur event.", agent_name, exc
            )
            return self.post_event(
                room_id,
                event_type="thought",
                content=content,
                metadata={"source": "secureflow", "agent": agent_name, "kind": "report"},
            )

    def post_agent_report(
        self,
        room_id: str,
        *,
        agent_name: str,
        content: str,
    ) -> dict[str, Any]:
        """Rapport technique structuré — publié EN ENTIER comme message(s) Band.

        Le rapport est découpé en plusieurs messages si nécessaire (jamais tronqué).
        Chaque morceau porte l'en-tête `**Agent — rapport (i/n)**` pour que l'UI web
        le classe en « report ». Repli sur un event si l'API refuse un message.
        """
        max_chars = int(getattr(settings, "BAND_MAX_EVENT_CHARS", DEFAULT_BAND_CONTENT_LIMIT))
        # Marge pour l'en-tête « **Agent — rapport (10/10)**\n\n »
        body_limit = max(500, max_chars - len(agent_name) - 40)
        chunks = self._chunk_for_band(content.strip(), limit=body_limit) or [""]
        total = len(chunks)

        last_response: dict[str, Any] = {}
        for index, chunk in enumerate(chunks, 1):
            suffix = f" ({index}/{total})" if total > 1 else ""
            formatted = f"**{agent_name} — rapport{suffix}**\n\n{chunk}"
            last_response = self._post_report_message(
                room_id, agent_name=agent_name, content=formatted
            )
        return last_response

    def post_agent_entering(
        self,
        room_id: str,
        *,
        agent_name: str,
        locale: str = "fr",
        prior_agent_name: str | None = None,
        task_brief: str = "",
    ) -> dict[str, Any]:
        """Annonce l'entrée de l'agent dans la discussion Band (« je m'y mets »)."""
        task = task_brief.strip()
        if locale == "en":
            content = f"**{agent_name} — I'm on it**\n\n"
            if prior_agent_name:
                content += f"Picking up after {prior_agent_name}. "
            content += "Starting my part now"
            if task:
                content += f": {task}."
            else:
                content += "."
        else:
            content = f"**{agent_name} — je m'y mets**\n\n"
            if prior_agent_name:
                content += f"Je reprends après {prior_agent_name}. "
            content += "Je commence mon travail"
            if task:
                content += f" : {task}."
            else:
                content += "."
        return self.post_event(
            room_id,
            event_type="thought",
            content=content,
            metadata={"source": "secureflow", "agent": agent_name, "kind": "entering"},
        )

    def post_pass_the_ball(
        self,
        room_id: str,
        *,
        from_agent_name: str,
        to_agent_name: str,
        locale: str = "fr",
        task_brief: str = "",
    ) -> dict[str, Any]:
        """Message court de relais — « j'ai terminé, @X à toi de continuer »."""
        _, handle, mention = self._mention_for(to_agent_name)
        target = handle or to_agent_name
        task = task_brief.strip()
        if locale == "en":
            content = (
                f"**Ball passed — {from_agent_name} → {to_agent_name}**\n\n"
                f"Done on my side. @{target}, I'm passing the ball to you — "
                f"please read the Band thread and continue"
            )
            if task:
                content += f" ({task})"
            content += "."
        else:
            content = (
                f"**Relais — {from_agent_name} → {to_agent_name}**\n\n"
                f"C'est bon pour moi, j'ai terminé. @{target}, je te passe la balle — "
                f"relis le fil et continue"
            )
            if task:
                content += f" ({task})"
            content += "."
        if mention:
            body = f"@{mention['handle']}\n\n{content}"
            return self.post_message(room_id, content=body, mentions=[mention])
        return self.post_message(room_id, content=content, mentions=[])

    def post_agent_wrap_up(
        self,
        room_id: str,
        *,
        agent_name: str,
        locale: str = "fr",
        message: str = "",
    ) -> dict[str, Any]:
        """Clôture du tour de l'agent quand il n'y a pas de successeur immédiat."""
        custom = message.strip()
        if locale == "en":
            content = custom or (
                f"**{agent_name} — done for now**\n\n"
                "My part is complete. The team can proceed to the next phase."
            )
        else:
            content = custom or (
                f"**{agent_name} — terminé pour moi**\n\n"
                "Mon travail est fait. L'équipe peut passer à la suite."
            )
        return self.post_event(
            room_id,
            event_type="thought",
            content=content,
            metadata={"source": "secureflow", "agent": agent_name, "kind": "wrap_up"},
        )

    def post_handoff(
        self,
        room_id: str,
        *,
        from_agent_name: str,
        to_agent_name: str,
        summary: str = "",
        locale: str = "fr",
    ) -> dict[str, Any]:
        """Alias — relais court vers l'agent suivant (@mention)."""
        _ = summary  # le rapport est déjà dans le fil ; pas de duplication
        return self.post_pass_the_ball(
            room_id,
            from_agent_name=from_agent_name,
            to_agent_name=to_agent_name,
            locale=locale,
        )

    def seed_room(
        self,
        room_id: str,
        initial_content: str,
        label: str = "Projet",
        *,
        locale: str = "fr",
    ) -> dict[str, Any]:
        """
        Dépose le contenu initial dans la Band Room (plusieurs events si nécessaire).
        Les agents suivants lisent cet historique via get_context().
        """
        chunks = self._chunk_for_band(initial_content)
        lang = (locale or "fr").lower()[:2]
        try:
            if not chunks:
                empty = "(empty content)" if lang == "en" else "(contenu vide)"
                return self.post_event(
                    room_id,
                    event_type="task",
                    content=f"**{label}** — {empty}",
                    metadata={"source": "secureflow", "kind": "initial_input"},
                )

            last_response: dict[str, Any] = {}
            total = len(chunks)
            for index, chunk in enumerate(chunks, start=1):
                if lang == "en":
                    header = f"**{label} — initial content ({index}/{total})**"
                else:
                    header = f"**{label} — contenu initial ({index}/{total})**"
                content = f"{header}\n\n{chunk}"
                last_response = self.post_event(
                    room_id,
                    event_type="task",
                    content=content,
                    metadata={
                        "source": "secureflow",
                        "kind": "initial_input",
                        "chunk": index,
                        "chunks_total": total,
                        "original_length": len(initial_content.strip()),
                    },
                )
            return last_response
        except BandAPIError as exc:
            logger.warning("seed_room ignoré (Band indisponible ou refusé): %s", exc)
            return {}

    def _mention_for(self, agent_name: str) -> tuple[str, str, dict[str, Any]] | tuple[None, None, None]:
        from apps.agents.band_registry import load_credentials, resolve_handle

        creds = load_credentials(agent_name)
        handle = resolve_handle(agent_name) or creds.handle
        if not creds.agent_id or not handle:
            return None, None, None
        handle = handle.lstrip("@")
        mention = {
            "id": creds.agent_id,
            "handle": handle,
            "name": agent_name,
        }
        return creds.agent_id, handle, mention

    def post_human_review_request(
        self,
        room_id: str,
        *,
        reason: str,
        locale: str = "fr",
        target_agent_name: str = "DecisionAgent",
    ) -> dict[str, Any]:
        """Demande validation humaine — réponse attendue DANS le fil Band (APPROVE / REJECT)."""
        _, handle, mention = self._mention_for(target_agent_name)
        if locale == "en":
            content = (
                "**HUMAN VALIDATION REQUIRED — reply in this Band thread**\n\n"
                f"{reason.strip()}\n\n"
                "Operator: type **APPROVE** to start remediation (DevAgent patch) "
                "or **REJECT** to abort.\n\n"
                "This message is the coordination gate — SecureFlow resumes only after "
                "your reply appears here."
            )
        else:
            content = (
                "**VALIDATION HUMAINE — répondez dans ce fil Band**\n\n"
                f"{reason.strip()}\n\n"
                "Opérateur : tapez **APPROUVE** pour lancer la remédiation (patch DevAgent) "
                "ou **REJETE** pour annuler.\n\n"
                "Ce message est le verrou de coordination — SecureFlow reprend uniquement "
                "quand votre réponse apparaît ici."
            )
        if mention:
            body = f"@{mention['handle']}\n\n{content}"
            return self.post_message(room_id, content=body, mentions=[mention])
        return self.post_message(room_id, content=content, mentions=[])

    def post_human_decision(
        self,
        room_id: str,
        *,
        action: str,
        comment: str = "",
        locale: str = "fr",
    ) -> dict[str, Any]:
        """Décision humaine publiée comme message Band (visible par tous les agents)."""
        label = "Human operator" if locale == "en" else "Opérateur humain"
        verb = "APPROVE" if action.lower() in ("proceed", "approve", "approved") else "REJECT"
        if locale == "fr" and verb == "APPROVE":
            verb = "APPROUVE"
        if locale == "fr" and verb == "REJECT":
            verb = "REJETE"
        body = f"**{label} — {verb}**"
        if comment.strip():
            body = f"{body}\n\n{comment.strip()}"
        return self.post_message(room_id, content=body, mentions=[])

    def post_escalation(
        self,
        room_id: str,
        *,
        from_agent: str,
        message: str,
        target_agent_id: str | None = None,
        target_handle: str | None = None,
        target_name: str | None = None,
    ) -> dict[str, Any]:
        """Escalade non linéaire — ex. Threat demande un second passage Scanner."""
        content = f"**ESCALADE — {from_agent}**\n\n{message.strip()}"
        if target_agent_id and target_handle:
            mention = f"@{target_handle.lstrip('@')}\n\n{content}"
            return self.post_message(
                room_id,
                content=mention,
                mentions=[
                    {
                        "id": target_agent_id,
                        "handle": target_handle.lstrip("@"),
                        "name": target_name or target_handle,
                    }
                ],
            )
        return self.post_event(
            room_id,
            event_type="task",
            content=content,
            metadata={"source": "secureflow", "kind": "escalation", "from": from_agent},
        )

    def post_recruitment(
        self,
        room_id: str,
        *,
        recruited_agent_name: str,
        reason: str,
        locale: str = "fr",
        from_agent_name: str = "ThreatAgent",
    ) -> dict[str, Any]:
        """Recrutement dynamique — message @mention dans le fil Band (pas un event caché)."""
        _, handle, mention = self._mention_for(recruited_agent_name)
        if locale == "en":
            content = (
                f"**Dynamic recruitment — {recruited_agent_name}**\n\n"
                f"{from_agent_name}: we need you on this thread.\n\n"
                f"{reason.strip()}\n\n"
                f"@{handle or recruited_agent_name} — I'm handing off to you, "
                f"please join the discussion and respond."
            )
        else:
            content = (
                f"**Recrutement dynamique — {recruited_agent_name}**\n\n"
                f"{from_agent_name} : j'ai besoin de toi sur ce fil.\n\n"
                f"{reason.strip()}\n\n"
                f"@{handle or recruited_agent_name} — je te passe la balle, "
                f"rejoins la discussion et réponds."
            )
        if mention:
            body = f"@{mention['handle']}\n\n{content}"
            return self.post_message(room_id, content=body, mentions=[mention])
        return self.post_message(room_id, content=content, mentions=[])

    def post_disagreement(
        self,
        room_id: str,
        *,
        disagreement: dict[str, Any],
        locale: str = "fr",
        decision_agent_name: str = "DecisionAgent",
    ) -> dict[str, Any]:
        """Désaccord visible — @mention DecisionAgent dans le fil Band."""
        scores = disagreement.get("scores") or {}
        lines = [f"- {agent}: {score}/10" for agent, score in scores.items()]
        score_block = "\n".join(lines)
        _, handle, mention = self._mention_for(decision_agent_name)
        if locale == "en":
            content = (
                "**DISAGREEMENT DETECTED**\n\n"
                f"{score_block}\n\n"
                f"Spread ≥ 3 points — @{handle or 'DecisionAgent'} must rule and justify "
                "which signal takes precedence."
            )
        else:
            content = (
                "**DÉSACCORD DÉTECTÉ**\n\n"
                f"{score_block}\n\n"
                f"Écart ≥ 3 points — @{handle or 'DecisionAgent'} doit trancher et justifier "
                "quel signal prime."
            )
        if mention:
            body = f"@{mention['handle']}\n\n{content}"
            return self.post_message(room_id, content=body, mentions=[mention])
        return self.post_message(room_id, content=content, mentions=[])


class BandAPIError(Exception):
    """Erreur remontée par l'API Band."""
