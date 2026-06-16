# Script de Démo — SecureFlow AI (4 minutes)

## 🎬 Structure Vidéo

### 0:00 - 0:30 | Introduction (30s)
**Slide 1 : Problème**
> "Chaque jour, des milliers d'applications sont déployées avec des vulnérabilités critiques. Les audits de sécurité manuels prennent des semaines et coûtent cher."

**Slide 2 : Solution**
> "SecureFlow AI : une plateforme d'audit de sécurité automatisée propulsée par 13 agents IA collaborant via Band AI."

---

### 0:30 - 1:00 | Architecture (30s)
**Slide 3 : Architecture Band AI**
```
┌─────────────────────────────────────────┐
│         SecureFlow AI Platform          │
├─────────────────────────────────────────┤
│  Mode A: Security Audit (5 agents)     │
│  Mode B: Dev Pipeline (6 agents)       │
│  Mode C: PDF Report (5 agents)         │
└─────────────────────────────────────────┘
           ↓
    ┌──────────────┐
    │   Band AI    │
    │  13 Agents   │
    └──────────────┘
```

> "13 agents spécialisés communiquent dans des Band Rooms partagées. Chaque agent a son propre compte Band AI et son expertise unique."

---

### 1:00 - 3:30 | Démo Live (2min 30s)

#### 1:00 - 1:45 | Mode A — Security Audit (45s)

**Action :**
1. Ouvrir `https://secureflow-ai.onrender.com/`
2. Sélectionner **Mode A**
3. Coller ce code vulnérable :
```python
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    query = f"SELECT * FROM users WHERE username='{username}'"
    cursor.execute(query)
```
4. Cliquer **"Lancer l'analyse"**

**Narration pendant l'exécution :**
> "Regardez les 5 agents collaborer en temps réel dans la Band Room :
> - **Scanner** détecte les zones sensibles
> - **Threat** identifie les vulnérabilités (SQL Injection critique)
> - **Compliance** mappe vers OWASP Top 10 et CWE
> - **Risk** calcule le score de risque (7.2/10)
> - **Decision** recommande : CORRIGER AVANT PROD"

**Résultat attendu :**
```
✓ Décision : CORRIGER
Audit ID : SF-AUDIT-20260616-XXXX
Score : 7.2/10 (Élevé)
```

---

#### 1:45 - 2:30 | Mode B — Dev Pipeline (45s)

**Action :**
1. Sélectionner **Mode B**
2. Saisir :
```
Créer une boutique e-commerce avec panier, paiement Stripe, 
et gestion des commandes. Stack : Django REST + React + PostgreSQL.
```
3. Cliquer **"Lancer l'analyse"**

**Narration :**
> "Mode B transforme une idée en code complet avec 6 agents :
> - **Feasibility** valide la faisabilité (3 semaines)
> - **Architect** conçoit l'architecture (Django REST + React)
> - **Design** crée l'interface (composants, palette)
> - **Dev** génère 847 lignes de code
> - **Security** audite le code généré (2 vulnérabilités détectées)
> - **QA** valide la qualité (score 72/100)"

**Résultat attendu :**
```
✓ Décision : LIVRABLE PRÊT
Code généré : 847 lignes
Score qualité : 72/100
```

---

#### 2:30 - 3:30 | Mode C — Rapport PDF (1min)

**Action :**
1. Sélectionner **Mode C**
2. Coller le même code vulnérable que Mode A
3. Cliquer **"Lancer l'analyse"**
4. Attendre l'apparition du bouton **"Télécharger le rapport PDF"**
5. Cliquer et ouvrir le PDF

**Narration :**
> "Mode C génère un rapport professionnel complet :
> - **Scanner** cartographie le projet (12 fichiers, 4 zones sensibles)
> - **Threat** liste les vulnérabilités (2 Critiques, 3 Élevées)
> - **Compliance** vérifie OWASP, CWE, RGPD
> - **Metrics** calcule la dette technique (4 jours)
> - **Report** compile tout dans un PDF téléchargeable"

**Montrer le PDF :**
- Page de couverture avec ID audit
- Résultats détaillés par agent
- Recommandations priorisées
- Pied de page professionnel

---

### 3:30 - 4:00 | Conclusion (30s)

**Slide 4 : Valeur Business**
```
✓ Audit automatisé en 30 secondes vs 2 semaines manuelles
✓ 13 agents spécialisés = expertise complète
✓ Rapports PDF professionnels instantanés
✓ Collaboration Band AI = agents qui apprennent ensemble
```

**Slide 5 : Call to Action**
> "SecureFlow AI : sécurisez votre code avant qu'il ne soit trop tard.
> Propulsé par Band AI — la plateforme qui fait collaborer les agents IA."

**Afficher :**
- URL : `https://secureflow-ai.onrender.com/`
- GitHub : `https://github.com/votre-repo/secureflow`
- Band AI : `https://band.ai`

---

## 📋 Checklist Pré-Enregistrement

### Technique
- [ ] App déployée et accessible
- [ ] Les 3 modes testés et fonctionnels
- [ ] PDF se génère correctement
- [ ] Pas d'erreurs dans les logs
- [ ] Temps de réponse < 30s par mode

### Contenu
- [ ] Code vulnérable préparé (copié dans un fichier)
- [ ] Description Mode B préparée
- [ ] Slides créées (5 slides max)
- [ ] Transitions fluides entre modes
- [ ] Musique de fond (optionnel)

### Enregistrement
- [ ] Écran en 1920x1080
- [ ] Navigateur en mode incognito (pas de bookmarks)
- [ ] Zoom navigateur à 100%
- [ ] Fermer notifications/popups
- [ ] Tester audio/micro
- [ ] Enregistrer en 1080p minimum

---

## 🎯 Points Clés à Mentionner

1. **Band AI** : Insister sur la collaboration entre agents
2. **Temps réel** : Montrer les agents qui apparaissent un par un
3. **Expertise** : Chaque agent a sa spécialité
4. **Pratique** : Résultats actionnables (pas juste théoriques)
5. **Professionnel** : PDF prêt à présenter aux clients

---

## 🚫 À Éviter

- Ne pas improviser (préparer les exemples)
- Ne pas attendre trop longtemps (couper si > 30s)
- Ne pas montrer d'erreurs (tester avant)
- Ne pas parler trop vite
- Ne pas oublier de mentionner Band AI

---

## 📊 Exemples de Backup

Si un mode ne fonctionne pas en live, avoir des screenshots/vidéos de backup :

### Mode A Backup
```
Scanner : 3 zones sensibles
Threat : SQL Injection (Critique)
Compliance : OWASP A03:2021
Risk : 7.2/10
Decision : CORRIGER
```

### Mode B Backup
```
Feasibility : 3 semaines
Architect : Django REST + React
Design : Interface minimaliste
Dev : 847 lignes
Security : 2 vulnérabilités
QA : Score 72/100
```

### Mode C Backup
- Avoir un PDF pré-généré à montrer

---

## ⏱️ Timing Précis

| Temps | Section | Durée |
|-------|---------|-------|
| 0:00 | Intro problème | 15s |
| 0:15 | Intro solution | 15s |
| 0:30 | Architecture | 30s |
| 1:00 | Mode A démo | 45s |
| 1:45 | Mode B démo | 45s |
| 2:30 | Mode C démo | 60s |
| 3:30 | Valeur business | 20s |
| 3:50 | Call to action | 10s |
| **4:00** | **FIN** | **Total** |

---

## 🎤 Script Vocal (Optionnel)

Enregistrer la voix séparément puis synchroniser avec la vidéo pour un résultat plus professionnel.

Bonne chance ! 🚀