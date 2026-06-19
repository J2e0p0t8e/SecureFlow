"""Helpers pour formater les messages Band Room côté API."""

from __future__ import annotations

import hashlib
import re
from typing import Any

_MENTION_RE = re.compile(r"@([\w./-]+)")
_MENTION_UUID_RE = re.compile(r"@\[\[[^\]]+\]\]\s*")
_AGENT_HEADER_RE = re.compile(r"^\*\*(.+?)\*\*\s*[—-]?\s*", re.MULTILINE)
_HANDOFF_RE = re.compile(
    r"^\*\*(?:Relais|Passage de relais|Ball passed|Handoff)\s*[—-]\s*(.+?)\*\*",
    re.MULTILINE | re.IGNORECASE,
)
_ENTERING_RE = re.compile(
    r"^\*\*(.+?)\s*[—-]\s*(?:je m'y mets|I'm on it|discussion|rapport|report)\*\*",
    re.MULTILINE | re.IGNORECASE,
)
_DISCUSSION_HEADER_RE = re.compile(
    r"^\*\*(.+?)\s*[—-]\s*discussion\*\*",
    re.MULTILINE | re.IGNORECASE,
)
_REPORT_HEADER_RE = re.compile(
    r"^\*\*(.+?)\s*[—-]\s*(?:rapport|report)(?:\s*\(\d+\s*/\s*\d+\))?\*\*",
    re.MULTILINE | re.IGNORECASE,
)
_COORD_HEADER_RE = re.compile(
    r"^\*\*(?:Recrutement dynamique|Dynamic recruitment|"
    r"DÉSACCORD DÉTECTÉ|DISAGREEMENT DETECTED|ESCALADE)\s*[—-]\s*.+?\*\*",
    re.MULTILINE | re.IGNORECASE,
)
_DISAGREE_RE = re.compile(
    r"\*\*(?:DÉSACCORD DÉTECTÉ|DISAGREEMENT DETECTED)\*\*",
    re.IGNORECASE,
)
_AGENT_ARROW_RE = re.compile(r"^([A-Za-z]+Agent)\s*(?:→|:)", re.MULTILINE)


def _extract_mentions(content: str, raw_mentions: list[Any]) -> list[str]:
    mentions: list[str] = []
    for mention in raw_mentions:
        if isinstance(mention, dict):
            label = mention.get("name") or mention.get("handle") or mention.get("id")
            if label:
                mentions.append(str(label).lstrip("@"))
        elif isinstance(mention, str):
            mentions.append(mention.lstrip("@"))

    for handle in _MENTION_RE.findall(content):
        if handle not in mentions:
            mentions.append(handle)

    return mentions


def format_messages_for_ui(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Transforme les messages Band bruts en format lisible pour le frontend."""
    formatted: list[dict[str, Any]] = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        metadata = msg.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        content = (msg.get("content") or msg.get("body") or "").strip()
        if not content:
            continue

        content = _MENTION_UUID_RE.sub("", content).strip()

        author = msg.get("sender_name") or msg.get("author") or "Agent"
        sender = msg.get("sender")
        if isinstance(sender, dict):
            author = msg.get("sender_name") or sender.get("name") or sender.get("handle") or author

        role = ""
        if isinstance(sender, dict):
            role = sender.get("role") or sender.get("type") or ""

        raw_content = content
        entering_match = _ENTERING_RE.search(raw_content)
        discussion_match = _DISCUSSION_HEADER_RE.search(raw_content)
        report_match = _REPORT_HEADER_RE.search(raw_content)
        handoff_match = _HANDOFF_RE.search(raw_content)
        disagree_match = _DISAGREE_RE.search(raw_content)
        if metadata.get("kind") == "discussion" or discussion_match:
            if discussion_match:
                author = discussion_match.group(1).strip()
            content = _DISCUSSION_HEADER_RE.sub("", content, count=1).strip()
        elif metadata.get("kind") == "report" or report_match:
            if report_match:
                author = report_match.group(1).strip()
            content = _REPORT_HEADER_RE.sub("", content, count=1).strip()
        elif entering_match:
            author = entering_match.group(1).strip()
            content = _ENTERING_RE.sub("", content, count=1).strip()
        elif handoff_match:
            author = handoff_match.group(1).strip().split("→")[0].strip()
            content = _HANDOFF_RE.sub("", content, count=1).strip()
        elif _COORD_HEADER_RE.search(raw_content):
            arrow = _AGENT_ARROW_RE.search(raw_content)
            if arrow:
                author = arrow.group(1).strip()
            content = _COORD_HEADER_RE.sub("", content, count=1).strip()
        else:
            header_match = _AGENT_HEADER_RE.match(content)
            if header_match:
                author = header_match.group(1).strip()
                content = _AGENT_HEADER_RE.sub("", content, count=1).strip()
            elif metadata.get("source") == "secureflow" and metadata.get("agent"):
                author = str(metadata["agent"])

        if metadata.get("kind") == "initial_input":
            author = "Entrée utilisateur"
            if not handoff_match and not entering_match:
                content = content or raw_content.split("\n\n", 1)[-1].strip()

        role = role or metadata.get("role") or ""
        if metadata.get("agent") and author == "Orchestrateur":
            role = metadata.get("agent")

        msg_type = msg.get("message_type") or msg.get("type") or "message"
        raw_mentions = list(msg.get("mentions") or [])
        raw_mentions.extend(metadata.get("mentions") or [])
        mentions = _extract_mentions(content, raw_mentions)

        formatted.append(
            {
                "id": msg.get("id"),
                "author": author,
                "role": role,
                "content": content,
                "type": msg_type,
                "mentions": mentions,
                "kind": "disagreement" if disagree_match else (metadata.get("kind") or (
                    "discussion"
                    if discussion_match or metadata.get("kind") == "discussion"
                    else "report"
                    if report_match or metadata.get("kind") == "report"
                    else ""
                )),
            }
        )

    return formatted


def is_pending_room_id(room_id: str | None) -> bool:
    return not room_id or room_id.startswith("pending-")


_MODE_AGENTS: dict[str, list[str]] = {}


def _mode_agent_names(mode: str | None) -> list[str]:
    from apps.orchestrator.mode_a import MODE_A_BAND_AGENTS

    return MODE_A_BAND_AGENTS


def _message_dedup_key(msg: dict[str, Any]) -> str:
    msg_id = msg.get("id")
    if msg_id:
        return f"id:{msg_id}"
    content = (msg.get("content") or msg.get("body") or "").strip()
    digest = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()[:24]
    return f"hash:{digest}"


def fetch_merged_room_messages(
    room_id: str,
    *,
    mode: str | None = None,
    page_size: int = 200,
) -> list[dict[str, Any]]:
    """Agrège le contexte Band de tous les agents du pipeline (vue complète)."""
    from apps.agents.band_registry import get_band_client_for

    merged: dict[str, dict[str, Any]] = {}
    for agent_name in _mode_agent_names(mode):
        try:
            client = get_band_client_for(agent_name)
            for msg in client.get_context(room_id, page_size=page_size):
                if not isinstance(msg, dict):
                    continue
                key = _message_dedup_key(msg)
                merged[key] = msg
        except Exception:
            continue

    messages = list(merged.values())
    messages.sort(key=lambda m: m.get("inserted_at") or m.get("created_at") or "")
    return messages
