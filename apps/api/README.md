# Module API - Personne 2

Backend et ingestion de projets pour SecureFlow AI.

## Fichiers créés

### Ingestion (`apps/ingestion/`)
- ✅ `github.py` - Récupération de repos GitHub publics via API
- ✅ `zip_loader.py` - Extraction de fichiers ZIP uploadés

### API (`apps/api/`)
- ✅ `models.py` - Modèle `AnalysisSession` pour stocker les résultats
- ✅ `views.py` - Endpoints API (analyze, session_detail, room_messages, health_check)
- ✅ `urls.py` - Routes API

### Documentation & Tests
- ✅ `scripts/test_api_backend.py` - Script de test complet
- ✅ `docs/API_DOCUMENTATION.md` - Documentation pour Personne 5

## Installation

```powershell
# Activer l'environnement virtuel
.venv\Scripts\Activate.ps1

# Installer les dépendances (si pas déjà fait)
pip install -r requirements.txt

# Créer les migrations
python manage.py makemigrations api

# Appliquer les migrations
python manage.py migrate

# Lancer le serveur
python manage.py runserver
```

## Tests

### Test des modules d'ingestion
```powershell
python scripts/test_api_backend.py
```

### Test de l'API HTTP
```powershell
# Terminal 1: Lancer le serveur
python manage.py runserver

# Terminal 2: Tester avec curl
curl -X POST http://127.0.0.1:8000/api/analyze/ ^
  -H "Content-Type: application/json" ^
  -d "{\"mode\":\"A\",\"input_type\":\"text\",\"content\":\"print(1)\"}"
```

## Endpoints disponibles

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/analyze/` | POST | Lancer une analyse (Mode A/B/C) |
| `/api/session/{id}/` | GET | Récupérer une session |
| `/api/room/{room_id}/messages/` | GET | Messages Band Room (live) |
| `/api/health/` | GET | Health check |

## Intégration avec Mode A (Personne 1)

Le module utilise le service orchestrateur:

```python
from apps.orchestrator.services import run_security_audit_json

result = run_security_audit_json(
    project_content="code...",
    project_label="Mon Projet"
)
```

## Format de réponse

```json
{
  "mode": "A",
  "room_id": "uuid",
  "decision": "CORRIGER",
  "audit_id": "SF-AUDIT-...",
  "final_report": "...",
  "agents": [
    {"name": "ScannerAgent", "content": "..."},
    {"name": "ThreatAgent", "content": "..."}
  ],
  "session_id": 42
}
```

## Prochaines étapes

- [ ] Tester avec un vrai repo GitHub
- [ ] Tester upload ZIP
- [ ] Coordonner avec Personne 5 pour l'interface
- [ ] Ajouter gestion CORS si nécessaire
- [ ] Tests de charge

## Notes

- Mode B et C retournent 501 (pas encore implémentés par Personne 3/4)
- CSRF désactivé pour dev (`@csrf_exempt`) - à sécuriser en prod
- Filtrage des dossiers configuré dans `settings.INGESTION_IGNORE_DIRS`