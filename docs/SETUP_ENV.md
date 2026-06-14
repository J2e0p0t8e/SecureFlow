# Configuration `.env` — guide pas à pas

## Fichier à éditer

Ouvre `.env` à la racine du projet (déjà créé). **Ne le commit jamais sur GitHub.**

---

## Partie 1 — Band AI (obligatoire)

### Étape 1 : Compte + plan Pro hackathon

1. Va sur [band.ai](https://band.ai) et crée un compte (ou connecte-toi).
2. **Settings → Manage Billing**
3. Choisis le plan **Pro**
4. Code promo : **`BANDHACK26`** → doit afficher **100% off**
5. Finalise le checkout (carte demandée mais pas débitée si 100% off)

### Étape 2 : Créer un agent « Remote »

1. Dans Band, va sur la page **Agents**
2. Clique **Create agent** (ou équivalent)
3. Type : **Remote Agent** (agent externe qui se connecte via API)
4. Donne-lui un nom clair, ex : `SecureFlow-Orchestrator`
5. **À la création**, une popup affiche ta **`API Key`**
   - ⚠️ **Copie-la immédiatement** — elle ne sera plus affichée
6. Sur la page paramètres de l'agent, copie l'**Agent UUID** (coin bas-droit)

### Étape 3 : Remplir le `.env`

```env
BAND_API_KEY=ta-cle-api-agent-ici
BAND_AGENT_ID=uuid-de-ton-agent-ici
BAND_BASE_URL=https://app.band.ai
```

> **Important** : `BAND_API_KEY` = clé **de l'agent**, pas ta clé utilisateur Band.

### Ce que Band fait dans SecureFlow

- Chaque audit Mode A crée une **Band Room** (salon de discussion)
- Chaque agent (Scanner, Threat, etc.) **écrit** son analyse dans cette Room
- Personne 5 affichera la Room en live dans l'interface
- Tu n'as besoin que **d'un seul agent Band** pour tout le pipeline

---

## Partie 2 — Groq (obligatoire pour commencer)

1. Va sur [console.groq.com](https://console.groq.com)
2. Crée un compte (pas de carte bancaire)
3. **API Keys → Create API Key**
4. Colle dans `.env` :

```env
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
LLM_PROVIDER=groq
```

---

## Partie 3 — AI/ML API (optionnel, plus tard)

Si tu récupères les crédits hackathon lablab :

```env
AIMLAPI_API_KEY=...
LLM_PROVIDER=aimlapi
```

---

## Vérifier que tout marche

```powershell
.venv\Scripts\python manage.py check_config
```

Tu dois voir :
```
Variables .env : OK
Connexion Band : OK (SecureFlow-Orchestrator)
```

Puis lancer un vrai test :

```powershell
.venv\Scripts\python manage.py run_mode_a --file scripts/sample_flask.py
```

---

## Dépannage rapide

| Problème | Solution |
|----------|----------|
| `BAND_API_KEY manquante` | Remplis `.env`, redémarre le terminal |
| Band 401 Unauthorized | Mauvaise clé — recrée une clé agent sur band.ai |
| Groq 401 | Vérifie `GROQ_API_KEY` sur console.groq.com |
| Clé Band perdue | Génère une **nouvelle** clé dans les paramètres de l'agent |
