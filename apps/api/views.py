"""
Vues API pour SecureFlow AI.
Backend ingestion (P2) + PDF download (P5).
"""

import json
import time
import uuid

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.api.models import AnalysisSession
from apps.api.pdf_generator import generate_audit_pdf
from apps.ingestion.github import fetch_github_project, is_valid_github_url
from apps.ingestion.zip_loader import extract_zip_project, validate_zip_file
from apps.orchestrator.services import run_security_audit_json


@csrf_exempt
@require_http_methods(["POST"])
def analyze(request) -> JsonResponse:
    """
    POST /api/analyze/

    JSON ou multipart/form-data (ZIP).
    """
    file_bytes = None
    body: dict = {}

    try:
        if request.content_type and "multipart/form-data" in request.content_type:
            mode = request.POST.get("mode", "A")
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
            file_bytes = uploaded_file.read()

            if not validate_zip_file(file_bytes):
                return JsonResponse({"error": "Fichier ZIP invalide ou corrompu"}, status=400)

            input_source = uploaded_file.name
        else:
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "JSON invalide"}, status=400)

            mode = body.get("mode", "A")
            input_type = body.get("input_type")
            label = body.get("label", "Projet")
            input_source = ""

        if mode not in ("A", "B", "C"):
            return JsonResponse({"error": "mode doit être 'A', 'B' ou 'C'"}, status=400)

        if mode in ("B", "C"):
            return JsonResponse(
                {
                    "error": f"Mode {mode} pas encore implémenté",
                    "message": "En attente de l'intégration orchestrateur",
                },
                status=501,
            )

        if not input_type:
            return JsonResponse({"error": "input_type requis"}, status=400)

        start_time = time.time()

        if input_type == "github":
            github_url = body.get("github_url")
            if not github_url:
                return JsonResponse({"error": "github_url manquant"}, status=400)
            if not is_valid_github_url(github_url):
                return JsonResponse({"error": "URL GitHub invalide"}, status=400)
            try:
                project_content = fetch_github_project(github_url, max_files=50)
                input_source = github_url
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=400)
            except Exception:
                return JsonResponse(
                    {"error": "Erreur lors de la récupération du repo GitHub"},
                    status=500,
                )

        elif input_type == "zip":
            if file_bytes is None:
                return JsonResponse(
                    {
                        "error": "ZIP requis en multipart/form-data",
                        "hint": "Envoyez mode, input_type=zip, label et file",
                    },
                    status=400,
                )
            try:
                project_content = extract_zip_project(file_bytes, max_files=50)
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=400)
            except Exception:
                return JsonResponse(
                    {"error": "Erreur lors de l'extraction du ZIP"},
                    status=500,
                )

        elif input_type == "text":
            project_content = body.get("content")
            if not project_content:
                return JsonResponse({"error": "content manquant"}, status=400)
            input_source = "Code collé"

        else:
            return JsonResponse(
                {"error": "input_type invalide", "valid_types": ["github", "zip", "text"]},
                status=400,
            )

        try:
            result = run_security_audit_json(
                project_content=project_content,
                project_label=label,
            )
            duration = int(time.time() - start_time)

            session = AnalysisSession.objects.create(
                mode=mode,
                room_id=result.get("room_id") or str(uuid.uuid4()),
                audit_id=result.get("audit_id", ""),
                input_type=input_type,
                input_source=input_source,
                project_label=label,
                decision=result.get("decision", ""),
                final_report=result.get("final_report", ""),
                result_json=result,
                status="completed",
                duration_seconds=duration,
            )

            result["session_id"] = session.id
            result["room_id"] = session.room_id
            return JsonResponse(result)

        except Exception as e:
            duration = int(time.time() - start_time)
            failed_room_id = str(uuid.uuid4())
            session = AnalysisSession.objects.create(
                mode=mode,
                room_id=failed_room_id,
                input_type=input_type,
                input_source=input_source,
                project_label=label,
                status="failed",
                error_message=str(e),
                duration_seconds=duration,
            )
            return JsonResponse(
                {
                    "error": "Erreur lors de l'analyse",
                    "session_id": session.id,
                    "room_id": session.room_id,
                },
                status=500,
            )

    except Exception:
        return JsonResponse({"error": "Erreur serveur"}, status=500)


@require_http_methods(["GET"])
def download_pdf(request, room_id: str) -> HttpResponse:
    """GET /api/pdf/<room_id>/ — génère le PDF à partir de la session."""
    try:
        session = AnalysisSession.objects.get(room_id=room_id)
    except AnalysisSession.DoesNotExist:
        return JsonResponse({"error": "Session introuvable", "room_id": room_id}, status=404)

    result_data = session.result_json or {}
    audit_id = result_data.get("audit_id") or session.audit_id or f"SF-AUDIT-{room_id[:8].upper()}"
    final_report = result_data.get("final_report") or session.final_report or "Rapport non disponible"
    mode = result_data.get("mode") or session.mode
    decision = result_data.get("decision") or session.decision or "N/A"

    report_lines = [
        "=" * 80,
        f"RAPPORT D'ANALYSE SECUREFLOW AI — MODE {mode}",
        "=" * 80,
        "",
        f"ID Audit       : {audit_id}",
        f"Room ID        : {room_id}",
        f"Date           : {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Mode           : {session.get_mode_display()}",
        f"Type d'entrée  : {session.get_input_type_display()}",
        f"Décision       : {decision}",
    ]

    if session.project_label:
        report_lines.append(f"Projet         : {session.project_label}")
    if session.duration_seconds:
        report_lines.append(f"Durée          : {session.duration_seconds}s")

    report_lines.extend(["", "=" * 80, "RÉSULTATS DES AGENTS", "=" * 80, ""])

    for i, agent in enumerate(result_data.get("agents", []), 1):
        report_lines.append(f"{i}. {agent.get('name', 'Agent inconnu')}")
        report_lines.append("-" * 80)
        report_lines.append(agent.get("content", "Pas de contenu"))
        report_lines.append("")

    report_lines.extend(
        [
            "=" * 80,
            "RAPPORT FINAL",
            "=" * 80,
            "",
            final_report,
            "",
            "Ce rapport a été généré automatiquement par SecureFlow AI.",
        ]
    )

    pdf_bytes = generate_audit_pdf(
        title=f"Rapport SecureFlow AI - Mode {mode}",
        report_text="\n".join(report_lines),
        audit_id=audit_id,
    )

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="secureflow-{audit_id}.pdf"'
    return response


@require_http_methods(["GET"])
def room_messages(request, room_id: str) -> JsonResponse:
    """GET /api/room/<room_id>/messages/"""
    try:
        session = AnalysisSession.objects.get(room_id=room_id)
    except AnalysisSession.DoesNotExist:
        return JsonResponse({"error": "Room introuvable"}, status=404)

    try:
        from apps.agents.band_registry import get_band_client_for

        client = get_band_client_for("ScannerAgent")
        messages = client.get_context(room_id)
        return JsonResponse(
            {
                "room_id": room_id,
                "session_id": session.id,
                "status": session.status,
                "messages": messages,
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

    if session.is_completed:
        response_data.update(session.result_json)
    elif session.is_failed:
        response_data["error"] = session.error_message

    return JsonResponse(response_data)


@require_http_methods(["GET"])
def health_check(request) -> JsonResponse:
    """GET /api/health/"""
    return JsonResponse(
        {"status": "ok", "service": "SecureFlow AI API", "version": "1.0.0"}
    )
