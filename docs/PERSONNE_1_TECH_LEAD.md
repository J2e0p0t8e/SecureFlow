# Personne 1 — Tech Lead & Architecture

> **Statut actuel : Mode A livré.** Ce document sert de référence et liste ce qui reste pour l'intégration finale (J5–J7).

---

## Ton rôle

- Architecture globale et cohérence du dépôt
- `BaseAgent`, orchestrateur, Mode A (5 agents)
- Intégration des modules des autres membres
- README final + soumission lablab.ai

---

## Dossiers que tu possèdes

```
apps/agents/base.py          ← moule commun (NE PAS casser sans prévenir l'équipe)
apps/agents/band_client.py
apps/agents/band_registry.py
apps/agents/llm.py
apps/agents/prompts.py       ← 13 prompts centralisés
apps/agents/mode_a/          ← 5 agents Mode A (TERMINÉ)
apps/orchestrator/           ← orchestrateur Mode A (TERMINÉ)
workflows/mode_a.py
```

---

## Variables `.env` — les tiennes (Mode A)

Tu as déjà configuré ces 5 agents Band + Groq :

| Agent SecureFlow | Variables `.env` |
|------------------|------------------|
| ScannerAgent | `BAND_SCANNER_AGENT_ID`, `BAND_SCANNER_API_KEY`, `BAND_SCANNER_HANDLE` |
| ThreatAgent | `BAND_THREAT_*` |
| ComplianceAgent | `BAND_COMPLIANCE_*` |
| RiskAgent | `BAND_RISK_*` |
| DecisionAgent | `BAND_DECISION_*` |

LLM (partagé par toute l'équipe) :

```env
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq
BAND_BASE_URL=https://app.band.ai
```

---

## Ce que tu as livré (ne pas refaire)

- [x] Structure Django
- [x] `BaseAgent` + clients Band/LLM
- [x] 5 agents Mode A + prompts
- [x] Orchestrateur multi-agents Band (`MultiAgentWorkflowRunner`)
- [x] Service API : `run_security_audit_json()`
- [x] Commandes : `manage.py run_mode_a`, `manage.py check_config`

### Test Mode A

```powershell
.venv\Scripts\Activate.ps1
.venv\Scripts\python manage.py check_config --mode-a-only
.venv\Scripts\python manage.py run_mode_a --file scripts/sample_flask.py
```

---

## Ce qu'il te reste à faire (J5–J7)

### J5 — Intégration

1. Brancher l'API de **Personne 2** dans `secureflow/urls.py` (déjà prévu : `path("api/", ...)`)
2. Quand **Personne 3/4** livrent Mode B/C :
   - Créer `apps/orchestrator/mode_b.py` et `mode_c.py` (copie de `mode_a.py`)
   - Créer `workflows/mode_b.py` et `mode_c.py`
   - Ajouter `run_dev_pipeline()` et `run_report_pipeline()` dans `services.py`
3. Tester les 3 modes depuis le même point d'entrée API

### J6 — Tests globaux

- Tester Mode A/B/C avec de vrais projets
- Corriger les bugs d'intégration (sans réécrire le code des autres)

### J7 — Soumission

- README GitHub complet
- Formulaire lablab.ai (URL démo, lien GitHub, vidéo)
- Superviser la soumission avant deadline

---

## Règles Git

- Branche : `personne-1-orchestrator`
- Ne pas push sur `main` sans validation
- Ne pas modifier le code des autres sauf urgence d'intégration

---

## Contacts équipe

| Membre | Guide |
|--------|-------|
| Personne 2 | `docs/PERSONNE_2_BACKEND.md` |
| Personne 3 | `docs/PERSONNE_3_MODE_B_CONCEPTION.md` |
| Personne 4 | `docs/PERSONNE_4_MODE_B_DEV_MODE_C.md` |
| Personne 5 | `docs/PERSONNE_5_INTERFACE_PDF.md` |
