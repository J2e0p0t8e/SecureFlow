# Créer les 13 agents Band AI — guide hackathon

SecureFlow utilise **13 Remote Agents** sur Band — un par rôle IA.
C'est ce que les juges attendent : une vraie équipe qui collabore via @mentions.

---

## Liste des 13 agents à créer

| # | Nom sur Band (suggéré) | Agent SecureFlow | Mode | Variables `.env` |
|---|------------------------|------------------|------|------------------|
| 1 | `SecureFlow-Scanner` | ScannerAgent | A, C | `BAND_SCANNER_*` |
| 2 | `SecureFlow-Threat` | ThreatAgent | A, C | `BAND_THREAT_*` |
| 3 | `SecureFlow-Compliance` | ComplianceAgent | A, C | `BAND_COMPLIANCE_*` |
| 4 | `SecureFlow-Risk` | RiskAgent | A | `BAND_RISK_*` |
| 5 | `SecureFlow-Decision` | DecisionAgent | A | `BAND_DECISION_*` |
| 6 | `SecureFlow-Feasibility` | FeasibilityAgent | B | `BAND_FEASIBILITY_*` |
| 7 | `SecureFlow-Architect` | ArchitectAgent | B | `BAND_ARCHITECT_*` |
| 8 | `SecureFlow-Design` | DesignAgent | B | `BAND_DESIGN_*` |
| 9 | `SecureFlow-Dev` | DevAgent | B | `BAND_DEV_*` |
| 10 | `SecureFlow-Security` | SecurityAgent | B | `BAND_SECURITY_*` |
| 11 | `SecureFlow-QA` | QAAgent | B | `BAND_QA_*` |
| 12 | `SecureFlow-Metrics` | MetricsAgent | C | `BAND_METRICS_*` |
| 13 | `SecureFlow-Report` | ReportAgent | C | `BAND_REPORT_*` |

> Mode A = 5 agents · Mode B = 6 agents · Mode C = 5 agents (3 partagés avec A)

---

## Étapes sur band.ai (à répéter 13 fois)

### 0. Plan Pro hackathon (une seule fois)

1. [band.ai](https://band.ai) → compte
2. **Settings → Manage Billing → Pro**
3. Code **`BANDHACK26`** → 100% off

### 1. Créer un Remote Agent

Pour **chaque** ligne du tableau :

1. **Agents → Create agent**
2. Type : **Remote Agent**
3. Nom : ex. `SecureFlow-Scanner`
4. **Copie l'API Key** (affichée une seule fois !)
5. Copie l'**Agent UUID** (page paramètres, bas de page)
6. Colle dans `.env` :

```env
BAND_SCANNER_AGENT_ID=uuid-ici
BAND_SCANNER_API_KEY=cle-ici
BAND_SCANNER_HANDLE=          # optionnel — laissé vide = auto via API
```

Répète pour les 13 agents.

---

## Comment ils collaborent dans le code

```
Scanner crée la Room
    → ajoute Threat, Compliance, Risk, Decision comme participants
    → Scanner @mentionne Threat avec son analyse
    → Threat @mentionne Compliance
    → ... jusqu'à Decision (dernier, sans @mention)
```

Chaque agent a **sa propre identité** visible dans la Band Room.

---

## Vérifier ta config

**Mode A seulement** (5 agents — pour tester maintenant) :

```powershell
.venv\Scripts\python manage.py check_config --mode-a-only
```

**Les 13 agents** :

```powershell
.venv\Scripts\python manage.py check_config
```

---

## Ordre recommandé (ne pas tout faire d'un coup)

1. **Aujourd'hui** : crée les **5 agents Mode A** + Groq → teste Mode A
2. **Ensuite** : Personne 3 crée ses 3 agents Mode B (Faisability, Architect, Design)
3. **Ensuite** : Personne 4 crée ses agents (Dev, Security, QA, Metrics, Report)

Tu peux aussi créer les 13 d'un coup si tu préfères — le `.env` est déjà prêt.

---

## Astuce gain de temps

Garde un tableur avec 3 colonnes : `Agent | UUID | API Key`
Band ne remontre **jamais** une API Key — note-la à la création.
