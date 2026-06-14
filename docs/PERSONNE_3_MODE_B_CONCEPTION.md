# Personne 3 — Agents Mode B (Conception)

> Tu construis **3 agents** du Mode B : Faisabilité, Architecture, Design. Les prompts sont **déjà écrits** — tu ne les réinventes pas.

---

## Ton rôle en une phrase

Créer 3 classes Python qui héritent de `BaseAgent`, brancher les 3 agents Band correspondants, assembler le début du pipeline Mode B.

---

## Dossiers où tu codes

```
apps/agents/mode_b/
  feasibility.py    ← à créer
  architect.py      ← à créer
  design.py         ← à créer
  __init__.py       ← exporter les classes + liste pipeline

apps/agents/prompts.py   ← LIRE SEULEMENT (prompts déjà prêts)
apps/agents/base.py      ← LIRE SEULEMENT (moule commun)
```

**Ne touche pas à :** `mode_a/`, `orchestrator/` (Personne 1 intègre à J5), `ingestion/`, `api/`.

Branche Git : `personne-3-mode-b-conception`

---

## Variables `.env` — tes 3 agents Band

Crée **3 Remote Agents** sur [band.ai](https://band.ai) (type Remote Agent, code promo `BANDHACK26`).

| Agent SecureFlow | Nom Band suggéré | Variables `.env` |
|------------------|------------------|------------------|
| FeasibilityAgent | `SecureFlow-Feasibility` | `BAND_FEASIBILITY_AGENT_ID`, `BAND_FEASIBILITY_API_KEY`, `BAND_FEASIBILITY_HANDLE` |
| ArchitectAgent | `SecureFlow-Architect` | `BAND_ARCHITECT_*` |
| DesignAgent | `SecureFlow-Design` | `BAND_DESIGN_*` |

Exemple :

```env
BAND_FEASIBILITY_AGENT_ID=uuid-ici
BAND_FEASIBILITY_API_KEY=band_a_...
BAND_FEASIBILITY_HANDLE=secureflow-feasibility

BAND_ARCHITECT_AGENT_ID=...
BAND_ARCHITECT_API_KEY=...
BAND_ARCHITECT_HANDLE=secureflow-architect

BAND_DESIGN_AGENT_ID=...
BAND_DESIGN_API_KEY=...
BAND_DESIGN_HANDLE=secureflow-design
```

LLM partagé (demande à Personne 1 ou crée ta clé Groq) :

```env
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
BAND_BASE_URL=https://app.band.ai
```

Vérifier :

```powershell
.venv\Scripts\python manage.py check_config
# Doit montrer [OK] pour tes 3 agents (+ les 5 Mode A si .env complet)
```

---

## Comment créer un agent (modèle exact)

Copie **exactement** le pattern Mode A. Exemple FeasibilityAgent :

```python
# apps/agents/mode_b/feasibility.py
from apps.agents.base import AgentResult, BaseAgent
from apps.agents.prompts import FEASIBILITY_PROMPT


class FeasibilityAgent(BaseAgent):
    name = "FeasibilityAgent"
    role_description = FEASIBILITY_PROMPT.strip()

    def run(
        self,
        room_id: str,
        extra_input: str | None = None,
        next_agent: BaseAgent | None = None,
    ) -> AgentResult:
        return super().run(room_id, extra_input=extra_input, next_agent=next_agent)
```

### ArchitectAgent

```python
from apps.agents.prompts import ARCHITECT_PROMPT
# name = "ArchitectAgent"
# role_description = ARCHITECT_PROMPT.strip()
```

### DesignAgent

```python
from apps.agents.prompts import DESIGN_PROMPT
# name = "DesignAgent"
# role_description = DESIGN_PROMPT.strip()
```

---

## `__init__.py` Mode B

```python
# apps/agents/mode_b/__init__.py
from apps.agents.mode_b.architect import ArchitectAgent
from apps.agents.mode_b.design import DesignAgent
from apps.agents.mode_b.feasibility import FeasibilityAgent

MODE_B_CONCEPTION_CLASSES = [
    FeasibilityAgent,
    ArchitectAgent,
    DesignAgent,
]

__all__ = ["ArchitectAgent", "DesignAgent", "FeasibilityAgent", "MODE_B_CONCEPTION_CLASSES"]
```

---

## Prompts disponibles (déjà dans `prompts.py`)

| Clé | Constante | Début de réponse attendu |
|-----|-----------|--------------------------|
| `feasibility` | `FEASIBILITY_PROMPT` | `ANALYSE DE FAISABILITÉ :` |
| `architect` | `ARCHITECT_PROMPT` | `ARCHITECTURE TECHNIQUE :` |
| `design` | `DESIGN_PROMPT` | `GUIDE DESIGN :` |

**Ne modifie pas les prompts** sans accord Personne 1 (format de réponse utilisé par les agents suivants).

---

## Ordre du pipeline Mode B (complet — 6 agents)

```
FeasibilityAgent → ArchitectAgent → DesignAgent → DevAgent → SecurityAgent → QAAgent
     (TOI)              (TOI)           (TOI)      (Pers.4)    (Pers.4)     (Pers.4)
```

Tu livres les **3 premiers**. Personne 4 livre les 3 derniers.

### Passage de contexte

L'orchestrateur (Personne 1) cumule automatiquement le travail précédent dans `extra_input`. Chaque agent reçoit :

- Description utilisateur initiale
- Rapports de tous les agents précédents

Tu n'as **pas** à gérer le passage manuellement si tu utilises `MultiAgentWorkflowRunner` (Personne 1).

---

## Test unitaire de TON agent seul

```python
# scripts/test_feasibility_agent.py (à créer sur le modèle de test_scanner_agent.py)
from apps.agents.mode_b.feasibility import FeasibilityAgent

agent = FeasibilityAgent()
band = agent.band
room = band.create_room()
band.seed_room(room.id, "Je veux une app de réservation de salles", label="Projet")

description = "Application web de réservation de salles de réunion pour une PME."
result = agent.run(room.id, extra_input=description)
print(result.content)
```

```powershell
.venv\Scripts\python scripts/test_feasibility_agent.py
```

Attendu : réponse commençant par `ANALYSE DE FAISABILITÉ :`

---

## Test des 3 agents en chaîne (sans Personne 4)

Script temporaire :

```python
from apps.orchestrator.base import MultiAgentWorkflowRunner
from apps.agents.mode_b import MODE_B_CONCEPTION_CLASSES

runner = MultiAgentWorkflowRunner(MODE_B_CONCEPTION_CLASSES)
result = runner.run(
    "App de réservation de salles pour une PME, 50 utilisateurs.",
    initial_label="Mode B test",
)
for step in result.results:
    print(step.agent_name, step.content[:200])
```

---

## Coordination Personne 4

Avant de coder, alignez-vous sur :

- **DesignAgent** produit un `GUIDE DESIGN :` structuré
- **DevAgent** (Pers. 4) consomme ce format + `ARCHITECTURE TECHNIQUE :`

Pas de changement de format sans message dans le canal équipe.

---

## Livrables

| Jour | Livrable |
|------|----------|
| J2 | FeasibilityAgent testé |
| J2 | ArchitectAgent testé |
| J3 | DesignAgent testé |
| J4 | Pipeline 3 agents testé bout en bout |

Personne 1 branchera `MODE_B_CONCEPTION_CLASSES + MODE_B_DEV_CLASSES` dans l'orchestrateur final à J5.

---

## Erreurs fréquentes

| Problème | Solution |
|----------|----------|
| `Agent Band inconnu : FeasibilityAgent` | Vérifier `name = "FeasibilityAgent"` exact |
| `BAND_FEASIBILITY_API_KEY manquant` | Remplir `.env` |
| Réponse hors format | Ne pas modifier le prompt — le LLM suit `FEASIBILITY_PROMPT` |
| `ModuleNotFoundError: groq` | Utiliser `.venv\Scripts\python` |
