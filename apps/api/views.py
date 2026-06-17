"""
Vues API pour SecureFlow AI.
Personne 2 - Backend & Ingestion.
"""

import json
import time
from typing import Any

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.api.models import AnalysisSession
from apps.ingestion.github import fetch_github_project, is_valid_github_url
from apps.ingestion.zip_loader import extract_zip_project, validate_zip_file
from apps.orchestrator.services import run_security_audit_json


@csrf_exempt  # À remplacer par une vraie gestion CSRF en production
@require_http_methods(["POST"])
def analyze(request) -> JsonResponse:
    """
    Endpoint principal pour lancer une analyse SecureFlow.
    
    POST /api/analyze/
    
    Body JSON:
    {
        "mode": "A" | "B" | "C",
        "input_type": "github" | "zip" | "text",
        "github_url": "https://github.com/user/repo",  // si input_type=github
        "content": "code...",                          // si input_type=text
        "label": "mon-projet"                          // optionnel
    }
    
    Ou multipart/form-data avec:
    - mode, input_type, label (form fields)
    - file (fichier ZIP si input_type=zip)
    
    Response:
    {
        "mode": "A",
        "room_id": "uuid",
        "decision": "CORRIGER",
        "audit_id": "SF-AUDIT-...",
        "final_report": "...",
        "agents": [...],
        "session_id": 123
    }
    """
    try:
        # 1. Parser la requête
        if request.content_type and "multipart/form-data" in request.content_type:
            # Upload de fichier ZIP
            mode = request.POST.get("mode", "A")
            input_type = request.POST.get("input_type", "zip")
            label = request.POST.get("label", "Projet")
            
            if input_type != "zip":
                return JsonResponse({
                    "error": "input_type doit être 'zip' pour multipart/form-data"
                }, status=400)
            
            if "file" not in request.FILES:
                return JsonResponse({"error": "Fichier 'file' manquant"}, status=400)
            
            uploaded_file = request.FILES["file"]
            file_bytes = uploaded_file.read()
            
            # Valider le ZIP
            if not validate_zip_file(file_bytes):
                return JsonResponse({"error": "Fichier ZIP invalide ou corrompu"}, status=400)
            
            input_source = uploaded_file.name
            
        else:
            # JSON
            try:
                body = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "JSON invalide"}, status=400)
            
            mode = body.get("mode", "A")
            input_type = body.get("input_type")
            label = body.get("label", "Projet")
            input_source = ""
        
        # 2. Valider le mode
        if mode not in ["A", "B", "C"]:
            return JsonResponse({"error": "mode doit être 'A', 'B' ou 'C'"}, status=400)
        
        # Mode B et C pas encore implémentés (Personne 3 et 4)
        if mode in ["B", "C"]:
            return JsonResponse({
                "error": f"Mode {mode} pas encore implémenté",
                "message": "En attente de l'intégration par Personne 1 (J5)"
            }, status=501)
        
        # 3. Récupérer le contenu du projet selon input_type
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
            except Exception as e:
                return JsonResponse({
                    "error": "Erreur lors de la récupération du repo GitHub",
                    "details": str(e)
                }, status=500)
        
        elif input_type == "zip":
            # Déjà traité dans le bloc multipart ci-dessus
            try:
                project_content = extract_zip_project(file_bytes, max_files=50)
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=400)
            except Exception as e:
                return JsonResponse({
                    "error": "Erreur lors de l'extraction du ZIP",
                    "details": str(e)
                }, status=500)
        
        elif input_type == "text":
            project_content = body.get("content")
            if not project_content:
                return JsonResponse({"error": "content manquant"}, status=400)
            input_source = "Code collé"
        
        else:
            return JsonResponse({
                "error": "input_type invalide",
                "valid_types": ["github", "zip", "text"]
            }, status=400)
        
        # 4. Créer la session en base (statut pending)
        session = AnalysisSession.objects.create(
            mode=mode,
            input_type=input_type,
            input_source=input_source,
            project_label=label,
            status="running",
        )
        
        # 5. Appeler l'orchestrateur Mode A (Personne 1)
        try:
            result = run_security_audit_json(
                project_content=project_content,
                project_label=label,
            )
            
            # 6. Mettre à jour la session avec les résultats
            duration = int(time.time() - start_time)
            
            session.room_id = result.get("room_id", "")
            session.audit_id = result.get("audit_id", "")
            session.decision = result.get("decision", "")
            session.final_report = result.get("final_report", "")
            session.result_json = result
            session.status = "completed"
            session.duration_seconds = duration
            session.save()
            
            # 7. Ajouter l'ID de session à la réponse
            result["session_id"] = session.id
            
            return JsonResponse(result)
        
        except Exception as e:
            # Marquer la session comme échouée
            session.status = "failed"
            session.error_message = str(e)
            session.duration_seconds = int(time.time() - start_time)
            session.save()
            
            return JsonResponse({
                "error": "Erreur lors de l'analyse",
                "details": str(e),
                "session_id": session.id
            }, status=500)
    
    except Exception as e:
        return JsonResponse({
            "error": "Erreur serveur",
            "details": str(e)
        }, status=500)


@require_http_methods(["GET"])
def room_messages(request, room_id: str) -> JsonResponse:
    """
    Récupère les messages d'une Band Room.
    Utile pour l'affichage live dans l'interface (Personne 5).
    
    GET /api/room/{room_id}/messages/
    
    Response:
    {
        "room_id": "uuid",
        "messages": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """
    try:
        # Vérifier que la session existe
        try:
            session = AnalysisSession.objects.get(room_id=room_id)
        except AnalysisSession.DoesNotExist:
            return JsonResponse({"error": "Room introuvable"}, status=404)
        
        # Récupérer les messages via le client Band
        from apps.agents.band_registry import get_band_client_for
        
        # Utiliser n'importe quel agent participant (ex: Scanner)
        client = get_band_client_for("ScannerAgent")
        messages = client.get_context(room_id)
        
        return JsonResponse({
            "room_id": room_id,
            "session_id": session.id,
            "status": session.status,
            "messages": messages,
        })
    
    except Exception as e:
        return JsonResponse({
            "error": "Erreur lors de la récupération des messages",
            "details": str(e)
        }, status=500)


@require_http_methods(["GET"])
def session_detail(request, session_id: int) -> JsonResponse:
    """
    Récupère les détails d'une session d'analyse.
    
    GET /api/session/{session_id}/
    
    Response: même format que /api/analyze/ + métadonnées
    """
    try:
        session = AnalysisSession.objects.get(pk=session_id)
    except AnalysisSession.DoesNotExist:
        return JsonResponse({"error": "Session introuvable"}, status=404)
    
    response_data = {
        "session_id": session.id,
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
    """
    Endpoint de santé pour vérifier que l'API fonctionne.
    
    GET /api/health/
    """
    return JsonResponse({
        "status": "ok",
        "service": "SecureFlow AI API",
        "version": "1.0.0"
    })

# Made with Bob
