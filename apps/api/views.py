import json
import uuid
import time
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .pdf_generator import generate_audit_pdf
from apps.api.models import AnalysisSession

# Import conditionnel pour éviter les erreurs au démarrage
try:
    from apps.orchestrator.services import run_security_audit_json
    ORCHESTRATOR_AVAILABLE = True
except Exception as e:
    ORCHESTRATOR_AVAILABLE = False
    ORCHESTRATOR_ERROR = str(e)


@csrf_exempt
@require_http_methods(["POST"])
def analyze(request):
    """
    Endpoint principal pour lancer une analyse SecureFlow.
    Remplace le mock par les vrais appels à l'orchestrateur de Personne 2.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    mode = data.get("mode", "A")
    input_type = data.get("input_type", "text")
    project_label = data.get("label", "Projet")
    
    # Récupération du contenu selon le type d'input
    if input_type == "text":
        project_content = data.get("content", "")
        if not project_content:
            return JsonResponse({"error": "content is required for input_type=text"}, status=400)
    
    elif input_type == "github":
        github_url = data.get("github_url", "")
        if not github_url:
            return JsonResponse({"error": "github_url is required for input_type=github"}, status=400)
        
        # TODO: Personne 2 doit implémenter l'ingestion GitHub
        # from apps.ingestion.github import fetch_github_project
        # project_content = fetch_github_project(github_url)
        return JsonResponse({
            "error": "GitHub ingestion not yet implemented by Personne 2",
            "message": "Use input_type=text for now"
        }, status=501)
    
    elif input_type == "zip":
        # TODO: Personne 2 doit implémenter l'ingestion ZIP
        # from apps.ingestion.zip_loader import extract_zip_project
        # project_content = extract_zip_project(request.FILES["file"].read())
        return JsonResponse({
            "error": "ZIP ingestion not yet implemented by Personne 2",
            "message": "Use input_type=text for now"
        }, status=501)
    
    else:
        return JsonResponse({"error": f"Invalid input_type: {input_type}"}, status=400)
    
    # Appel à l'orchestrateur selon le mode
    if mode == "A":
        # Mode A : Audit de sécurité (implémenté par Personne 1)
        start_time = time.time()
        
        # Vérifier si l'orchestrateur est disponible
        if not ORCHESTRATOR_AVAILABLE:
            return JsonResponse({
                "error": "Orchestrator not available",
                "message": f"Cannot import orchestrator: {ORCHESTRATOR_ERROR}",
                "mode": "A"
            }, status=500)
        
        try:
            # Lancer l'analyse
            result = run_security_audit_json(
                project_content,
                project_label=project_label
            )
            
            # Calculer la durée
            duration = int(time.time() - start_time)
            
            # Ajouter session_id pour compatibilité avec l'interface
            result["session_id"] = result.get("room_id", str(uuid.uuid4()))
            
            # Générer un audit_id si absent
            audit_id = result.get("audit_id")
            if not audit_id:
                room_id = result.get("room_id", str(uuid.uuid4()))
                audit_id = f"SF-AUDIT-{room_id[:8].upper()}"
                result["audit_id"] = audit_id
            
            # Sauvegarder en base de données
            session = AnalysisSession.objects.create(
                mode=mode,
                room_id=result.get("room_id", str(uuid.uuid4())),
                audit_id=audit_id,
                input_type=input_type,
                input_source=data.get("github_url", "") if input_type == "github" else "",
                project_label=project_label,
                decision=result.get("decision", ""),
                final_report=result.get("final_report", ""),
                result_json=result,
                duration_seconds=duration,
                status="completed"
            )
            
            return JsonResponse(result)
        
        except Exception as e:
            # Sauvegarder l'erreur en base
            try:
                AnalysisSession.objects.create(
                    mode=mode,
                    room_id=str(uuid.uuid4()),
                    input_type=input_type,
                    project_label=project_label,
                    status="failed",
                    error_message=str(e),
                    result_json={"error": str(e)}
                )
            except:
                pass  # Si la sauvegarde échoue, on continue
            
            return JsonResponse({
                "error": "Security audit failed",
                "message": str(e),
                "mode": "A"
            }, status=500)
    
    elif mode == "B":
        # Mode B : Pipeline de développement (à implémenter par Personne 3/4)
        return JsonResponse({
            "error": "Mode B not yet implemented",
            "message": "Mode B (Development Pipeline) is being developed by Personne 3 and 4",
            "mode": "B"
        }, status=501)
    
    elif mode == "C":
        # Mode C : Rapport complet (à implémenter par Personne 4)
        return JsonResponse({
            "error": "Mode C not yet implemented",
            "message": "Mode C (Complete Report) is being developed by Personne 4",
            "mode": "C"
        }, status=501)
    
    else:
        return JsonResponse({"error": f"Invalid mode: {mode}"}, status=400)
def download_pdf(request, session_id):
    """
    Génère un PDF pour n'importe quel mode (A, B, C).
    Utilise les vraies données du ReportAgent depuis la base de données.
    """
    try:
        from apps.api.models import AnalysisSession
        
        # Récupérer la session depuis la base de données
        session = AnalysisSession.objects.get(room_id=session_id)
        
        # Extraire les données du résultat JSON
        result_data = session.result_json
        audit_id = result_data.get("audit_id", f"SF-AUDIT-{session_id[:8].upper()}")
        final_report = result_data.get("final_report", "Rapport non disponible")
        mode = result_data.get("mode", "A")
        decision = result_data.get("decision", "N/A")
        
        # Construire le texte du rapport à partir des agents
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append(f"RAPPORT D'ANALYSE SECUREFLOW AI — MODE {mode}")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append(f"ID Audit       : {audit_id}")
        report_lines.append(f"Session        : {session_id}")
        report_lines.append(f"Date           : {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Mode           : {session.get_mode_display()}")
        report_lines.append(f"Type d'entrée  : {session.get_input_type_display()}")
        report_lines.append(f"Décision       : {decision}")
        
        if session.project_label:
            report_lines.append(f"Projet         : {session.project_label}")
        
        if session.duration_seconds:
            report_lines.append(f"Durée          : {session.duration_seconds}s")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("RÉSULTATS DES AGENTS")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Ajouter les résultats de chaque agent
        agents = result_data.get("agents", [])
        for i, agent in enumerate(agents, 1):
            agent_name = agent.get("name", "Agent inconnu")
            agent_content = agent.get("content", "Pas de contenu")
            
            report_lines.append(f"{i}. {agent_name}")
            report_lines.append("-" * 80)
            report_lines.append(agent_content)
            report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("RAPPORT FINAL")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append(final_report)
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("Ce rapport a été généré automatiquement par SecureFlow AI.")
        report_lines.append("Pour plus d'informations : https://secureflow-ai.com")
        
        report_text = "\n".join(report_lines)
        
    except AnalysisSession.DoesNotExist:
        # Session non trouvée
        audit_id = f"SF-AUDIT-{session_id[:8].upper()}"
        report_text = f"""ERREUR - SESSION NON TROUVÉE

Session ID : {session_id}

La session demandée n'existe pas dans la base de données.
Veuillez vérifier l'ID de session et réessayer.

Si le problème persiste, contactez le support technique."""
        
        return JsonResponse({
            "error": "Session not found",
            "session_id": session_id
        }, status=404)
    
    except Exception as e:
        # Autre erreur
        audit_id = f"SF-AUDIT-{session_id[:8].upper()}"
        report_text = f"""ERREUR LORS DE LA GÉNÉRATION DU RAPPORT

Session ID : {session_id}
Erreur : {str(e)}

Une erreur s'est produite lors de la récupération des données.
Veuillez réessayer ou contactez le support technique."""
        
        return JsonResponse({
            "error": "PDF generation failed",
            "message": str(e),
            "session_id": session_id
        }, status=500)
    
    # Générer le PDF avec les vraies données
    pdf_bytes = generate_audit_pdf(
        title=f"Rapport d'Analyse SecureFlow AI - Mode {mode}",
        report_text=report_text,
        audit_id=audit_id,
    )
    
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="secureflow-{audit_id}.pdf"'
    return response
@require_http_methods(["GET"])
def room_messages(request, room_id):
    """
    Endpoint optionnel pour afficher les messages Band Room en temps réel.
    Nécessite l'intégration avec band_registry pour récupérer le contexte.
    """
    try:
        from apps.agents.band_registry import get_band_client_for
        
        # Utiliser n'importe quel agent participant pour accéder à la room
        client = get_band_client_for("ScannerAgent")
        messages = client.get_context(room_id)
        
        return JsonResponse({
            "room_id": room_id,
            "messages": messages,
            "count": len(messages)
        })
    except Exception as e:
        return JsonResponse({
            "error": str(e),
            "room_id": room_id,
            "messages": []
        }, status=500)