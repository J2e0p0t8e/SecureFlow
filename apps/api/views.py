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

    if mode == "A":
        agents = [
            {"name": "ScannerAgent", "content": "SCAN TERMINÉ : 3 zones sensibles détectées — endpoints /login, /api/users, dépendance Flask 1.0.2 obsolète."},
            {"name": "ThreatAgent", "content": "MENACES IDENTIFIÉES : Injection SQL possible sur /login (Critique), XSS sur /api/users (Élevé), CVE-2021-23386 (Moyen)."},
            {"name": "ComplianceAgent", "content": "CONFORMITÉ : Injection SQL → OWASP A03:2021 / CWE-89. XSS → OWASP A07:2021 / CWE-79. RGPD : données personnelles exposées."},
            {"name": "RiskAgent", "content": "SCORE DE RISQUE : 7.2/10 — Élevé. Impact business : accès non autorisé aux données utilisateurs possible."},
            {"name": "DecisionAgent", "content": "DÉCISION : CORRIGER AVANT MISE EN PROD. Actions : (1) Paramétrer les requêtes SQL, (2) Échapper les sorties HTML, (3) Mettre à jour Flask."},
        ]
        decision = "CORRIGER"

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

    else:  # Mode C
        agents = [
            {"name": "ScannerAgent", "content": "CARTOGRAPHIE : 12 fichiers analysés, 4 zones sensibles, langage dominant Python/Django."},
            {"name": "ThreatAgent", "content": "VULNÉRABILITÉS : 2 Critiques, 3 Élevées, 4 Moyennes, 1 Faible."},
            {"name": "ComplianceAgent", "content": "CONFORMITÉ : OWASP Top 10 — 3 violations. CWE — 5 références. RGPD : données sans consentement."},
            {"name": "MetricsAgent", "content": "MÉTRIQUES : Score global 6.8/10. Dette technique : 4 jours. Couverture bonnes pratiques : 61%."},
            {"name": "ReportAgent", "content": "RAPPORT FINAL : 10 vulnérabilités documentées, recommandations priorisées. ID : SF-AUDIT-20260616-0042."},
        ]
        decision = "RAPPORT GÉNÉRÉ"

    return JsonResponse({
        "mode": mode,
        "room_id": room_id,
        "decision": decision,
        "audit_id": f"SF-AUDIT-20260616-{str(uuid.uuid4())[:4].upper()}",
        "final_report": agents[-1]["content"],
        "agents": agents,
        "session_id": room_id,
    })


def download_pdf(request, session_id):
    audit_id = f"SF-AUDIT-20260616-{session_id[:4].upper()}"
    report_text = """ScannerAgent : 3 zones sensibles détectées — endpoints /login, /api/users, dépendance obsolète.

ThreatAgent : Injection SQL possible sur /login (Critique), XSS sur /api/users (Élevé), CVE-2021-23386 (Moyen).

ComplianceAgent : OWASP A03:2021 / CWE-89 (SQL), OWASP A07:2021 / CWE-79 (XSS). RGPD : données exposées.

MetricsAgent : Score global 6.8/10. Dette technique : 4 jours. Couverture bonnes pratiques : 61%.

ReportAgent : 10 vulnérabilités documentées. Actions prioritaires : corriger SQL, échapper HTML, mettre à jour dépendances."""

    pdf_bytes = generate_audit_pdf(
        title="Audit sécurité",
        report_text=report_text,
        audit_id=audit_id,
    )
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="secureflow-{audit_id}.pdf"'
    return response