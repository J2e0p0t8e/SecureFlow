# Guide de Déploiement — SecureFlow AI

## 🚀 Déploiement sur Render

### Prérequis
- Compte Render.com (gratuit)
- Repository GitHub avec le code SecureFlow
- Fichier `.env` avec toutes les variables (13 agents Band + GROQ)

### Étapes

#### 1. Préparer le repository
```bash
git add .
git commit -m "Prêt pour déploiement"
git push origin main
```

#### 2. Créer le service sur Render

1. Aller sur https://dashboard.render.com/
2. Cliquer sur **"New +"** → **"Web Service"**
3. Connecter votre repository GitHub
4. Configuration :
   - **Name** : `secureflow-ai`
   - **Region** : Frankfurt (ou le plus proche)
   - **Branch** : `main`
   - **Root Directory** : `SecureFlow`
   - **Runtime** : Python 3
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn secureflow.wsgi --log-file -`

#### 3. Variables d'environnement

Ajouter dans l'onglet **Environment** :

```env
# Django
DJANGO_SECRET_KEY=<générer avec python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DJANGO_DEBUG=False
ALLOWED_HOSTS=secureflow-ai.onrender.com,127.0.0.1

# LLM
GROQ_API_KEY=<votre clé>
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile

# Band AI - Scanner Agent
BAND_SCANNER_API_KEY=<clé>
BAND_SCANNER_AGENT_ID=<id>

# Band AI - Threat Agent
BAND_THREAT_API_KEY=<clé>
BAND_THREAT_AGENT_ID=<id>

# Band AI - Compliance Agent
BAND_COMPLIANCE_API_KEY=<clé>
BAND_COMPLIANCE_AGENT_ID=<id>

# Band AI - Risk Agent
BAND_RISK_API_KEY=<clé>
BAND_RISK_AGENT_ID=<id>

# Band AI - Decision Agent
BAND_DECISION_API_KEY=<clé>
BAND_DECISION_AGENT_ID=<id>

# Band AI - Feasibility Agent
BAND_FEASIBILITY_API_KEY=<clé>
BAND_FEASIBILITY_AGENT_ID=<id>

# Band AI - Architect Agent
BAND_ARCHITECT_API_KEY=<clé>
BAND_ARCHITECT_AGENT_ID=<id>

# Band AI - Design Agent
BAND_DESIGN_API_KEY=<clé>
BAND_DESIGN_AGENT_ID=<id>

# Band AI - Dev Agent
BAND_DEV_API_KEY=<clé>
BAND_DEV_AGENT_ID=<id>

# Band AI - Security Agent
BAND_SECURITY_API_KEY=<clé>
BAND_SECURITY_AGENT_ID=<id>

# Band AI - QA Agent
BAND_QA_API_KEY=<clé>
BAND_QA_AGENT_ID=<id>

# Band AI - Metrics Agent
BAND_METRICS_API_KEY=<clé>
BAND_METRICS_AGENT_ID=<id>

# Band AI - Report Agent
BAND_REPORT_API_KEY=<clé>
BAND_REPORT_AGENT_ID=<id>

# CORS (optionnel)
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=
```

#### 4. Déployer

Cliquer sur **"Create Web Service"**. Le déploiement prend 2-5 minutes.

#### 5. Vérifier

Une fois déployé, ouvrir l'URL : `https://secureflow-ai.onrender.com/`

### Tests post-déploiement

```bash
# Test Mode A
curl -X POST https://secureflow-ai.onrender.com/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"mode":"A","input_type":"text","code":"test SQL injection"}'

# Test PDF
curl https://secureflow-ai.onrender.com/api/pdf/test-id/ -o test.pdf
```

---

## 🐛 Dépannage

### Erreur 500 au démarrage
- Vérifier les logs Render : Dashboard → Logs
- Vérifier que toutes les variables d'environnement sont définies
- Vérifier `ALLOWED_HOSTS` contient l'URL Render

### PDF ne se génère pas
- Vérifier que `reportlab` est dans `requirements.txt`
- Vérifier les logs pour les erreurs ReportLab

### Agents Band ne répondent pas
- Vérifier que les 26 variables Band (13 × 2) sont toutes définies
- Tester les clés API Band localement d'abord

### Timeout
- Le plan gratuit Render a des limites de temps
- Optimiser les appels API ou passer au plan payant

---

## 📊 Monitoring

### Logs en temps réel
```bash
# Via Render Dashboard
Dashboard → Logs → Live Logs
```

### Métriques
- CPU/RAM : Dashboard → Metrics
- Requêtes : Dashboard → Events

---

## 🔄 Mise à jour

```bash
git add .
git commit -m "Mise à jour"
git push origin main
```

Render redéploie automatiquement.

---

## 💰 Coûts

- **Plan gratuit** : 750h/mois, suffisant pour la démo
- **Plan Starter** : 7$/mois pour production
- **Bandwidth** : 100GB/mois gratuit

---

## 🎥 Checklist Démo J7

- [ ] URL publique fonctionnelle
- [ ] Mode A testé avec exemple réel
- [ ] Mode B testé avec description projet
- [ ] Mode C testé + PDF téléchargeable
- [ ] Band Room affiche les agents
- [ ] Pas d'erreurs dans les logs
- [ ] Temps de réponse < 30s par mode
- [ ] Screenshots/vidéo de chaque mode

---

## 📞 Support

- Documentation Render : https://render.com/docs
- Band AI : https://docs.band.ai
- Django : https://docs.djangoproject.com