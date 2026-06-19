# SecureFlow AI — installation locale

## Prérequis

- Python 3.11+
- Compte [Band AI](https://band.ai) (code hackathon : `BANDHACK26`)
- Clé [Groq](https://console.groq.com) ou crédits [AI/ML API](https://aimlapi.com)

## Installation

```bash
cd "Band G.U.A.R.D"
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
copy .env.example .env
# Éditer .env avec tes clés
python manage.py migrate
python manage.py runserver
```

## Structure du dépôt

```
apps/
  agents/          ← BaseAgent, clients Band/LLM, tous les agents IA
    mode_a/        ← audit sécurité (Scanner, Threat, Compliance, Risk, Decision)
    mode_b/        ← faisabilité, archi, design, dev, sécu, QA
    mode_c/        ← métriques, rapport
  orchestrator/    ← pipeline Audit-to-Fix
  ingestion/       ← GitHub, ZIP
  api/             ← routes Django
workflows/         ← points d'entrée des pipelines
templates/         ← interface web
scripts/           ← tests manuels
```

## BaseAgent — comment créer un agent

Tous les agents héritent de `apps.agents.base.BaseAgent`.

```python
from apps.agents.base import BaseAgent, AgentResult

class MonAgent(BaseAgent):
    name = "MonAgent"
    role_description = "Ta consigne système ici..."

    def run(self, room_id: str, extra_input: str | None = None) -> AgentResult:
        return super().run(room_id, extra_input=extra_input)
```

Cycle automatique de `BaseAgent.run()` :

1. `GET /agent/chats/{room_id}/context` — lit l'historique Band
2. Appel LLM (Groq ou AI/ML API)
3. `POST /agent/chats/{room_id}/events` — publie la réponse
4. Retourne un `AgentResult`

## Variables d'environnement

Voir `.env.example`. Minimum pour tester un agent :

| Variable | Description |
|----------|-------------|
| `BAND_API_KEY` | Clé API de ton agent Band |
| `BAND_AGENT_ID` | UUID de l'agent Band (optionnel pour REST) |
| `GROQ_API_KEY` | Clé Groq si `LLM_PROVIDER=groq` |
| `AIMLAPI_API_KEY` | Clé AI/ML API si `LLM_PROVIDER=aimlapi` |

## Test Mode A complet (5 agents)

```bash
# Via script
python scripts/test_mode_a.py

# Via commande Django
python manage.py run_mode_a --file scripts/sample_flask.py
python manage.py run_mode_a --text "print('hello')"
```

## Test Mode B (6 agents)

```bash
python manage.py run_mode_b --text "Application todo-list avec authentification"
python scripts/test_mode_b.py
```

## Test Mode C (5 agents)

```bash
python manage.py run_mode_c --file scripts/sample_flask.py
```

## Intégration API

Point d'entrée :

```python
from apps.orchestrator.services import run_security_audit_json

response = run_security_audit_json(project_content, project_label="mon-projet")
```

Voir [docs/API_DOCUMENTATION.md](./docs/API_DOCUMENTATION.md) et [docs/FONCTIONNEMENT_COMPLET.md](./docs/FONCTIONNEMENT_COMPLET.md).

## Test rapide du ScannerAgent seul

```bash
python scripts/test_scanner_agent.py
```

Crée une Band Room, dépose un mini-projet Flask, lance ScannerAgent.

## Documentation

- [docs/SETUP_ENV.md](./docs/SETUP_ENV.md) — configuration `.env`
- [docs/SETUP_BAND_13_AGENTS.md](./docs/SETUP_BAND_13_AGENTS.md) — agents Band
- [docs/FONCTIONNEMENT_COMPLET.md](./docs/FONCTIONNEMENT_COMPLET.md) — architecture et flux
- [docs/API_DOCUMENTATION.md](./docs/API_DOCUMENTATION.md) — endpoints REST
