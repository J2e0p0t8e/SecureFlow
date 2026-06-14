# SecureFlow AI — Guides équipe

Chaque membre a un guide détaillé **autonome** (variables, dossiers, code, tests).

| Personne | Rôle | Guide |
|----------|------|-------|
| **1** | Tech Lead, BaseAgent, Mode A, orchestrateur | [PERSONNE_1_TECH_LEAD.md](./PERSONNE_1_TECH_LEAD.md) |
| **2** | Backend, GitHub, ZIP, API Django | [PERSONNE_2_BACKEND.md](./PERSONNE_2_BACKEND.md) |
| **3** | Mode B — Faisabilité, Archi, Design | [PERSONNE_3_MODE_B_CONCEPTION.md](./PERSONNE_3_MODE_B_CONCEPTION.md) |
| **4** | Mode B — Dev, Sécu, QA + Mode C | [PERSONNE_4_MODE_B_DEV_MODE_C.md](./PERSONNE_4_MODE_B_DEV_MODE_C.md) |
| **5** | Interface, PDF, déploiement, vidéo | [PERSONNE_5_INTERFACE_PDF.md](./PERSONNE_5_INTERFACE_PDF.md) |

---

## Setup commun (toute l'équipe)

1. Cloner le repo
2. `python -m venv .venv` → `.venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt`
4. Copier `.env.example` → `.env` (ou utiliser le `.env` partagé par Personne 1)
5. `python manage.py migrate`

---

## Variables `.env` — vue d'ensemble (13 agents Band)

| Slug `.env` | Agent SecureFlow | Qui configure |
|-------------|------------------|---------------|
| `SCANNER` | ScannerAgent | Personne 1 |
| `THREAT` | ThreatAgent | Personne 1 |
| `COMPLIANCE` | ComplianceAgent | Personne 1 |
| `RISK` | RiskAgent | Personne 1 |
| `DECISION` | DecisionAgent | Personne 1 |
| `FEASIBILITY` | FeasibilityAgent | Personne 3 |
| `ARCHITECT` | ArchitectAgent | Personne 3 |
| `DESIGN` | DesignAgent | Personne 3 |
| `DEV` | DevAgent | Personne 4 |
| `SECURITY` | SecurityAgent | Personne 4 |
| `QA` | QAAgent | Personne 4 |
| `METRICS` | MetricsAgent | Personne 4 |
| `REPORT` | ReportAgent | Personne 4 |

Format pour chaque agent :

```env
BAND_{SLUG}_AGENT_ID=uuid
BAND_{SLUG}_API_KEY=band_a_...
BAND_{SLUG}_HANDLE=secureflow-xxx    # optionnel
```

LLM (une clé suffit pour toute l'équipe en dev) :

```env
GROQ_API_KEY=gsk_...
LLM_PROVIDER=groq
BAND_BASE_URL=https://app.band.ai
```

---

## Autres docs

- [SETUP_BAND_13_AGENTS.md](./SETUP_BAND_13_AGENTS.md) — créer les agents sur band.ai
- [SETUP_ENV.md](./SETUP_ENV.md) — configuration `.env`
- [INTEGRATION_PERSONNE_2.md](./INTEGRATION_PERSONNE_2.md) — contrat API Mode A

---

## Règles équipe

- **Un seul repo**, une branche par personne
- **Prompts** : uniquement dans `apps/agents/prompts.py`
- **Agents** : héritent de `BaseAgent`, ne pas réimplémenter Band/LLM
- **Orchestrateur** : Personne 1 intègre à J5 — n'appelez pas les agents depuis l'API sauf via `services.py`

---

## Message type pour le canal équipe

> Guides prêts dans `docs/` :
> - Pers. 2 → PERSONNE_2_BACKEND.md
> - Pers. 3 → PERSONNE_3_MODE_B_CONCEPTION.md
> - Pers. 4 → PERSONNE_4_MODE_B_DEV_MODE_C.md
> - Pers. 5 → PERSONNE_5_INTERFACE_PDF.md
> Mode A fonctionne : `python manage.py run_mode_a --file scripts/sample_flask.py`
> Questions format API → voir INTEGRATION_PERSONNE_2.md
