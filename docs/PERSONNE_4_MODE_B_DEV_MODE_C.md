# Personne 4 — Mode B (Dev + QA) & Mode C (Métriques + Rapport)

> Tu construis **5 agents** : Dev, Security, QA (Mode B) + Metrics, Report (Mode C). Prompts déjà dans `prompts.py`.

---

## Ton rôle en une phrase

Compléter le pipeline Mode B (agents 4–6) et construire le pipeline Mode C (Metrics + Report).

---

## Dossiers où tu codes

```
apps/agents/mode_b/
  dev.py          ← à créer
  security.py     ← à créer
  qa.py           ← à créer
  __init__.py     ← compléter (pipeline Mode B complet avec Pers. 3)

apps/agents/mode_c/
  metrics.py      ← à créer
  report.py       ← à créer
  __init__.py     ← à créer

apps/orchestrator/   ← Personne 1 intègre mode_b.py / mode_c.py à J5
workflows/           ← idem
```

Branche Git : `personne-4-mode-b-dev-mode-c`

---

## Variables `.env` — tes 5 agents Band

Crée **5 Remote Agents** sur band.ai :

| Agent SecureFlow | Nom Band suggéré | Variables `.env` |
|------------------|------------------|------------------|
| DevAgent | `SecureFlow-Dev` | `BAND_DEV_AGENT_ID`, `BAND_DEV_API_KEY`, `BAND_DEV_HANDLE` |
| SecurityAgent | `SecureFlow-Security` | `BAND_SECURITY_*` |
| QAAgent | `SecureFlow-QA` | `BAND_QA_*` |
| MetricsAgent | `SecureFlow-Metrics` | `BAND_METRICS_*` |
| ReportAgent | `SecureFlow-Report` | `BAND_REPORT_*` |

Exemple :

```env
BAND_DEV_AGENT_ID=uuid
BAND_DEV_API_KEY=band_a_...
BAND_DEV_HANDLE=secureflow-dev

BAND_SECURITY_AGENT_ID=...
BAND_SECURITY_API_KEY=...
BAND_SECURITY_HANDLE=secureflow-security

BAND_QA_AGENT_ID=...
BAND_QA_API_KEY=...
BAND_QA_HANDLE=secureflow-qa

BAND_METRICS_AGENT_ID=...
BAND_METRICS_API_KEY=...
BAND_METRICS_HANDLE=secureflow-metrics

BAND_REPORT_AGENT_ID=...
BAND_REPORT_API_KEY=...
BAND_REPORT_HANDLE=secureflow-report
```

Mode C **réutilise** Scanner, Threat, Compliance (Mode A) — déjà configurés par Personne 1 :

```env
BAND_SCANNER_*   # déjà rempli
BAND_THREAT_*
BAND_COMPLIANCE_*
```

LLM :

```env
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
```

---

## Mode B — tes 3 agents

### Modèle identique à Personne 3

```python
# apps/agents/mode_b/dev.py
from apps.agents.base import AgentResult, BaseAgent
from apps.agents.prompts import DEV_PROMPT


class DevAgent(BaseAgent):
    name = "DevAgent"
    role_description = DEV_PROMPT.strip()

    def run(self, room_id, extra_input=None, next_agent=None):
        return super().run(room_id, extra_input=extra_input, next_agent=next_agent)
```

| Fichier | Prompt | `name` | Début réponse |
|---------|--------|--------|---------------|
| `dev.py` | `DEV_PROMPT` | `DevAgent` | `CODE GÉNÉRÉ :` |
| `security.py` | `SECURITY_PROMPT` | `SecurityAgent` | `AUDIT DU CODE GÉNÉRÉ :` |
| `qa.py` | `QA_PROMPT` | `QAAgent` | `RAPPORT DE VALIDATION :` |

### Pipeline Mode B complet (6 agents)

```python
# apps/agents/mode_b/__init__.py
from apps.agents.mode_b.feasibility import FeasibilityAgent   # Pers. 3
from apps.agents.mode_b.architect import ArchitectAgent
from apps.agents.mode_b.design import DesignAgent
from apps.agents.mode_b.dev import DevAgent
from apps.agents.mode_b.security import SecurityAgent
from apps.agents.mode_b.qa import QAAgent

MODE_B_AGENT_CLASSES = [
    FeasibilityAgent,
    ArchitectAgent,
    DesignAgent,
    DevAgent,
    SecurityAgent,
    QAAgent,
]
```

Test chaîne complète (quand Pers. 3 a livré) :

```python
from apps.orchestrator.base import MultiAgentWorkflowRunner
from apps.agents.mode_b import MODE_B_AGENT_CLASSES

runner = MultiAgentWorkflowRunner(MODE_B_AGENT_CLASSES)
result = runner.run("App todo-list avec auth utilisateur", initial_label="Mode B")
print(result.final_report)
```

---

## Mode C — tes 2 agents + réutilisation Mode A

Mode C = **5 agents** :

```
ScannerAgent → ThreatAgent → ComplianceAgent → MetricsAgent → ReportAgent
  (Pers. 1)      (Pers. 1)      (Pers. 1)         (TOI)          (TOI)
```

### MetricsAgent & ReportAgent

```python
# apps/agents/mode_c/metrics.py
from apps.agents.prompts import METRICS_PROMPT

class MetricsAgent(BaseAgent):
    name = "MetricsAgent"
    role_description = METRICS_PROMPT.strip()
```

```python
# apps/agents/mode_c/report.py
from apps.agents.prompts import REPORT_PROMPT

class ReportAgent(BaseAgent):
    name = "ReportAgent"
    role_description = REPORT_PROMPT.strip()
```

```python
# apps/agents/mode_c/__init__.py
from apps.agents.mode_a.scanner import ScannerAgent
from apps.agents.mode_a.threat import ThreatAgent
from apps.agents.mode_a.compliance import ComplianceAgent
from apps.agents.mode_c.metrics import MetricsAgent
from apps.agents.mode_c.report import ReportAgent

MODE_C_AGENT_CLASSES = [
    ScannerAgent,
    ThreatAgent,
    ComplianceAgent,
    MetricsAgent,
    ReportAgent,
]
```

| Agent | Prompt | Début réponse |
|-------|--------|---------------|
| MetricsAgent | `METRICS_PROMPT` | `MÉTRIQUES DE SÉCURITÉ :` |
| ReportAgent | `REPORT_PROMPT` | `RAPPORT FINAL :` |

---

## Contrat avec Personne 5 — format PDF

`ReportAgent` produit un texte structuré avec 6 sections :

1. RÉSUMÉ EXÉCUTIF
2. TABLEAU DES VULNÉRABILITÉS
3. RECOMMANDATIONS PRIORITAIRES
4. MÉTRIQUES
5. CONCLUSION ET DÉCISION
6. IDENTIFIANT D'AUDIT : `SF-REPORT-[DATE]-[4 chiffres]`

Personne 5 transforme ce texte en PDF ReportLab. **Ne change pas cette structure.**

Fonction à documenter pour Pers. 5 :

```python
# Ce que l'API Mode C renverra (Personne 1 branchera)
{
  "mode": "C",
  "room_id": "...",
  "final_report": "... contenu ReportAgent ...",
  "agents": [...]
}
```

---

## Test Mode C (sans PDF)

```python
from apps.orchestrator.base import MultiAgentWorkflowRunner
from apps.agents.mode_c import MODE_C_AGENT_CLASSES

runner = MultiAgentWorkflowRunner(MODE_C_AGENT_CLASSES)
result = runner.run(
    open("scripts/sample_flask.py").read(),
    initial_label="Audit PDF test",
)
print(result.final_report)
```

Vérifier config agents Mode C :

```powershell
# Nécessite Scanner+Threat+Compliance+Metrics+Report configurés
.venv\Scripts\python manage.py check_config
```

---

## Coordination

| Avec | Sujet |
|------|--------|
| **Personne 3** | Format sortie DesignAgent → entrée DevAgent |
| **Personne 5** | Structure `RAPPORT FINAL :` pour PDF |
| **Personne 1** | Intégration `run_report_pipeline()` à J5 |

---

## Livrables

| Jour | Livrable |
|------|----------|
| J2 | DevAgent + SecurityAgent testés |
| J3 | QAAgent + jonction avec Pers. 3 |
| J4 | MetricsAgent + ReportAgent |
| J5 | Mode C testé bout en bout |

---

## Note importante — SecurityAgent vs ThreatAgent

- **ThreatAgent** (Mode A/C) : audite un projet **existant**
- **SecurityAgent** (Mode B) : audite le **code généré par DevAgent**

Même logique, agents Band **distincts** (`BAND_THREAT_*` vs `BAND_SECURITY_*`).
