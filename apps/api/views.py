"""
Vues API pour SecureFlow AI.
Backend ingestion (P2) + PDF download (P5).
"""

import json
import logging
import re
import time
import uuid
from typing import Any, Callable

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.api.analysis_worker import resume_after_human_review, start_analysis_thread
from apps.api.auth import check_api_key
from apps.api.band_human import band_room_web_url
from apps.api.band_messages import (
    fetch_merged_room_messages,
    format_messages_for_ui,
    is_pending_room_id,
)
from apps.api.models import AnalysisSession
from apps.api.html_report import render_report_html
from apps.api.pdf_generator import generate_audit_pdf, generate_mode_c_pdf
from apps.api.project_bundle import build_mode_b_zip
from apps.api.report_data import build_executive_summary, extract_report_context, format_disagreement
from apps.core.config import get_ingestion_max_files
from apps.core.locale import api_message, normalize_locale, pdf_decision_label
from apps.ingestion.github import fetch_github_project, is_valid_github_url
from apps.ingestion.types import IngestionResult
from apps.ingestion.zip_loader import extract_zip_project, validate_zip_file
from apps.orchestrator.services import run_security_audit_json

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = getattr(settings, "INGESTION_MAX_UPLOAD_BYTES", 20 * 1024 * 1024)

_MODE_RUNNERS: dict[str, Callable[..., dict]] = {
    "A": run_security_audit_json,
}


def _extract_locale(request, body: dict, *, multipart: bool) -> str:
    if multipart:
        return normalize_locale(request.POST.get("locale"))
    return normalize_locale(body.get("locale"))


def _prepare_project_content(*, content: str) -> str:
    return content


def _ingest_project(
    *,
    mode: str,
    input_type: str,
    body: dict,
    file_bytes: bytes | None,
) -> tuple[IngestionResult, str]:
    """Retourne (IngestionResult, input_source)."""
    max_files = get_ingestion_max_files(mode)

    if input_type == "github":
        github_url = body.get("github_url")
        if not github_url:
            raise ValueError("github_url manquant")
        if not is_valid_github_url(github_url):
            raise ValueError("URL GitHub invalide")
        result = fetch_github_project(github_url, max_files=max_files)
        return result, github_url

    if input_type == "zip":
        if file_bytes is None:
            raise ValueError(
                "ZIP requis en multipart/form-data (mode, input_type=zip, label, file)"
            )
        result = extract_zip_project(file_bytes, max_files=max_files)
        return result, "ZIP upload"

    if input_type == "text":
        content = body.get("content")
        if not content:
            raise ValueError("content manquant")
        return IngestionResult(content=content, source_label="text:paste"), "Code collé"

    raise ValueError(f"input_type invalide : {input_type!r}")


def _save_session_and_respond(
    *,
    mode: str,
    input_type: str,
    input_source: str,
    label: str,
    result: dict,
    duration: int,
) -> JsonResponse:
    session = AnalysisSession.objects.create(
        mode=mode,
        room_id=result.get("room_id") or str(uuid.uuid4()),
        audit_id=(result.get("audit_id") or "")[:50],
        input_type=input_type,
        input_source=input_source,
        project_label=label,
        decision=(result.get("decision") or "")[:20],
        final_report=result.get("final_report", ""),
        result_json=result,
        status="completed",
        duration_seconds=duration,
    )
    result["session_id"] = session.id
    result["room_id"] = session.room_id
    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["POST"])
def analyze(request) -> JsonResponse:
    """POST /api/analyze/ — JSON ou multipart/form-data (ZIP)."""
    auth_error = check_api_key(request)
    if auth_error:
        return auth_error

    file_bytes: bytes | None = None
    body: dict[str, Any] = {}

    try:
        if request.content_type and "multipart/form-data" in request.content_type:
            input_type = request.POST.get("input_type", "zip")
            label = request.POST.get("label", "Projet")

            if input_type != "zip":
                return JsonResponse(
                    {"error": "input_type doit être 'zip' pour multipart/form-data"},
                    status=400,
                )
            if "file" not in request.FILES:
                return JsonResponse({"error": "Fichier 'file' manquant"}, status=400)

            uploaded_file = request.FILES["file"]
            if uploaded_file.size > MAX_UPLOAD_BYTES:
                return JsonResponse(
                    {"error": f"Fichier trop volumineux (max {MAX_UPLOAD_BYTES // 1_048_576} Mo)"},
                    status=400,
                )
            file_bytes = uploaded_file.read()
            if len(file_bytes) > MAX_UPLOAD_BYTES:
                return JsonResponse({"error": "Fichier trop volumineux"}, status=400)
            if not validate_zip_file(file_bytes):
                return JsonResponse({"error": "Fichier ZIP invalide ou corrompu"}, status=400)
            input_source = uploaded_file.name
        else:
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "JSON invalide"}, status=400)

            input_type = body.get("input_type")
            label = body.get("label", "Projet")
            input_source = ""

        mode = "A"
        multipart = bool(
            request.content_type and "multipart/form-data" in request.content_type
        )
        locale = _extract_locale(request, body, multipart=multipart)

        if not input_type:
            return JsonResponse({"error": api_message("input_type_required", locale)}, status=400)

        async_mode = body.get("async", True)
        if request.content_type and "multipart/form-data" in request.content_type:
            async_mode = request.POST.get("async", "true").lower() in ("1", "true", "yes")

        start_time = time.time()

        if async_mode and input_type == "github":
            github_url = body.get("github_url") if not multipart else None
            if not github_url:
                return JsonResponse({"error": "github_url manquant"}, status=400)
            if not is_valid_github_url(github_url):
                return JsonResponse({"error": "URL GitHub invalide"}, status=400)

            session = AnalysisSession.objects.create(
                mode=mode,
                room_id="pending",
                input_type=input_type,
                input_source=github_url,
                project_label=label,
                status="pending",
            )
            session.room_id = f"pending-{session.id}"
            session.save(update_fields=["room_id"])
            start_analysis_thread(
                session.id,
                mode,
                label,
                github_url=github_url,
                ingestion_meta={"locale": locale},
                locale=locale,
            )
            return JsonResponse(
                {
                    "async": True,
                    "session_id": session.id,
                    "status": "pending",
                    "message": (
                        "Analysis started — fetching GitHub repository"
                        if locale == "en"
                        else "Analyse démarrée — récupération du dépôt GitHub"
                    ),
                    "locale": locale,
                },
                status=202,
            )

        try:
            ingestion, source = _ingest_project(
                mode=mode,
                input_type=input_type,
                body=body,
                file_bytes=file_bytes,
            )
            if not input_source:
                input_source = source
            project_content = _prepare_project_content(content=ingestion.content)
            ingestion_meta = ingestion.to_dict(locale=locale)
            ingestion_meta["locale"] = locale
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except requests.RequestException as exc:
            logger.warning("GitHub ingestion failed: %s", exc)
            return JsonResponse(
                {
                    "error": (
                        "Impossible de contacter GitHub (réseau ou timeout). "
                        "Ajoutez GITHUB_TOKEN dans .env, réessayez ou collez le code directement."
                    )
                },
                status=502,
            )
        except Exception:
            return JsonResponse(
                {"error": "Erreur lors de l'ingestion du projet"},
                status=500,
            )

        if async_mode:
            session = AnalysisSession.objects.create(
                mode=mode,
                room_id="pending",
                input_type=input_type,
                input_source=input_source,
                project_label=label,
                status="pending",
            )
            session.room_id = f"pending-{session.id}"
            session.save(update_fields=["room_id"])
            start_analysis_thread(
                session.id,
                mode,
                label,
                project_content=project_content,
                ingestion_meta=ingestion_meta,
                locale=locale,
            )
            response_payload = {
                "async": True,
                "session_id": session.id,
                "status": "pending",
                "message": (
                    "Analysis started — follow the live Band Room"
                    if locale == "en"
                    else "Analyse démarrée — suivez la Band Room en direct"
                ),
                "locale": locale,
                "ingestion": ingestion_meta,
            }
            return JsonResponse(response_payload, status=202)

        try:
            runner = _MODE_RUNNERS[mode]
            result = runner(
                project_content=project_content,
                project_label=label,
                ingestion_meta=ingestion_meta,
                locale=locale,
            )
            duration = int(time.time() - start_time)
            return _save_session_and_respond(
                mode=mode,
                input_type=input_type,
                input_source=input_source,
                label=label,
                result=result,
                duration=duration,
            )
        except Exception as exc:
            logger.exception("Sync analysis failed")
            duration = int(time.time() - start_time)
            failed_room_id = str(uuid.uuid4())
            session = AnalysisSession.objects.create(
                mode=mode,
                room_id=failed_room_id,
                input_type=input_type,
                input_source=input_source,
                project_label=label,
                status="failed",
                error_message=str(exc)[:2000],
                duration_seconds=duration,
            )
            payload = {
                "error": "Erreur lors de l'analyse",
                "session_id": session.id,
                "room_id": session.room_id,
            }
            if settings.DEBUG:
                payload["details"] = str(exc)
            return JsonResponse(payload, status=500)

    except Exception as exc:
        logger.exception("Analyze endpoint error")
        payload = {"error": "Erreur serveur"}
        if settings.DEBUG:
            payload["details"] = str(exc)
        return JsonResponse(payload, status=500)


@require_http_methods(["GET"])
def download_pdf(request, room_id: str) -> HttpResponse:
    """GET /api/pdf/<room_id>/ — génère le PDF à partir de la session."""
    try:
        session = AnalysisSession.objects.get(room_id=room_id)
    except AnalysisSession.DoesNotExist:
        return JsonResponse({"error": "Session introuvable", "room_id": room_id}, status=404)

    if session.status != "completed":
        return JsonResponse({"error": "Analyse non terminée"}, status=400)

    result_data = session.result_json or {}
    mode = result_data.get("mode") or session.mode
    branch = result_data.get("branch")
    ingestion = result_data.get("ingestion", {})
    session_locale = normalize_locale(
        result_data.get("locale") or ingestion.get("locale")
    )

    if mode != "A":
        return JsonResponse(
            {"error": api_message("pdf_mode_a_only", session_locale)},
            status=400,
        )

    ctx = extract_report_context(session)
    summary = build_executive_summary(ctx)
    disagreement = format_disagreement(ctx.get("disagreement"), session_locale)
    audit_id = ctx["audit_id"]
    decision = ctx["decision"]
    security_score = ctx["security_score"]
    agents = ctx["agents"]
    final_report = ctx["final_report"]
    report_body = ctx["report_body"]
    metrics_body = ctx["metrics_body"]
    en = session_locale == "en"

    if branch == "reporting":
        pdf_bytes = generate_mode_c_pdf(
            audit_id=audit_id,
            decision=decision,
            security_score=security_score,
            report_text=report_body,
            metrics_text=metrics_body,
            session_date=session.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            locale=session_locale,
            ingestion=ingestion,
            summary=summary,
            disagreement=disagreement,
        )
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="secureflow-{audit_id}.pdf"'
        return response

    report_lines: list[str] = []
    for i, agent in enumerate(agents, 1):
        report_lines.append(f"## {i}. {agent.get('name', 'Agent')}")
        report_lines.append(agent.get("content", "Pas de contenu"))
        report_lines.append("")

    report_lines.append("## " + ("Final report" if en else "Rapport final"))
    report_lines.append(final_report)

    meta_rows = [
        ("Room ID", room_id),
        ("Date", session.created_at.strftime("%Y-%m-%d %H:%M:%S")),
        ("Mode", session.get_mode_display()),
        ("Entrée" if not en else "Input", session.get_input_type_display()),
    ]
    if session.project_label:
        meta_rows.append(("Projet" if not en else "Project", session.project_label))
    if session.duration_seconds:
        meta_rows.append(("Durée" if not en else "Duration", f"{session.duration_seconds}s"))

    pdf_bytes = generate_audit_pdf(
        title=("Security audit report" if en else "Rapport d'audit de sécurité"),
        report_text="\n".join(report_lines),
        audit_id=audit_id,
        decision=decision,
        decision_label=pdf_decision_label(decision, session_locale),
        security_score=security_score,
        summary=summary,
        meta_rows=meta_rows,
        disagreement=disagreement,
        locale=session_locale,
    )

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="secureflow-{audit_id}.pdf"'
    return response


@require_http_methods(["GET"])
def download_zip(request, room_id: str) -> HttpResponse:
    """GET /api/zip/<room_id>/ — patch ZIP post-remédiation Audit-to-Fix."""
    try:
        session = AnalysisSession.objects.get(room_id=room_id)
    except AnalysisSession.DoesNotExist:
        return JsonResponse({"error": "Session introuvable", "room_id": room_id}, status=404)

    if session.status != "completed":
        return JsonResponse({"error": "Analyse non terminée"}, status=400)

    result_data = session.result_json or {}
    mode = result_data.get("mode") or session.mode
    branch = result_data.get("branch")

    if branch != "remediation":
        return JsonResponse(
            {"error": "ZIP disponible uniquement après remédiation (branche CRITIQUE/CORRIGER)."},
            status=400,
        )

    zip_bytes = build_mode_b_zip(result_data, project_label=session.project_label or "remediation")
    if not zip_bytes:
        return JsonResponse(
            {"error": "Aucun fichier patch extrait du DevAgent"},
            status=404,
        )

    audit_id = result_data.get("audit_id") or session.audit_id or room_id[:8]
    response = HttpResponse(zip_bytes, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="secureflow-patch-{audit_id}.zip"'
    return response


@require_http_methods(["GET"])
def download_html_report(request, room_id: str) -> HttpResponse:
    """GET /api/report/<room_id>/ — rapport HTML autonome et stylé.

    ?inline=1 pour l'afficher dans le navigateur, sinon téléchargement .html.
    """
    try:
        session = AnalysisSession.objects.get(room_id=room_id)
    except AnalysisSession.DoesNotExist:
        return JsonResponse({"error": "Session introuvable", "room_id": room_id}, status=404)

    if session.status != "completed":
        return JsonResponse({"error": "Analyse non terminée"}, status=400)

    ctx = extract_report_context(session)
    if ctx.get("mode") != "A":
        return JsonResponse(
            {"error": api_message("pdf_mode_a_only", ctx.get("locale", "fr"))},
            status=400,
        )

    html_doc = render_report_html(ctx)
    audit_id = ctx.get("audit_id") or room_id[:8]
    disposition = "inline" if request.GET.get("inline") else "attachment"
    response = HttpResponse(html_doc, content_type="text/html; charset=utf-8")
    response["Content-Disposition"] = (
        f'{disposition}; filename="secureflow-{audit_id}.html"'
    )
    return response


@require_http_methods(["GET"])
def room_messages(request, room_id: str) -> JsonResponse:
    """GET /api/room/<room_id>/messages/"""
    if is_pending_room_id(room_id):
        return JsonResponse(
            {
                "room_id": room_id,
                "session_id": None,
                "status": "pending",
                "messages": [],
                "count": 0,
            }
        )

    try:
        session = AnalysisSession.objects.get(room_id=room_id)
    except AnalysisSession.DoesNotExist:
        session = None

    try:
        mode = session.mode if session else request.GET.get("mode")
        raw_messages = fetch_merged_room_messages(room_id, mode=mode)
        messages = format_messages_for_ui(raw_messages)
        return JsonResponse(
            {
                "room_id": room_id,
                "session_id": session.id if session else None,
                "status": session.status if session else "unknown",
                "messages": messages,
                "count": len(messages),
            }
        )
    except Exception as e:
        return JsonResponse(
            {"error": "Erreur lors de la récupération des messages", "details": str(e)},
            status=500,
        )


@require_http_methods(["GET"])
def session_detail(request, session_id: int) -> JsonResponse:
    """GET /api/session/<session_id>/"""
    try:
        session = AnalysisSession.objects.get(pk=session_id)
    except AnalysisSession.DoesNotExist:
        return JsonResponse({"error": "Session introuvable"}, status=404)

    response_data = {
        "session_id": session.id,
        "room_id": session.room_id,
        "mode": session.mode,
        "input_type": session.input_type,
        "input_source": session.input_source,
        "project_label": session.project_label,
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "duration_seconds": session.duration_seconds,
    }
    if session.room_id and not is_pending_room_id(session.room_id):
        response_data["band_room_url"] = band_room_web_url(session.room_id)

    if session.is_completed:
        response_data.update(session.result_json)
    elif session.status == "running":
        partial = session.result_json or {}
        response_data["mode"] = partial.get("mode") or session.mode
        response_data["phase"] = partial.get("phase")
        response_data["agents"] = partial.get("agents", [])
        response_data["active_agent"] = partial.get("active_agent")
        response_data["pipeline_agents"] = partial.get("pipeline_agents")
        response_data["recruited_agents"] = partial.get("recruited_agents")
        if partial.get("ingestion"):
            response_data["ingestion"] = partial["ingestion"]
    elif session.status == "awaiting_human":
        partial = session.result_json or {}
        response_data.update(partial)
        response_data["human_review_required"] = True
    elif session.is_failed:
        response_data["error"] = session.error_message

    return JsonResponse(response_data)


@csrf_exempt
@require_http_methods(["POST"])
def human_review(request, session_id: int) -> JsonResponse:
    """POST /api/session/<id>/human-review/ — validation humaine Mode A."""
    try:
        session = AnalysisSession.objects.get(pk=session_id)
    except AnalysisSession.DoesNotExist:
        return JsonResponse({"error": "Session introuvable"}, status=404)

    if session.status != "awaiting_human":
        locale = normalize_locale((session.result_json or {}).get("locale"))
        return JsonResponse(
            {"error": api_message("human_review_not_pending", locale)},
            status=400,
        )

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        body = {}

    action = (body.get("action") or "").strip().lower()
    comment = (body.get("comment") or "").strip()
    locale = normalize_locale(body.get("locale") or (session.result_json or {}).get("locale"))

    if action not in ("proceed", "abort"):
        return JsonResponse({"error": api_message("human_review_invalid_action", locale)}, status=400)

    resume_after_human_review(session_id, action=action, comment=comment)
    return JsonResponse(
        {
            "session_id": session_id,
            "status": "running" if action == "proceed" else "completed",
            "message": api_message("human_review_accepted", locale),
        },
        status=202,
    )


@require_http_methods(["GET"])
def health_check(request) -> JsonResponse:
    """GET /api/health/"""
    return JsonResponse(
        {"status": "ok", "service": "SecureFlow AI API", "version": "1.0.0"}
    )
