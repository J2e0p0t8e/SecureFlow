# Intégration PDF avec ReportAgent - TERMINÉE ✅

## Résumé des modifications

Le fichier [`apps/api/views.py`](apps/api/views.py) a été mis à jour pour utiliser les vraies données du ReportAgent depuis la base de données Django via le modèle `AnalysisSession`.

## Changements effectués

### 1. Modèle `AnalysisSession` créé

Le fichier [`apps/api/models.py`](apps/api/models.py) a été créé depuis la branche `Le-monstre` avec le modèle complet:

```python
class AnalysisSession(models.Model):
    # Identifiants
    mode = models.CharField(max_length=1, choices=MODE_CHOICES)
    room_id = models.CharField(max_length=64, unique=True)
    audit_id = models.CharField(max_length=50, blank=True)
    
    # Entrée utilisateur
    input_type = models.CharField(max_length=20, choices=INPUT_TYPE_CHOICES)
    input_source = models.TextField(blank=True)
    project_label = models.CharField(max_length=200, blank=True)
    
    # Résultats
    decision = models.CharField(max_length=20, blank=True)
    final_report = models.TextField(blank=True)
    result_json = models.JSONField(default=dict)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default="pending")
```

### 2. Fonction `analyze()` mise à jour

La fonction sauvegarde maintenant automatiquement les résultats en base de données:

```python
# Après l'appel à run_security_audit_json()
session = AnalysisSession.objects.create(
    mode=mode,
    room_id=result["room_id"],
    audit_id=result.get("audit_id", ""),
    input_type=input_type,
    project_label=project_label,
    decision=result.get("decision", ""),
    final_report=result.get("final_report", ""),
    result_json=result,
    duration_seconds=duration,
    status="completed"
)
```

### 3. Fonction `download_pdf()` complètement réécrite

**Avant:** Texte fictif générique

**Après:** Récupération des vraies données depuis la base de données

```python
def download_pdf(request, session_id):
    # Récupérer la session depuis la base de données
    session = AnalysisSession.objects.get(room_id=session_id)
    
    # Extraire les données du résultat JSON
    result_data = session.result_json
    audit_id = result_data.get("audit_id")
    final_report = result_data.get("final_report")
    
    # Construire le rapport avec les vraies données des agents
    agents = result_data.get("agents", [])
    for agent in agents:
        # Inclure le contenu de chaque agent (ScannerAgent, ThreatAgent, etc.)
        report_lines.append(f"{agent['name']}: {agent['content']}")
    
    # Générer le PDF avec les vraies données
    pdf_bytes = generate_audit_pdf(...)
```

### 4. Format du PDF généré

Le PDF contient maintenant:

```
================================================================================
RAPPORT D'ANALYSE SECUREFLOW AI — MODE A
================================================================================

ID Audit       : SF-AUDIT-20260614-1234
Session        : e93506d9-3597-4c8f-bd65-35c14712d0d5
Date           : 2026-06-17 12:30:45
Mode           : Mode A - Audit de sécurité
Type d'entrée  : Code collé
Décision       : CORRIGER
Projet         : Test SQL Injection
Durée          : 45s

================================================================================
RÉSULTATS DES AGENTS
================================================================================

1. ScannerAgent
--------------------------------------------------------------------------------
SCAN TERMINÉ : 3 zones sensibles détectées — endpoints /login, /api/users...

2. ThreatAgent
--------------------------------------------------------------------------------
MENACES IDENTIFIÉES : Injection SQL possible sur /login (Critique)...

3. ComplianceAgent
--------------------------------------------------------------------------------
CONFORMITÉ : Injection SQL → OWASP A03:2021 / CWE-89...

4. RiskAgent
--------------------------------------------------------------------------------
SCORE DE RISQUE : 7.2/10 — Élevé...

5. DecisionAgent
--------------------------------------------------------------------------------
DÉCISION : CORRIGER AVANT MISE EN PROD...

================================================================================
RAPPORT FINAL
================================================================================

[Contenu du champ final_report du ReportAgent]

================================================================================

Ce rapport a été généré automatiquement par SecureFlow AI.
Pour plus d'informations : https://secureflow-ai.com
```

## Installation et test

### 1. Créer les migrations

```powershell
cd SecureFlow
.\.venv\Scripts\Activate.ps1

# Installer les dépendances manquantes si nécessaire
pip install django-cors-headers

# Créer les migrations pour le nouveau modèle
python manage.py makemigrations api

# Appliquer les migrations
python manage.py migrate
```

### 2. Tester l'API complète

```powershell
# Lancer le serveur
python manage.py runserver

# Dans un autre terminal, tester l'analyse
$body = @{
    mode = "A"
    input_type = "text"
    content = @"
import sqlite3
def login(user, pwd):
    query = f"SELECT * FROM users WHERE user='{user}' AND pwd='{pwd}'"
    return query
"@
    label = "Test SQL Injection"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/analyze/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

# Récupérer le session_id
$sessionId = $response.session_id
Write-Host "Session ID: $sessionId"

# Télécharger le PDF avec les vraies données
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/download_pdf/$sessionId/" `
    -OutFile "rapport-test.pdf"

Write-Host "PDF téléchargé: rapport-test.pdf"
```

### 3. Vérifier en base de données

```powershell
# Ouvrir le shell Django
python manage.py shell

# Vérifier les sessions sauvegardées
from apps.api.models import AnalysisSession
sessions = AnalysisSession.objects.all()
for s in sessions:
    print(f"{s.audit_id} - {s.decision} - {s.created_at}")
```

## Gestion des erreurs

### Session non trouvée (404)

```json
{
  "error": "Session not found",
  "session_id": "invalid-uuid"
}
```

### Erreur de génération (500)

```json
{
  "error": "PDF generation failed",
  "message": "Détails de l'erreur",
  "session_id": "uuid"
}
```

## Structure des données

### Champ `result_json` dans AnalysisSession

```json
{
  "mode": "A",
  "room_id": "uuid",
  "session_id": "uuid",
  "decision": "CORRIGER",
  "audit_id": "SF-AUDIT-20260614-1234",
  "final_report": "DÉCISION FINALE : CORRIGER AVANT MISE EN PROD...",
  "agents": [
    {
      "name": "ScannerAgent",
      "content": "SCAN TERMINÉ : 3 zones sensibles détectées..."
    },
    {
      "name": "ThreatAgent",
      "content": "MENACES IDENTIFIÉES : Injection SQL..."
    },
    {
      "name": "ComplianceAgent",
      "content": "CONFORMITÉ : OWASP A03:2021..."
    },
    {
      "name": "RiskAgent",
      "content": "SCORE DE RISQUE : 7.2/10..."
    },
    {
      "name": "DecisionAgent",
      "content": "DÉCISION : CORRIGER AVANT MISE EN PROD..."
    }
  ]
}
```

### Champ `final_report` (ReportAgent - Mode C)

Pour le Mode C, le ReportAgent génère un rapport complet qui sera stocké dans le champ `final_report`. Ce champ contient le texte formaté prêt pour le PDF.

## Fichiers modifiés

- ✅ [`apps/api/models.py`](apps/api/models.py) - Modèle AnalysisSession créé
- ✅ [`apps/api/views.py`](apps/api/views.py) - Fonctions analyze() et download_pdf() mises à jour
- ✅ [`PDF_INTEGRATION_COMPLETE.md`](PDF_INTEGRATION_COMPLETE.md) - Cette documentation

## Statut final

- ✅ Modèle AnalysisSession créé depuis la branche Le-monstre
- ✅ Fonction analyze() sauvegarde les résultats en base
- ✅ Fonction download_pdf() utilise les vraies données
- ✅ PDF généré avec contenu complet des agents
- ✅ Gestion d'erreurs complète (404, 500)
- ✅ Documentation complète pour les tests

## Prochaines étapes

1. **Personne 2** : Exécuter les migrations en production
2. **Personne 4** : Vérifier que le champ `final_report` du ReportAgent est bien formaté
3. **Personne 5** : Tester le téléchargement PDF depuis l'interface web
4. **Équipe** : Valider le format du PDF avant la démo

---

**Date:** 2026-06-17  
**Auteur:** Personne 5  
**Intégration:** ReportAgent (Personne 4) + AnalysisSession (Personne 2)  
**Statut:** ✅ TERMINÉ - Prêt pour les tests