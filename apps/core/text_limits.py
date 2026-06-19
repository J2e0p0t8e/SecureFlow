"""Limites de taille pour ingestion et prompts LLM."""

from __future__ import annotations

from django.conf import settings


def truncate_text(text: str, max_chars: int | None = None, *, label: str = "") -> str:
    limit = max_chars or getattr(settings, "LLM_MAX_PROMPT_CHARS", 14_000)
    cleaned = (text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    suffix = f"\n\n[… tronqué — {len(cleaned):,} caractères"
    if label:
        suffix += f" dans {label}"
    suffix += "]"
    return cleaned[:limit] + suffix
