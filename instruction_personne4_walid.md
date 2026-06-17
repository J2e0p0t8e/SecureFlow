# Instructions Personne 4 (Walid) — Mode B Dev + Mode C

## ✅ Ce qui a été fait

J'ai créé **5 agents** pour SecureFlow AI :

### Mode B (3 agents)
1. **DevAgent** ([`apps/agents/mode_b/dev.py`](apps/agents/mode_b/dev.py))
   - Génère le code source du projet
   - Utilise le prompt `DEV_PROMPT`
   - Commence sa réponse par : `CODE GÉNÉRÉ :`
   - Inclut intentionnellement 3-4 vulnérabilités pour test

2. **SecurityAgent** ([`apps/agents/mode_b/security.py`](apps/agents/mode_b/security.py))
   - Audite le code généré par DevAgent
   - Utilise le prompt `SECURITY_PROMPT`
   - Commence sa réponse par : `AUDIT DU CODE GÉNÉRÉ :`
   - Identifie les vulnérabilités avec niveau 🔴🟠🟡🟢

3. **QAAgent** ([`apps/agents/mode_b/qa.py`](apps/agents/mode_b/qa.py))
   - Valide la qualité du projet
   - Utilise le prompt `QA_PROMPT`
   - Commence sa réponse par : `RAPPORT DE VALIDATION :`
   - Définit les tests à implémenter

### Mode C (2 agents)
4. **MetricsAgent** ([`apps/agents/mode_c/metrics.py`](apps/agents/mode_c/metrics.py))
   - Calcule les métriques de sécurité
   - Utilise le prompt `METRICS_PROMPT`
   - Commence sa réponse par : `MÉTRIQUES DE SÉCURITÉ :`
   - Score /100, dette technique, maturité

5. **ReportAgent** ([`apps/agents/mode_c/report.py`](apps/agents/mode_c/report.py))
   - Génère le rapport PDF final
   - Utilise le prompt `REPORT_PROMPT`
   - Commence sa réponse par : `RAPPORT FINAL :`
   - Structure en 6 sections pour Personne 5

### Fichiers de configuration
- [`apps/agents/mode_b/__init__.py`](apps/agents/mode_b/__init__.py) : Pipeline Mode B (mes 3 agents + 3 de Personne 3)
- [`apps/agents/mode_c/__init__.py`](apps/agents/mode_c/__init__.py) : Pipeline Mode C complet (5 agents)

---

## 🔧 Configuration Band AI

Tous mes agents utilisent les clés du fichier [`.env`](.env) :

✅ **Vérification effectuée** : `python manage.py check_config` → 13/13 agents connectés

---

## 📋 Instructions pour les autres personnes

### Pour Personne 3 (Mode B Conception)
Vous devez créer 3 agents dans [`apps/agents/mode_b/`](apps/agents/mode_b/) :
- `feasibility.py` → FeasibilityAgent
- `architect.py` → ArchitectAgent  
- `design.py` → DesignAgent

Ensuite, mettez à jour [`apps/agents/mode_b/__init__.py`](apps/agents/mode_b/__init__.py) :
```python
from apps.agents.mode_b.feasibility import FeasibilityAgent
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

### Pour Personne 1 (Tech Lead / Orchestrateur)
Mes agents sont prêts pour intégration dans l'orchestrateur :

**Mode B** : Créer `apps/orchestrator/mode_b.py`
```python
from apps.orchestrator.base import MultiAgentWorkflowRunner
from apps.agents.mode_b import MODE_B_AGENT_CLASSES

def run_mode_b_pipeline(project_description: str):
    runner = MultiAgentWorkflowRunner(MODE_B_AGENT_CLASSES)
    return runner.run(project_description, initial_label="Mode B")
```

**Mode C** : Créer `apps/orchestrator/mode_c.py`
```python
from apps.orchestrator.base import MultiAgentWorkflowRunner
from apps.agents.mode_c import MODE_C_AGENT_CLASSES

def run_mode_c_pipeline(project_content: str):
    runner = MultiAgentWorkflowRunner(MODE_C_AGENT_CLASSES)
    return runner.run(project_content, initial_label="Mode C - Rapport PDF")
```

### Pour Personne 5 (Interface + PDF)
Le **ReportAgent** génère un rapport structuré en **6 sections** :

1. **RÉSUMÉ EXÉCUTIF** (3 phrases pour non-technique)
2. **TABLEAU DES VULNÉRABILITÉS** (faille / niveau / OWASP)
3. **RECOMMANDATIONS PRIORITAIRES** (3 actions urgentes)
4. **MÉTRIQUES** (score /100, dette technique, maturité)
5. **CONCLUSION ET DÉCISION** (🔴 CRITIQUE / 🟠 CORRIGER / 🟡 SURVEILLER / 🟢 PROPRE)
6. **IDENTIFIANT D'AUDIT** : `SF-REPORT-[DATE]-[4 chiffres]`

Vous devez transformer ce texte en PDF avec ReportLab.

**Exemple de sortie ReportAgent** :
```
RAPPORT FINAL :

1. RÉSUMÉ EXÉCUTIF
Le projet présente 2 vulnérabilités critiques...

2. TABLEAU DES VULNÉRABILITÉS
- SQL Injection (🔴 CRITIQUE) → OWASP A03:2021
- XSS (🟠 ÉLEVÉ) → CWE-79

3. RECOMMANDATIONS PRIORITAIRES
1. Corriger la SQL Injection dans auth.py ligne 45
2. Implémenter la validation des entrées
3. Ajouter des tests de sécurité

4. MÉTRIQUES
Score de sécurité : 45/100
Dette technique : ÉLEVÉE (5 jours)
Maturité : EN PROGRESSION

5. CONCLUSION ET DÉCISION
🔴 CRITIQUE — Ne pas déployer

6. IDENTIFIANT D'AUDIT
SF-REPORT-2026-06-16-7392
```

---

## 🧪 Tests disponibles

### Test Mode C complet
```bash
python scripts/test_mode_c.py
```

### Test d'un agent individuel
```python
from apps.agents.mode_c.metrics import MetricsAgent

agent = MetricsAgent()
result = agent.run(room_id="test-room-123")
print(result.content)
```

### Vérifier la configuration
```bash
python manage.py check_config
```

---

## 🔄 Fonctionnement des agents

Tous mes agents héritent de [`BaseAgent`](apps/agents/base.py) et suivent ce cycle :

1. **Lecture du contexte** : `GET /agent/chats/{room_id}/context` via Band API
2. **Appel LLM** : Groq (llama-3.3-70b-versatile) avec le prompt système
3. **Publication** : `POST /agent/chats/{room_id}/events` pour envoyer la réponse
4. **Retour** : `AgentResult` avec le contenu généré

### Exemple de flux Mode C
```
ScannerAgent (Pers. 1)
    ↓ SCAN TERMINÉ : ...
ThreatAgent (Pers. 1)
    ↓ MENACES IDENTIFIÉES : ...
ComplianceAgent (Pers. 1)
    ↓ CONFORMITÉ OWASP/CWE : ...
MetricsAgent (MOI)
    ↓ MÉTRIQUES DE SÉCURITÉ : ...
ReportAgent (MOI)
    ↓ RAPPORT FINAL : ...
```

Chaque agent lit **tout l'historique** de la Band Room et ajoute sa contribution.

---

## 📁 Structure des fichiers créés

```
apps/agents/mode_b/
├── dev.py          ← DevAgent (MOI)
├── security.py     ← SecurityAgent (MOI)
├── qa.py           ← QAAgent (MOI)
└── __init__.py     ← Pipeline Mode B (mis à jour)

apps/agents/mode_c/
├── metrics.py      ← MetricsAgent (MOI)
├── report.py       ← ReportAgent (MOI)
└── __init__.py     ← Pipeline Mode C (créé)
```

---

## ✅ Checklist de validation

- [x] 5 agents créés et testés
- [x] Prompts importés depuis [`apps/agents/prompts.py`](apps/agents/prompts.py)
- [x] Configuration Band validée (13/13 agents)
- [x] Pipelines Mode B et Mode C définis
- [x] Documentation pour les autres personnes
- [ ] Intégration orchestrateur (Personne 1)
- [ ] Tests bout en bout Mode B (avec Personne 3)
- [ ] Génération PDF (Personne 5)

---

## 🚀 Prochaines étapes

1. **Personne 3** : Créer FeasibilityAgent, ArchitectAgent, DesignAgent
2. **Personne 1** : Intégrer mes agents dans l'orchestrateur
3. **Personne 5** : Transformer la sortie ReportAgent en PDF
4. **Tests** : Valider les pipelines Mode B et Mode C bout en bout

---

**Contact** : Walid (Personne 4)  
**Date** : 2026-06-16  
**Status** : ✅ Livraison complète