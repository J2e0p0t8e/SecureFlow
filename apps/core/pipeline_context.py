"""Contexte d'exécution d'un pipeline (warnings, ingestion) — thread-safe."""

from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any

logger = logging.getLogger(__name__)

_ingestion_meta: ContextVar[dict[str, Any] | None] = ContextVar("ingestion_meta", default=None)
_workflow_mode: ContextVar[str | None] = ContextVar("workflow_mode", default=None)
_locale: ContextVar[str | None] = ContextVar("locale", default=None)


_disagreement: ContextVar[dict[str, Any] | None] = ContextVar("disagreement", default=None)
_pipeline_phase: ContextVar[str | None] = ContextVar("pipeline_phase", default=None)
_static_signal: ContextVar[dict[str, Any] | None] = ContextVar("static_signal", default=None)


def init_pipeline_context(
    ingestion_meta: dict[str, Any] | None = None,
    *,
    workflow_mode: str | None = None,
    locale: str | None = None,
) -> None:
    from apps.core.locale import normalize_locale

    _ingestion_meta.set(dict(ingestion_meta or {}))
    _workflow_mode.set((workflow_mode or "A").upper())
    _locale.set(normalize_locale(locale))


def add_warning(message: str) -> None:
    """Journalise une notice interne — jamais exposée à l'utilisateur final."""
    if message:
        logger.info("Pipeline (internal): %s", message)


def collect_warnings() -> list[str]:
    """Les avertissements techniques ne sont pas affichés dans l'UI."""
    return []


def get_ingestion_meta() -> dict[str, Any]:
    return dict(_ingestion_meta.get() or {})


def get_workflow_mode() -> str | None:
    return _workflow_mode.get()


def get_locale() -> str:
    from apps.core.locale import normalize_locale

    return normalize_locale(_locale.get())


def set_disagreement_context(data: dict[str, Any] | None) -> None:
    _disagreement.set(dict(data) if data else None)


def get_disagreement_context() -> dict[str, Any] | None:
    value = _disagreement.get()
    return dict(value) if value else None


def set_pipeline_phase(phase: str | None) -> None:
    _pipeline_phase.set(phase)


def get_pipeline_phase() -> str | None:
    return _pipeline_phase.get()


def set_static_signal(data: dict[str, Any] | None) -> None:
    """Stocke le résumé d'analyse statique (regex + Bandit) pour le cross-check."""
    _static_signal.set(dict(data) if data else None)


def get_static_signal() -> dict[str, Any] | None:
    value = _static_signal.get()
    return dict(value) if value else None
