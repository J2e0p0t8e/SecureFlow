# Personne 2 — Backend & Ingestion de projets

> Tu construis l'API Django et la récupération GitHub/ZIP. **Tu n'écris pas les agents IA** — tu appelles le service livré par Personne 1.

---

## Ton rôle en une phrase

Recevoir GitHub / ZIP / texte → extraire le code → appeler l'orchestrateur → renvoyer le JSON à l'interface.

---

## Dossiers où tu codes

```
apps/ingestion/          ← GitHub, ZIP, filtrage fichiers (TON CODE)
apps/api/                ← modèles Django, vues, routes (TON CODE)
  models.py              ← à créer
  views.py               ← à créer
  urls.py                ← à compléter (vide pour l'instant)
secureflow/settings.py   ← INGESTION_IGNORE_DIRS déjà défini (ne pas dupliquer)
```

**Ne touche pas à :** `apps/agents/`, `apps/orchestrator/` (sauf import du service).

---

## Installation (premier jour)

```powershell
cd "Band G.U.A.R.D"
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Copie le .env de Personne 1 ou remplis au minimum GROQ + agents Mode A
python manage.py migrate
python manage.py runserver
```

Branche Git : `personne-2-backend`

---

## Variables `.env` dont tu as besoin

### LLM (obligatoire — les agents appellent Groq)

```env
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq
```

### Band — Mode A (obligatoire pour lancer un audit)

Personne 1 configure déjà les 5 agents. **Tu utilises le même `.env` partagé** — pas de variables supplémentaires côté backend.

| Variable | Agent |
|----------|-------|
| `BAND_SCANNER_AGENT_ID` / `_API_KEY` / `_HANDLE` | ScannerAgent |
| `BAND_THREAT_*` | ThreatAgent |
| `BAND_COMPLIANCE_*` | ComplianceAgent |
| `BAND_RISK_*` | RiskAgent |
| `BAND_DECISION_*` | DecisionAgent |
| `BAND_BASE_URL=https://app.band.ai` | URL Band |

### Django

```env
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Contrat avec Personne 1 — point d'entrée Mode A

**Ne pas** instancier `ScannerAgent` toi-même. Appelle :

```python
from apps.orchestrator.services import run_security_audit_json

response = run_security_audit_json(
    project_content=texte_du_projet,
    project_label="nom-du-repo",   # optionnel
)
```

### Réponse JSON exacte

```json
{
  "mode": "A",
  "room_id": "uuid-band-room",
  "decision": "CORRIGER",
  "audit_id": "SF-AUDIT-20260614-1234",
  "final_report": "DÉCISION FINALE : ...",
  "agents": [
    {"name": "ScannerAgent", "content": "SCAN TERMINÉ : ..."},
    {"name": "ThreatAgent", "content": "MENACES IDENTIFIÉES : ..."},
    {"name": "ComplianceAgent", "content": "CONFORMITÉ OWASP/CWE : ..."},
    {"name": "RiskAgent", "content": "RISQUE GLOBAL : 7.5/10 ..."},
    {"name": "DecisionAgent", "content": "DÉCISION FINALE : ..."}
  ]
}
```

Sauvegarde en base au minimum : `room_id`, `mode`, `decision`, `final_report`, JSON complet.

---

## Module 1 — Ingestion (`apps/ingestion/`)

### 1.1 GitHub (repo public)

- Entrée : URL `https://github.com/user/repo`
- API GitHub **gratuite sans token** pour repos publics
- Endpoints utiles :
  - `GET https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1`
  - Télécharger chaque fichier texte via `raw.githubusercontent.com`

Fonction à livrer :

```python
# apps/ingestion/github.py
def fetch_github_project(url: str, max_files: int = 50) -> str:
    """Retourne une représentation textuelle : chemin + contenu par fichier."""
```

### 1.2 ZIP upload

```python
# apps/ingestion/zip_loader.py
def extract_zip_project(file_bytes: bytes, max_files: int = 50) -> str:
    """Décompresse, ignore les dossiers inutiles, retourne le texte agrégé."""
```

Dossiers à **ignorer** (déjà dans `settings.INGESTION_IGNORE_DIRS`) :

```
.git, node_modules, __pycache__, .venv, venv, dist, build, vendor, ...
```

### 1.3 Texte direct

Pas de transformation — passer le string tel quel.

### 1.4 Priorisation (gros projets)

Si > 50 fichiers : prioriser `*.py`, `*.js`, `*.ts`, `*.env*`, `requirements.txt`, `package.json`, `Dockerfile`, README.

---

## Module 2 — API Django (`apps/api/`)

### Endpoint principal suggéré

```
POST /api/analyze/
Content-Type: application/json
```

Body :

```json
{
  "mode": "A",
  "input_type": "github",
  "github_url": "https://github.com/user/repo"
}
```

Ou :

```json
{
  "mode": "A",
  "input_type": "text",
  "content": "code ici..."
}
```

Ou `multipart/form-data` avec `input_type: "zip"` + fichier.

### Vue Django (exemple)

```python
# apps/api/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.ingestion.github import fetch_github_project
from apps.orchestrator.services import run_security_audit_json

@csrf_exempt  # à remplacer par CSRF propre en prod
def analyze(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    body = json.loads(request.body)
    mode = body.get("mode", "A")
    input_type = body.get("input_type")

    if mode != "A":
        return JsonResponse({"error": "Mode B/C pas encore branché"}, status=501)

    if input_type == "github":
        content = fetch_github_project(body["github_url"])
    elif input_type == "text":
        content = body["content"]
    elif input_type == "zip":
        content = extract_zip_project(request.FILES["file"].read())
    else:
        return JsonResponse({"error": "input_type invalide"}, status=400)

    result = run_security_audit_json(content, project_label=body.get("label", "Projet"))
    return JsonResponse(result)
```

### Routes (`apps/api/urls.py`)

```python
from django.urls import path
from apps.api.views import analyze

urlpatterns = [
    path("analyze/", analyze, name="analyze"),
]
```

---

## Modèle Django suggéré (`apps/api/models.py`)

```python
class AnalysisSession(models.Model):
    mode = models.CharField(max_length=1)           # A, B, C
    room_id = models.CharField(max_length=64)
    input_type = models.CharField(max_length=20)
    decision = models.CharField(max_length=20, blank=True)
    audit_id = models.CharField(max_length=50, blank=True)
    result_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## Tests sans l'interface (Personne 5)

```powershell
# Test ingestion + Mode A manuellement
.venv\Scripts\python manage.py run_mode_a --file scripts/sample_flask.py

# Quand ton API est prête
curl -X POST http://127.0.0.1:8000/api/analyze/ ^
  -H "Content-Type: application/json" ^
  -d "{\"mode\":\"A\",\"input_type\":\"text\",\"content\":\"print(1)\"}"
```

---

## Coordination

| Avec | Sujet |
|------|--------|
| **Personne 1** | Format JSON final, erreurs orchestrateur |
| **Personne 5** | Contrat requête/réponse API, CORS, polling `room_id` |

Personne 5 appellera `POST /api/analyze/`. Documente ton API dans un commentaire ou `docs/API.md` quand c'est stable.

---

## Livrables par jour (rappel)

| Jour | Livrable |
|------|----------|
| J1 | Modèles + routes vides |
| J2 | GitHub fonctionnel |
| J3 | ZIP fonctionnel |
| J4 | API complète + test avec Personne 5 |

---

## Erreurs fréquentes

| Erreur | Cause |
|--------|-------|
| `BAND_* manquant` | `.env` incomplet — voir Personne 1 |
| `GROQ_API_KEY manquante` | Ajouter clé Groq |
| Timeout | Projet trop gros — réduire `max_files` |
| GitHub 404 | Repo privé ou branche pas `main` |
