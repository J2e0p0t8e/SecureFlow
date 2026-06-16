import json
import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .pdf_generator import generate_audit_pdf


@csrf_exempt
@require_http_methods(["POST"])
def analyze(request):
    data = json.loads(request.body)
    mode = data.get("mode", "A")

    room_id = str(uuid.uuid4())
    audit_id = f"SF-AUDIT-20260616-{str(uuid.uuid4())[:4].upper()}"

    if mode == "A":
        agents = [
            {"name": "ScannerAgent", "content": "SCAN TERMINÉ : 3 zones sensibles détectées — endpoints /login, /api/users, dépendance Flask 1.0.2 obsolète."},
            {"name": "ThreatAgent", "content": "MENACES IDENTIFIÉES : Injection SQL possible sur /login (Critique), XSS sur /api/users (Élevé), CVE-2021-23386 (Moyen)."},
            {"name": "ComplianceAgent", "content": "CONFORMITÉ : Injection SQL → OWASP A03:2021 / CWE-89. XSS → OWASP A07:2021 / CWE-79. RGPD : données personnelles exposées."},
            {"name": "RiskAgent", "content": "SCORE DE RISQUE : 7.2/10 — Élevé. Impact business : accès non autorisé aux données utilisateurs possible."},
            {"name": "DecisionAgent", "content": "DÉCISION : CORRIGER AVANT MISE EN PROD. Actions : (1) Paramétrer les requêtes SQL, (2) Échapper les sorties HTML, (3) Mettre à jour Flask."},
        ]
        decision = "CORRIGER"
        final_report = f"""RAPPORT D'AUDIT DE SÉCURITÉ — {audit_id}

ScannerAgent : 3 zones sensibles détectées — endpoints /login, /api/users, dépendance Flask 1.0.2 obsolète.

ThreatAgent : Injection SQL possible sur /login (Critique), XSS sur /api/users (Élevé), CVE-2021-23386 (Moyen).

ComplianceAgent : OWASP A03:2021 / CWE-89 (SQL), OWASP A07:2021 / CWE-79 (XSS). RGPD : données exposées.

RiskAgent : Score de risque 7.2/10 — Élevé. Impact business : accès non autorisé aux données utilisateurs.

DecisionAgent : CORRIGER AVANT MISE EN PROD. Actions prioritaires : (1) Paramétrer les requêtes SQL, (2) Échapper les sorties HTML, (3) Mettre à jour Flask."""

    elif mode == "B":
        agents = [
            {"name": "FeasibilityAgent", "content": "FAISABILITÉ : Projet réalisable en 3 semaines. Risques : intégration paiement complexe. Feu vert avec réserves."},
            {"name": "ArchitectAgent", "content": "ARCHITECTURE : Django REST + React + PostgreSQL. Structure : apps/auth, apps/products, apps/orders."},
            {"name": "DesignAgent", "content": "DESIGN : Interface minimaliste, palette bleu/blanc, composants : Navbar, ProductCard, CartDrawer, CheckoutForm."},
            {"name": "DevAgent", "content": "CODE GÉNÉRÉ : models.py, views.py, serializers.py, App.jsx avec routing React. 847 lignes au total."},
            {"name": "SecurityAgent", "content": "AUDIT CODE : token JWT non expiré (Élevé), mot de passe en clair dans les logs (Critique). Correctifs fournis."},
            {"name": "QAAgent", "content": "VALIDATION : Score qualité 72/100. Tests à implémenter : auth flow, panier, paiement."},
        ]
        decision = "LIVRABLE PRÊT"
        final_report = f"""RAPPORT DE DÉVELOPPEMENT — {audit_id}

FeasibilityAgent : Projet réalisable en 3 semaines. Risques : intégration paiement complexe. Feu vert avec réserves.

ArchitectAgent : Architecture Django REST + React + PostgreSQL. Structure : apps/auth, apps/products, apps/orders.

DesignAgent : Interface minimaliste, palette bleu/blanc. Composants : Navbar, ProductCard, CartDrawer, CheckoutForm.

DevAgent : Code généré — models.py, views.py, serializers.py, App.jsx avec routing React. Total : 847 lignes.

SecurityAgent : Audit du code généré — token JWT non expiré (Élevé), mot de passe en clair dans les logs (Critique). Correctifs fournis.

QAAgent : Score qualité 72/100. Tests à implémenter : auth flow, panier, paiement."""

    else:  # Mode C
        agents = [
            {"name": "ScannerAgent", "content": "CARTOGRAPHIE : 12 fichiers analysés, 4 zones sensibles, langage dominant Python/Django."},
            {"name": "ThreatAgent", "content": "VULNÉRABILITÉS : 2 Critiques, 3 Élevées, 4 Moyennes, 1 Faible."},
            {"name": "ComplianceAgent", "content": "CONFORMITÉ : OWASP Top 10 — 3 violations. CWE — 5 références. RGPD : données sans consentement."},
            {"name": "MetricsAgent", "content": "MÉTRIQUES : Score global 6.8/10. Dette technique : 4 jours. Couverture bonnes pratiques : 61%."},
            {"name": "ReportAgent", "content": "RAPPORT FINAL : 10 vulnérabilités documentées, recommandations priorisées. ID : SF-AUDIT-20260616-0042."},
        ]
        decision = "RAPPORT GÉNÉRÉ"
        final_report = f"""RAPPORT COMPLET D'AUDIT — {audit_id}

ScannerAgent : Cartographie — 12 fichiers analysés, 4 zones sensibles, langage dominant Python/Django.

ThreatAgent : Vulnérabilités détectées — 2 Critiques, 3 Élevées, 4 Moyennes, 1 Faible.

ComplianceAgent : Conformité — OWASP Top 10 (3 violations), CWE (5 références), RGPD (données sans consentement).

MetricsAgent : Métriques — Score global 6.8/10, Dette technique 4 jours, Couverture bonnes pratiques 61%.

ReportAgent : 10 vulnérabilités documentées avec recommandations priorisées."""

    return JsonResponse({
        "mode": mode,
        "room_id": room_id,
        "decision": decision,
        "audit_id": audit_id,
        "final_report": final_report,
        "agents": agents,
        "session_id": room_id,
    })


def download_pdf(request, session_id):
    """
    Génère un PDF pour n'importe quel mode (A, B, C).
    Le contenu est générique mais peut être personnalisé selon le mode.
    """
    audit_id = f"SF-AUDIT-20260616-{session_id[:4].upper()}"
    
    # Contenu générique pour tous les modes
    report_text = f"""RAPPORT D'ANALYSE SECUREFLOW AI

ID : {audit_id}
Session : {session_id}

Ce rapport contient les résultats de l'analyse effectuée par les agents IA de SecureFlow.

RÉSUMÉ DES AGENTS :

ScannerAgent : Analyse complète du code source et détection des zones sensibles.

ThreatAgent : Identification des menaces et vulnérabilités potentielles.

ComplianceAgent : Vérification de la conformité aux standards OWASP, CWE et RGPD.

RiskAgent / MetricsAgent : Évaluation des risques et calcul des métriques de qualité.

DecisionAgent / ReportAgent : Recommandations finales et plan d'action.

CONCLUSION :

Tous les résultats détaillés sont disponibles dans l'interface web.
Ce rapport PDF sert de document officiel pour archivage et partage.

Pour plus d'informations, consultez : https://secureflow-ai.com"""

    pdf_bytes = generate_audit_pdf(
        title="Rapport d'Analyse SecureFlow AI",
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