# Contrat d'intégration — Personne 2 (Backend API)

Personne 1 livre le **Mode A** prêt à brancher. Personne 2 n'appelle **pas** les agents
directement : elle appelle le service orchestrateur.

## Point d'entrée

```python
from apps.orchestrator.services import run_security_audit_json

# project_content = texte extrait par ingestion (GitHub, ZIP ou paste)
response = run_security_audit_json(
    project_content,
    project_label="mon-repo",
)
```

## Format de réponse JSON

```json
{
  "mode": "A",
  "room_id": "uuid-band-room",
  "decision": "CRITIQUE",
  "audit_id": "SF-AUDIT-20260614-1234",
  "final_report": "... DecisionAgent ...",
  "agents": [
    {"name": "ScannerAgent", "content": "..."},
    {"name": "ThreatAgent", "content": "..."},
    {"name": "ComplianceAgent", "content": "..."},
    {"name": "RiskAgent", "content": "..."},
    {"name": "DecisionAgent", "content": "..."}
  ]
}
```

## Endpoint API suggéré (Personne 2)

```
POST /api/analyze/
Body: {
  "mode": "A",
  "input_type": "github" | "zip" | "text",
  "content": "..."   // ou github_url, ou fichier uploadé → ingestion
}
Response: { ... format ci-dessus ... }
```

Flux côté Personne 2 :

1. Recevoir la requête utilisateur
2. Récupérer le texte du projet (ingestion)
3. Appeler `run_security_audit_json(project_content)`
4. Sauvegarder `room_id` + résultat en base
5. Retourner la réponse à l'interface (Personne 5)

## Band Room live (Personne 5)

L'interface peut interroger la Room avec `room_id` retourné.
Le client Band côté lecture est dans `apps/agents/band_client.py` :

- `BandClient.get_context(room_id)` — historique des messages agents

## Test local (Personne 1)

```powershell
# Vérifier la config
.venv\Scripts\python manage.py run_mode_a --text "print('hello')"

# Avec le sample vulnérable
.venv\Scripts\python manage.py run_mode_a --file scripts/sample_flask.py
```

Variables `.env` requises : voir `docs/PERSONNE_2_BACKEND.md` (5 agents Mode A + `GROQ_API_KEY`).
