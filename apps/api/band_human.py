"""Détection des décisions humaines publiées dans la Band Room."""

from __future__ import annotations

import re
from typing import Any

from apps.agents.band_registry import ALL_BAND_AGENT_NAMES, load_credentials

_APPROVE_RE = re.compile(
    r"\b(APPROVE|APPROUVE|APPROUVÉ|APPROUVEE|CONFIRMER|PROCEED|OUI|YES|GO)\b",
    re.IGNORECASE,
)
_REJECT_RE = re.compile(
    r"\b(REJECT|REJETE|REJETÉ|REJETEE|ANNULER|ABORT|NON|NO|STOP)\b",
    re.IGNORECASE,
)


def _known_agent_ids() -> set[str]:
    ids: set[str] = set()
    for name in ALL_BAND_AGENT_NAMES:
        try:
            creds = load_credentials(name)
            if creds.agent_id:
                ids.add(creds.agent_id)
        except KeyError:
            continue
    return ids


def _sender_id(msg: dict[str, Any]) -> str:
    sender = msg.get("sender")
    if isinstance(sender, dict):
        for key in ("id", "agent_id", "participant_id"):
            value = sender.get(key)
            if value:
                return str(value)
    for key in ("sender_id", "author_id", "participant_id"):
        value = msg.get(key)
        if value:
            return str(value)
    return ""


def _sender_label(msg: dict[str, Any]) -> str:
    sender = msg.get("sender")
    if isinstance(sender, dict):
        return str(
            sender.get("name") or sender.get("handle") or sender.get("display_name") or ""
        )
    return str(msg.get("sender_name") or msg.get("author") or "")


def _message_text(msg: dict[str, Any]) -> str:
    return (msg.get("content") or msg.get("body") or "").strip()


def parse_human_decision_from_messages(
    messages: list[dict[str, Any]],
    *,
    skip_agent_ids: set[str] | None = None,
    min_index: int = 0,
) -> tuple[str, str] | None:
    """
    Cherche une réponse humaine APPROVE/REJECT dans le fil Band.
    Retourne (action, comment) avec action in ('proceed', 'abort') ou None.
    """
    agent_ids = skip_agent_ids or _known_agent_ids()

    for msg in messages[min_index:]:
        if not isinstance(msg, dict):
            continue

        metadata = msg.get("metadata") or {}
        if isinstance(metadata, dict) and metadata.get("kind") == "human_decision":
            action = str(metadata.get("action", "")).lower()
            comment = _message_text(msg)
            if action in ("proceed", "approve", "approved", "proceed"):
                return "proceed", comment
            if action in ("abort", "reject", "rejected", "cancel"):
                return "abort", comment

        sender_id = _sender_id(msg)
        text = _message_text(msg)
        is_human_proxy = "Opérateur humain" in text or "Human operator" in text

        if sender_id and sender_id in agent_ids and not is_human_proxy:
            continue

        if not text:
            continue

        if _REJECT_RE.search(text):
            return "abort", text
        if _APPROVE_RE.search(text):
            return "proceed", text

    return None


def band_room_web_url(room_id: str) -> str:
    from django.conf import settings

    template = getattr(
        settings,
        "BAND_ROOM_URL_TEMPLATE",
        "{base}/chat/{room_id}",
    )
    base = getattr(settings, "BAND_WEB_APP_URL", settings.BAND_BASE_URL).rstrip("/")
    return template.format(base=base, room_id=room_id)
