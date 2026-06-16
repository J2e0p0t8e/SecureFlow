import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["POST"])
def analyze(request):
    data = json.loads(request.body)
    mode = data.get("mode", "A")

    # ---- MOCK : simule la réponse de Personne 2 ----
    room_id = str(uuid.uuid4())

    if mode == "A":
        agents = [
            {"name": "ScannerAgent", "content": "SCAN TERMINÉ : 3 zones sensibles détectées — endpoints /login, /api/users, dépendance Flask 1.0.2 obsolète."},
            {"name": "ThreatAgent", "content": "MENACES IDENTIFIÉES : Injection SQL possible sur /login (Critique), XSS sur /api/users (Élevé), dépendance vulnérable CVE-2021-23386 (Moyen)."},
            {"name": "ComplianceAgent", "content": "CONFORMITÉ : Injection SQL → OWASP A03:2021 / CWE-89. XSS → OWASP A07:2021 / CWE-79. RGPD : données personnelles exposées sans chiffrement."},
            {"name": "RiskAgent", "content": "SCORE DE RISQUE : 7.2/10 — Élevé. Impact business : accès non autorisé aux données utilisateurs possible. 3 actions urgentes identifiées."},
            {"name": "DecisionAgent", "content": "DÉCISION : CORRIGER AVANT MISE EN PROD. Actions prioritaires : (1) Paramétrer les requêtes SQL, (2) Échapper les sorties HTML, (3) Mettre à jour Flask."},
        ]
        decision = "CORRIGER"

    elif mode == "B":
        agents = [
            {"name": "FeasibilityAgent", "content": "FAISABILITÉ : Projet réalisable en 3 semaines avec une équipe de 2. Risques : intégration paiement complexe. Feu vert avec réserves."},
            {"name": "ArchitectAgent", "content": "ARCHITECTURE : Stack recommandée — Django REST + React + PostgreSQL. Structure : apps/auth, apps/products, apps/orders. API REST versionnée."},
            {"name": "DesignAgent", "content": "DESIGN : Interface minimaliste, palette bleu/blanc, composants : Navbar, ProductCard, CartDrawer, CheckoutForm. Mobile-first."},
            {"name": "DevAgent", "content": "CODE GÉNÉRÉ : models.py (User, Product, Order), views.py (CRUD), serializers.py, App.jsx avec routing React. 847 lignes au total."},
            {"name": "SecurityAgent", "content": "AUDIT CODE : 2 vulnérabilités — token JWT non expiré (Élevé), mot de passe en clair dans les logs (Critique). Correctifs fournis."},
            {"name": "QAAgent", "content": "VALIDATION : Score qualité 72/100. Tests à implémenter : auth flow, panier, paiement. Risques résiduels : performance sous charge."},
        ]
        decision = "LIVRABLE PRÊT"

    else:  # Mode C
        agents = [
            {"name": "ScannerAgent", "content": "CARTOGRAPHIE : 12 fichiers analysés, 4 zones sensibles, langage dominant Python/Django."},
            {"name": "ThreatAgent", "content": "VULNÉRABILITÉS : 2 Critiques, 3 Élevées, 4 Moyennes, 1 Faible."},
            {"name": "ComplianceAgent", "content": "CONFORMITÉ : OWASP Top 10 — 3 violations. CWE — 5 références. RGPD — données personnelles sans consentement explicite."},
            {"name": "MetricsAgent", "content": "MÉTRIQUES : Score global 6.8/10. Dette technique estimée : 4 jours. Couverture bonnes pratiques : 61%."},
            {"name": "ReportAgent", "content": "RAPPORT FINAL : Audit complet généré. 10 vulnérabilités documentées, recommandations priorisées, identifiant SF-AUDIT-20260616-0042."},
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