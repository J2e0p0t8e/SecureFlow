"""Exécution asynchrone des analyses (thread background)."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import requests

from apps.agents.base import AgentResult
from apps.core.locale import normalize_locale
from apps.api.band_human import parse_human_decision_from_messages
from apps.api.band_messages import fetch_merged_room_messages
from apps.orchestrator.exceptions import HumanReviewRequired
from apps.orchestrator.services import run_security_audit

logger = logging.getLogger(__name__)


def _fetch_github_with_retry(github_url: str, *, max_files: int, session_id: int, attempts: int = 2):
    """Ingestion GitHub avec un retry sur erreur réseau transitoire.

    Les erreurs métier (ValueError : URL/branche/token) ne sont PAS réessayées.
    """
    from apps.ingestion.github import fetch_github_project

    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fetch_github_project(github_url, max_files=max_files)
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning(
                "GitHub ingestion transient error (session %s, essai %s/%s): %s",
                session_id,
                attempt,
                attempts,
                exc,
            )
            if attempt < attempts:
                time.sleep(1.5 * attempt)
    raise last_exc if last_exc else requests.RequestException("GitHub ingestion failed")


def _agent_results_from_dicts(items: list[dict[str, str]], room_id: str) -> list[AgentResult]:
    return [
        AgentResult(
            agent_name=item.get("name", "Agent"),
            room_id=room_id,
            content=item.get("content", ""),
        )
        for item in items
    ]


def _merge_progress(partial: dict, payload: dict, *, mode: str, lang: str, meta: dict) -> None:
    partial["mode"] = mode
    partial["locale"] = lang
    partial.setdefault("ingestion", meta)
    if payload.get("workflow_phase"):
        partial["phase"] = payload["workflow_phase"]
    if payload.get("recruited_agents"):
        partial["recruited_agents"] = payload["recruited_agents"]
        partial["pipeline_agents"] = payload.get("agents") and [
            a.get("name") for a in payload["agents"]
        ]
    if payload.get("phase") == "started":
        partial["active_agent"] = payload.get("agent")
    elif payload.get("phase") == "completed" or payload.get("agents"):
        partial["agents"] = payload.get("agents", [])
        partial["active_agent"] = payload.get("next_agent")
        if payload.get("escalation"):
            partial["last_escalation"] = payload["escalation"]


def _finalize_session(session_id: int, result, start_time: float, mode: str) -> None:
    from apps.api.models import AnalysisSession

    duration = int(time.time() - start_time)
    result_dict = result.to_dict()
    AnalysisSession.objects.filter(pk=session_id).update(
        room_id=result.room_id,
        audit_id=(result_dict.get("audit_id") or "")[:50],
        decision=(result_dict.get("decision") or "")[:20],
        final_report=result_dict.get("final_report") or "",
        result_json=result_dict,
        status="completed",
        duration_seconds=duration,
        error_message="",
    )


def _store_human_review_pending(session_id: int, pending, mode: str, start_time: float) -> None:
    from apps.api.models import AnalysisSession

    partial = {
        "mode": mode,
        "product": "audit-to-fix",
        "locale": pending.locale,
        "room_id": pending.room_id,
        "phase": "awaiting_human_approval",
        "agents": pending.results_as_dicts(),
        "pipeline_agents": [a["name"] for a in pending.results_as_dicts()],
        "ingestion": pending.ingestion_meta or {},
        "human_review": {
            "required": True,
            "reason": pending.reason,
            "review_kind": pending.review_kind,
            "branch": pending.branch,
            "decision": pending.decision,
        },
        "_pipeline": {
            "project_content": pending.project_content,
            "project_label": pending.project_label,
            "room_id": pending.room_id,
            "ingestion_meta": pending.ingestion_meta or {},
            "locale": pending.locale,
            "results": pending.results_as_dicts(),
            "recruited_agents": [a["name"] for a in pending.results_as_dicts()],
            "resume_branch": pending.branch,
            "review_kind": pending.review_kind,
            "decision": pending.decision,
            "started_at": start_time,
            "band_message_count": _band_message_count(pending.room_id),
        },
    }
    AnalysisSession.objects.filter(pk=session_id).update(
        room_id=pending.room_id,
        status="awaiting_human",
        decision=(pending.decision or "")[:20],
        result_json=partial,
        duration_seconds=int(time.time() - start_time),
    )
    start_band_human_poll(session_id, pending.room_id, pending.locale)


def _band_message_count(room_id: str) -> int:
    try:
        return len(fetch_merged_room_messages(room_id, mode="A"))
    except Exception:
        return 0


def start_band_human_poll(session_id: int, room_id: str, locale: str) -> None:
    """Reprend le pipeline quand l'opérateur répond APPROUVE/REJETE dans la Band Room."""

    def poll() -> None:
        from apps.api.models import AnalysisSession

        min_index = 0
        try:
            session = AnalysisSession.objects.get(pk=session_id)
            pipeline = (session.result_json or {}).get("_pipeline") or {}
            min_index = int(pipeline.get("band_message_count") or 0)
        except AnalysisSession.DoesNotExist:
            return

        while True:
            try:
                session = AnalysisSession.objects.get(pk=session_id)
            except AnalysisSession.DoesNotExist:
                return
            if session.status != "awaiting_human":
                return

            try:
                messages = fetch_merged_room_messages(room_id, mode="A")
                parsed = parse_human_decision_from_messages(messages, min_index=min_index)
                if parsed:
                    action, comment = parsed
                    resume_after_human_review(session_id, action=action, comment=comment)
                    return
            except Exception as exc:
                logger.debug("Band human poll: %s", exc)

            time.sleep(4)

    threading.Thread(target=poll, daemon=True).start()


def start_analysis_thread(
    session_id: int,
    mode: str,
    label: str,
    *,
    project_content: str | None = None,
    github_url: str | None = None,
    ingestion_meta: dict[str, Any] | None = None,
    locale: str | None = None,
) -> None:
    """Lance l'orchestrateur en arrière-plan et met à jour la session."""

    def worker() -> None:
        from apps.api.models import AnalysisSession
        from apps.core.config import get_ingestion_max_files
        from apps.orchestrator.services import run_security_audit

        runners = {
            "A": run_security_audit,
        }

        lang = normalize_locale(locale or (ingestion_meta or {}).get("locale"))
        mode = "A"

        try:
            runner = runners[mode]
            meta = dict(ingestion_meta or {})
            meta["locale"] = lang
            content = (project_content or "").strip()

            if github_url:
                AnalysisSession.objects.filter(pk=session_id).update(
                    status="running",
                    result_json={
                        "mode": mode,
                        "locale": lang,
                        "phase": "ingesting",
                        "agents": [],
                        "active_agent": None,
                        "ingestion": meta,
                    },
                )
                try:
                    ingestion = _fetch_github_with_retry(
                        github_url,
                        max_files=get_ingestion_max_files(mode),
                        session_id=session_id,
                    )
                    content = ingestion.content
                    meta.update(ingestion.to_dict(locale=lang))
                except ValueError as exc:
                    AnalysisSession.objects.filter(pk=session_id).update(
                        status="failed",
                        error_message=str(exc)[:2000],
                    )
                    return
                except requests.RequestException:
                    logger.exception("GitHub ingestion failed for session %s", session_id)
                    AnalysisSession.objects.filter(pk=session_id).update(
                        status="failed",
                        error_message=(
                            "Impossible de contacter GitHub (réseau ou timeout). "
                            "Ajoutez GITHUB_TOKEN dans .env ou collez le code directement."
                        )[:2000],
                    )
                    return

            if not content:
                AnalysisSession.objects.filter(pk=session_id).update(
                    status="failed",
                    error_message="Contenu projet vide après ingestion.",
                )
                return

            def on_room_created(room_id: str) -> None:
                AnalysisSession.objects.filter(pk=session_id).update(
                    room_id=room_id,
                    status="running",
                    result_json={
                        "mode": mode,
                        "product": "audit-to-fix" if mode == "A" else None,
                        "locale": lang,
                        "phase": "scanning",
                        "agents": [],
                        "active_agent": None,
                        "ingestion": meta,
                    },
                )

            def on_progress(payload: dict) -> None:
                session = AnalysisSession.objects.get(pk=session_id)
                partial = dict(session.result_json or {})
                _merge_progress(partial, payload, mode=mode, lang=lang, meta=meta)
                AnalysisSession.objects.filter(pk=session_id).update(result_json=partial)

            start = time.time()
            try:
                result = runner(
                    content,
                    project_label=label,
                    on_room_created=on_room_created,
                    on_progress=on_progress,
                    ingestion_meta=meta,
                    locale=lang,
                )
                _finalize_session(session_id, result, start, mode)
            except HumanReviewRequired as gate:
                _store_human_review_pending(session_id, gate.pending, mode, start)
        except Exception as exc:
            logger.exception("Analysis failed for session %s", session_id)
            from apps.core.locale import api_message
            from django.conf import settings

            user_message = api_message("analysis_failed", lang)
            detail = str(exc)[:500]
            if settings.DEBUG:
                user_message = f"{user_message} ({detail})"
            AnalysisSession.objects.filter(pk=session_id).update(
                status="failed",
                error_message=user_message[:2000],
            )

    threading.Thread(target=worker, daemon=True).start()


def resume_after_human_review(
    session_id: int,
    *,
    action: str,
    comment: str = "",
) -> None:
    """Reprend ou annule le pipeline après validation humaine (remédiation Mode A)."""

    def worker() -> None:
        from apps.api.models import AnalysisSession
        from apps.agents.band_registry import get_band_client_for

        session = AnalysisSession.objects.get(pk=session_id)
        if session.status != "awaiting_human":
            return

        pipeline = (session.result_json or {}).get("_pipeline") or {}
        room_id = pipeline.get("room_id") or session.room_id
        locale = normalize_locale(pipeline.get("locale") or session.result_json.get("locale"))
        lang = locale

        lead_band = get_band_client_for("ScannerAgent")
        try:
            lead_band.post_human_decision(
                room_id,
                action=action,
                comment=comment,
                locale=lang,
            )
        except Exception as exc:
            logger.warning("post_human_decision: %s", exc)

        start = time.time()
        started_at = pipeline.get("started_at") or start

        if action.lower() in ("abort", "cancel", "annuler", "non", "reject", "rejected"):
            partial = dict(session.result_json or {})
            partial["decision"] = partial.get("decision") or session.decision
            partial["phase"] = "done"
            partial["branch"] = "aborted"
            partial["human_review"] = {
                "action": action,
                "comment": comment,
                "completed": True,
            }
            AnalysisSession.objects.filter(pk=session_id).update(
                status="completed",
                final_report=comment or partial.get("decision", ""),
                result_json=partial,
                duration_seconds=int(time.time() - started_at),
            )
            return

        prior = _agent_results_from_dicts(pipeline.get("results") or [], room_id)
        meta = dict(pipeline.get("ingestion_meta") or {})
        meta["_recruited"] = pipeline.get("recruited_agents") or []

        def on_progress(payload: dict) -> None:
            session_ref = AnalysisSession.objects.get(pk=session_id)
            partial = dict(session_ref.result_json or {})
            _merge_progress(partial, payload, mode="A", lang=lang, meta=meta)
            partial["status_running"] = True
            AnalysisSession.objects.filter(pk=session_id).update(
                status="running",
                result_json=partial,
            )

        AnalysisSession.objects.filter(pk=session_id).update(status="running")

        try:
            result = run_security_audit(
                pipeline.get("project_content", ""),
                project_label=pipeline.get("project_label", "Projet"),
                on_progress=on_progress,
                ingestion_meta=meta,
                locale=lang,
                existing_results=prior,
                existing_room_id=room_id,
                skip_human_gate=True,
                resume_branch=pipeline.get("resume_branch", "remediation"),
            )
            result_dict = result.to_dict()
            result_dict["human_review"] = {
                "action": action,
                "comment": comment,
                "completed": True,
            }
            AnalysisSession.objects.filter(pk=session_id).update(
                room_id=result.room_id,
                audit_id=(result_dict.get("audit_id") or "")[:50],
                decision=(result_dict.get("decision") or "")[:20],
                final_report=result_dict.get("final_report") or "",
                result_json=result_dict,
                status="completed",
                duration_seconds=int(time.time() - started_at),
            )
        except Exception as exc:
            logger.exception("Resume after human review failed for session %s", session_id)
            from apps.core.locale import api_message

            AnalysisSession.objects.filter(pk=session_id).update(
                status="failed",
                error_message=api_message("analysis_failed", lang)[:2000],
            )

    threading.Thread(target=worker, daemon=True).start()
