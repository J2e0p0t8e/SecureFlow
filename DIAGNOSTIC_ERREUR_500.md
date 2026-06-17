# 🔴 Diagnostic Erreur 500 - SecureFlow AI

## Étape 1 : Redémarrer le serveur proprement

```powershell
# Dans le terminal PowerShell
cd SecureFlow
.\.venv\Scripts\Activate.ps1

# Redémarrer avec traceback complet
python manage.py runserver --traceback
```

## Étape 2 : Vérifier les migrations

```powershell
# Vérifier l'état des migrations
python manage.py showmigrations

# Si "api" n'a pas de [X], faire :
python manage.py makemigrations api
python manage.py migrate
```

## Étape 3 : Tester l'import de l'orchestrateur

```powershell
python manage.py shell
```

Puis dans le shell Python :
```python
# Test 1 : Import de base
try:
    from apps.orchestrator.services import run_security_audit_json
    print("✅ Import OK")
except Exception as e:
    print(f"❌ Erreur import : {e}")

# Test 2 : Vérifier les agents
try:
    from apps.agents.band_registry import get_band_client_for
    print("✅ Band registry OK")
except Exception as e:
    print(f"❌ Erreur band : {e}")

# Test 3 : Vérifier le modèle
try:
    from apps.api.models import AnalysisSession
    print("✅ Modèle OK")
    print(f"Sessions en base : {AnalysisSession.objects.count()}")
except Exception as e:
    print(f"❌ Erreur modèle : {e}")

# Quitter
exit()
```

## Étape 4 : Vérifier les variables d'environnement

```powershell
# Vérifier que le fichier .env existe
Test-Path .env

# Afficher les variables (sans les valeurs sensibles)
Get-Content .env | Select-String "GROQ_API_KEY|BAND_"
```

## Étape 5 : Test minimal de l'API

Créez un fichier `test_minimal.py` :

```python
# test_minimal.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secureflow.settings')
django.setup()

from apps.api.views import analyze
from django.http import HttpRequest
import json

# Créer une fausse requête
request = HttpRequest()
request.method = 'POST'
request._body = json.dumps({
    "mode": "A",
    "input_type": "text",
    "content": "test = 1",
    "label": "test"
}).encode('utf-8')

# Tester
try:
    response = analyze(request)
    print(f"✅ Status: {response.status_code}")
    print(f"✅ Response: {response.content.decode()}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
```

Exécuter :
```powershell
python test_minimal.py
```

## Causes probables de l'erreur 500

### Cause 1 : Migrations non faites
**Symptôme :** `OperationalError: no such table: api_analysissession`

**Solution :**
```powershell
python manage.py makemigrations api
python manage.py migrate
```

### Cause 2 : Module orchestrator non trouvé
**Symptôme :** `ModuleNotFoundError: No module named 'apps.orchestrator'`

**Solution :**
```powershell
# Vérifier que le dossier existe
Test-Path apps/orchestrator/services.py

# Si non, vous êtes peut-être sur la mauvaise branche
git branch
# Devrait afficher : * interface
```

### Cause 3 : Variables d'environnement manquantes
**Symptôme :** `KeyError: 'GROQ_API_KEY'` ou erreur Band

**Solution :**
```powershell
# Copier le .env.example
Copy-Item .env.example .env

# Éditer .env avec les vraies valeurs
notepad .env
```

### Cause 4 : Dépendances manquantes
**Symptôme :** `ModuleNotFoundError: No module named 'reportlab'`

**Solution :**
```powershell
pip install -r requirements.txt
```

### Cause 5 : Erreur dans le code de l'orchestrateur
**Symptôme :** Erreur dans `run_security_audit_json`

**Solution :**
Ceci est un problème de Personne 2. Vous pouvez temporairement utiliser un mock :

Créez `apps/api/views_mock.py` :
```python
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def analyze_mock(request):
    """Version mock pour tester l'interface sans l'orchestrateur"""
    data = json.loads(request.body)
    
    return JsonResponse({
        "mode": data.get("mode", "A"),
        "room_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "decision": "CORRIGER",
        "audit_id": "SF-AUDIT-TEST-1234",
        "final_report": "Ceci est un rapport de test.",
        "agents": [
            {"name": "ScannerAgent", "content": "Test scan OK"},
            {"name": "ThreatAgent", "content": "Test menaces OK"},
            {"name": "ComplianceAgent", "content": "Test conformité OK"},
            {"name": "RiskAgent", "content": "Test risque OK"},
            {"name": "DecisionAgent", "content": "Test décision OK"}
        ]
    })
```

Puis dans `apps/api/urls.py`, remplacer temporairement :
```python
from .views_mock import analyze_mock as analyze
```

## Étape 6 : Logs détaillés

Activez les logs Django dans `secureflow/settings.py` :

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

## Commandes de diagnostic rapide

```powershell
# 1. Vérifier Python et environnement
python --version
pip list | Select-String "django|reportlab|groq"

# 2. Vérifier la structure
Get-ChildItem -Recurse -Filter "*.py" | Select-String "def analyze"

# 3. Vérifier les imports
python -c "import django; print(django.get_version())"

# 4. Tester la base de données
python manage.py dbshell
# Puis : .tables (pour SQLite)
# Puis : .quit

# 5. Vérifier les URLs
python manage.py show_urls | Select-String "analyze"
```

## Si rien ne fonctionne

Contactez Personne 2 (Backend) car le problème est probablement dans :
- `apps/orchestrator/services.py`
- `apps/agents/band_registry.py`
- Les variables d'environnement Band

En attendant, utilisez le mock ci-dessus pour tester l'interface.