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
        mentions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Envoie un message texte avec @mentions (collaboration multi-agents Band)."""
        return self._request(
            "POST",
            f"/chats/{room_id}/messages",
            json={"message": {"content": content, "mentions": mentions}},
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
        unwrapped = self._unwrap(data)
        messages = (
            unwrapped.get("messages")
            or data.get("messages")
            or data.get("context")
            or unwrapped
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
                "content": content,
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

        if next_agent_id and next_agent_handle:
            mention_content = f"@{next_agent_handle.lstrip('@')}\n\n{formatted}"
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
            event_type=event_type,
            content=formatted,
            metadata={"agent": agent_name, "source": "secureflow"},
        )

    def seed_room(self, room_id: str, initial_content: str, label: str = "Projet") -> dict[str, Any]:
        """
        Dépose le contenu initial (projet, description utilisateur) dans la Room
        avant le passage du premier agent.
        """
        content = f"**{label} — contenu initial**\n\n{initial_content.strip()}"
        return self.post_event(
            room_id,
            event_type="task",
            content=content,
            metadata={"source": "secureflow", "kind": "initial_input"},
        )


class BandAPIError(Exception):
    """Erreur remontée par l'API Band."""
