# Intégration API Personne 5 - TERMINÉE ✅

## Résumé des modifications

Le fichier [`apps/api/views.py`](apps/api/views.py) a été mis à jour pour remplacer les données mock par les vrais appels à l'API de Personne 2 (orchestrateur).

## Changements effectués

### 1. Endpoint `/api/analyze/` - Mode A fonctionnel

**Avant (mock):**
```python
# Données hardcodées pour tous les modes
agents = [{"name": "ScannerAgent", "content": "MOCK DATA"}]
```

**Après (intégration réelle):**
```python
from apps.orchestrator.services import run_security_audit_json

# Appel réel à l'orchestrateur de Personne 1
result = run_security_audit_json(
    project_content,
    project_label=project_label
)
```

### 2. Gestion des types d'input

L'endpoint supporte maintenant:
- ✅ **`input_type: "text"`** - Fonctionne avec l'orchestrateur Mode A
- ⏳ **`input_type: "github"`** - Attend l'implémentation de Personne 2 (ingestion GitHub)
- ⏳ **`input_type: "zip"`** - Attend l'implémentation de Personne 2 (ingestion ZIP)

### 3. Gestion des modes

- ✅ **Mode A** - Audit de sécurité (fonctionnel avec orchestrateur)
- ⏳ **Mode B** - Pipeline de développement (retourne 501 - à implémenter par Personne 3/4)
- ⏳ **Mode C** - Rapport complet (retourne 501 - à implémenter par Personne 4)

### 4. Endpoint `/api/download_pdf/<session_id>/`

Mis à jour avec:
- Documentation claire pour Personne 2
- Code commenté prêt à être activé une fois le modèle `AnalysisSession` créé
- PDF générique temporaire en attendant

## Format de réponse API (Mode A)

```json
{
  "mode": "A",
  "room_id": "uuid-band-room",
  "session_id": "uuid-band-room",
  "decision": "CORRIGER",
  "audit_id": "SF-AUDIT-20260614-1234",
  "final_report": "DÉCISION FINALE : ...",
  "agents": [
    {"name": "ScannerAgent", "content": "SCAN TERMINÉ : ..."},
    {"name": "ThreatAgent", "content": "MENACES IDENTIFIÉES : ..."},
    {"name": "ComplianceAgent", "content": "CONFORMITÉ : ..."},
    {"name": "RiskAgent", "content": "SCORE DE RISQUE : ..."},
    {"name": "DecisionAgent", "content": "DÉCISION : ..."}
  ]
}
```

## Tests

### Test manuel avec curl (Windows PowerShell)

```powershell
# Activer l'environnement virtuel
cd SecureFlow
.\.venv\Scripts\Activate.ps1

# Lancer le serveur Django
python manage.py runserver

# Dans un autre terminal, tester l'API
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

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/analyze/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### Test avec le script Python

```powershell
# Installer les dépendances manquantes si nécessaire
pip install django-cors-headers

# Lancer le test
python scripts/test_api_integration.py
```

## Ce qui reste à faire (Personne 2)

### 1. Créer le modèle de base de données

Créer [`apps/api/models.py`](apps/api/models.py):

```python
from django.db import models

class AnalysisSession(models.Model):
    mode = models.CharField(max_length=1)           # A, B, C
    room_id = models.CharField(max_length=64, unique=True)
    input_type = models.CharField(max_length=20)
    decision = models.CharField(max_length=20, blank=True)
    audit_id = models.CharField(max_length=50, blank=True)
    result_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

Puis:
```powershell
python manage.py makemigrations
python manage.py migrate
```

### 2. Sauvegarder les résultats dans la base

Dans [`apps/api/views.py`](apps/api/views.py), ajouter après l'appel à `run_security_audit_json()`:

```python
from apps.api.models import AnalysisSession

# Sauvegarder en base
session = AnalysisSession.objects.create(
    mode=mode,
    room_id=result["room_id"],
    input_type=input_type,
    decision=result.get("decision", ""),
    audit_id=result.get("audit_id", ""),
    result_json=result
)
```

### 3. Implémenter l'ingestion GitHub

Créer [`apps/ingestion/github.py`](apps/ingestion/github.py):

```python
import requests

def fetch_github_project(url: str, max_files: int = 50) -> str:
    """
    Récupère le contenu d'un repo GitHub public.
    Retourne une représentation textuelle du projet.
    """
    # Extraire owner/repo de l'URL
    # Appeler l'API GitHub
    # Filtrer les fichiers pertinents
    # Retourner le texte agrégé
    pass
```

### 4. Implémenter l'ingestion ZIP

Créer [`apps/ingestion/zip_loader.py`](apps/ingestion/zip_loader.py):

```python
import zipfile
from io import BytesIO

def extract_zip_project(file_bytes: bytes, max_files: int = 50) -> str:
    """
    Extrait et analyse un fichier ZIP.
    Retourne une représentation textuelle du projet.
    """
    # Décompresser le ZIP
    # Ignorer les dossiers inutiles (node_modules, .git, etc.)
    # Retourner le texte agrégé
    pass
```

### 5. Activer le code PDF avec vraies données

Dans [`apps/api/views.py`](apps/api/views.py), fonction `download_pdf()`:
- Décommenter le bloc de code marqué `# TODO: Personne 2`
- Supprimer le code temporaire

## Coordination avec l'équipe

| Personne | Action requise |
|----------|----------------|
| **Personne 2** | Créer modèles DB + ingestion GitHub/ZIP |
| **Personne 3/4** | Implémenter Mode B et Mode C |
| **Personne 5** | Interface web prête à consommer l'API |

## Fichiers modifiés

- ✅ [`apps/api/views.py`](apps/api/views.py) - Intégration orchestrateur
- ✅ [`scripts/test_api_integration.py`](scripts/test_api_integration.py) - Script de test
- ✅ [`INTEGRATION_COMPLETE.md`](INTEGRATION_COMPLETE.md) - Cette documentation

## Statut

- ✅ Mock remplacé par vrais appels API
- ✅ Mode A fonctionnel avec orchestrateur
- ✅ Gestion d'erreurs implémentée
- ✅ Documentation complète
- ⏳ En attente: modèles DB (Personne 2)
- ⏳ En attente: ingestion GitHub/ZIP (Personne 2)
- ⏳ En attente: Mode B/C (Personne 3/4)

---

**Date:** 2026-06-17  
**Auteur:** Personne 5  
**Branche:** monstre (ne pas modifier le travail de Personne 2)