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
    mode_a/        ← Personne 1 — audit sécurité (5 agents)
    mode_b/        ← Personne 3 — faisabilité, archi, design
    mode_c/        ← Personne 4 — métriques, rapport
  orchestrator/    ← Personne 1 (J2) — enchaîne les agents
  ingestion/       ← Personne 2 — GitHub, ZIP
  api/             ← Personne 2 — routes Django
workflows/         ← définitions Mode A / B / C
templates/         ← Personne 5 — interface web
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

## Intégration API (Personne 2)

Voir [docs/INTEGRATION_PERSONNE_2.md](./docs/INTEGRATION_PERSONNE_2.md).

Point d'entrée :

```python
from apps.orchestrator.services import run_security_audit_json

response = run_security_audit_json(project_content, project_label="mon-projet")
```

## Test rapide du ScannerAgent seul

```bash
python scripts/test_scanner_agent.py
```

Crée une Band Room, dépose un mini-projet Flask, lance ScannerAgent.

## Branches Git (règle équipe)

- Une branche par personne : `personne-1-orchestrator`, `personne-2-backend`, etc.
- Pas de push direct sur `main` sans validation Personne 1

## Guides équipe (autonomes)

Voir **[docs/README_EQUIPE.md](./docs/README_EQUIPE.md)** — un fichier `.md` par membre avec variables, dossiers, code et tests.

## Contacts

| Rôle | Dossiers principaux |
|------|---------------------|
| Personne 1 (Tech Lead) | `apps/agents/base.py`, `apps/orchestrator/`, `apps/agents/mode_a/` |
| Personne 2 (Backend) | `apps/ingestion/`, `apps/api/` |
| Personne 3 (Mode B conception) | `apps/agents/mode_b/` |
| Personne 4 (Mode B dev + Mode C) | `apps/agents/mode_b/`, `apps/agents/mode_c/` |
| Personne 5 (UI + PDF) | `templates/`, déploiement |
