# 🧪 Guide de Test des 3 Modes SecureFlow AI

**Pour : Personne 5**  
**Date : 2026-06-17**  
**Environnement : Local (http://127.0.0.1:8000/)**

---

## 🚀 Préparation avant les tests

### 1. Démarrer le serveur Django

```powershell
cd SecureFlow
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

### 2. Ouvrir l'interface dans le navigateur

```
http://127.0.0.1:8000/
```

---

## 📋 MODE A — Security Audit (Audit de sécurité)

### ✅ Statut : FONCTIONNEL

### (1) Quoi saisir dans le formulaire

**Sélection du mode :**
- Cliquer sur la carte **"Security Audit"** (icône bouclier violet)

**Agents à sélectionner :**
- ✅ Scanner (détecte les zones sensibles)
- ✅ Threat (identifie les menaces)
- ✅ Compliance (vérifie la conformité OWASP)
- ✅ Risk (calcule le score de risque)
- ✅ Decision (décision finale)

**Données de test recommandées :**

**Option 1 - Injection SQL (vulnérabilité critique) :**
```python
import sqlite3

def login(user, pwd):
    query = f"SELECT * FROM users WHERE user='{user}' AND pwd='{pwd}'"
    conn = sqlite3.connect('db.sqlite')
    return conn.execute(query).fetchone()
```

**Option 2 - Hardcoded credentials (vulnérabilité haute) :**
```python
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"

def connect():
    return db.connect(password=DATABASE_PASSWORD)
```

**Option 3 - Code sécurisé (pour tester VALIDER) :**
```python
import hashlib
from sqlalchemy import text

def login(user, pwd):
    hashed = hashlib.sha256(pwd.encode()).hexdigest()
    query = text("SELECT * FROM users WHERE user=:user AND pwd=:pwd")
    return db.execute(query, {"user": user, "pwd": hashed}).fetchone()
```

### (2) Ce que vous devez voir dans la Band Room

**Séquence d'affichage (animation progressive) :**

1. **Loader initial** (1-2 secondes)
   ```
   🔄 Analyse en cours...
   ```

2. **ScannerAgent** (icône scan violet)
   ```
   SCAN TERMINÉ : 3 zones sensibles détectées
   - Ligne 4 : Concaténation SQL directe
   - Ligne 5 : Utilisation de f-string avec input utilisateur
   - Ligne 6 : Pas de paramétrage de requête
   ```

3. **Communication → ThreatAgent** (flèche animée)
   ```
   Transmission du contexte et des résultats pour analyse...
   ```

4. **ThreatAgent** (icône alerte rouge)
   ```
   MENACES IDENTIFIÉES :
   - Injection SQL possible (CWE-89)
   - Risque d'accès non autorisé
   - Exposition de données sensibles
   ```

5. **Communication → ComplianceAgent**

6. **ComplianceAgent** (icône clipboard bleu)
   ```
   CONFORMITÉ :
   - OWASP A03:2021 - Injection
   - CWE-89 - SQL Injection
   - Non conforme aux standards de sécurité
   ```

7. **Communication → RiskAgent**

8. **RiskAgent** (icône graphique ambre)
   ```
   SCORE DE RISQUE : 7.2/10 — Élevé
   - Impact : Critique (accès base de données)
   - Probabilité : Haute (exploitation facile)
   - Recommandation : Correction immédiate
   ```

9. **Communication → DecisionAgent**

10. **DecisionAgent** (icône marteau vert)
    ```
    DÉCISION : CORRIGER AVANT MISE EN PROD
    
    Le code présente des vulnérabilités critiques qui doivent
    être corrigées avant tout déploiement en production.
    ```

11. **Verdict final** (badge vert avec icône check)
    ```
    ✓ Décision : CORRIGER
    ```

12. **Bouton PDF** (apparaît à la fin)
    ```
    📥 Télécharger le rapport d'analyse
    ```

### (3) Comment vérifier que le PDF se génère bien

**Étape 1 : Cliquer sur le bouton PDF**
- Le bouton vert "📥 Télécharger le rapport d'analyse" apparaît en bas de la Band Room
- Cliquer dessus

**Étape 2 : Vérifier le téléchargement**
- Le navigateur télécharge automatiquement un fichier `secureflow-SF-AUDIT-XXXXXXXX.pdf`
- Vérifier dans votre dossier Téléchargements

**Étape 3 : Ouvrir et vérifier le contenu du PDF**

Le PDF doit contenir :

```
================================================================================
RAPPORT D'ANALYSE SECUREFLOW AI — MODE A
================================================================================

ID Audit       : SF-AUDIT-20260617-XXXX
Session        : [UUID complet]
Date           : 2026-06-17 13:XX:XX
Mode           : Mode A - Audit de sécurité
Type d'entrée  : Code collé
Décision       : CORRIGER
Projet         : mon-projet
Durée          : XXs

================================================================================
RÉSULTATS DES AGENTS
================================================================================

1. ScannerAgent
--------------------------------------------------------------------------------
[Contenu complet du scan]

2. ThreatAgent
--------------------------------------------------------------------------------
[Analyse des menaces]

3. ComplianceAgent
--------------------------------------------------------------------------------
[Vérification conformité]

4. RiskAgent
--------------------------------------------------------------------------------
[Score de risque]

5. DecisionAgent
--------------------------------------------------------------------------------
[Décision finale]

================================================================================
RAPPORT FINAL
================================================================================

[Synthèse complète de l'analyse]

================================================================================

Ce rapport a été généré automatiquement par SecureFlow AI.
Pour plus d'informations : https://secureflow-ai.com
```

**✅ Points de validation :**
- [ ] Le PDF s'ouvre sans erreur
- [ ] L'ID d'audit est présent et unique
- [ ] Les 5 agents sont listés avec leur contenu complet
- [ ] La décision finale est claire (VALIDER/CORRIGER/CRITIQUE)
- [ ] La date et l'heure sont correctes
- [ ] Le formatage est lisible (pas de texte tronqué)

---

## 📋 MODE B — Dev Pipeline (Équipe complète IA)

### ⚠️ Statut : NON IMPLÉMENTÉ (501 Not Implemented)

### (1) Quoi saisir dans le formulaire

**Sélection du mode :**
- Cliquer sur la carte **"Dev Pipeline"** (icône code bleu)

**Agents disponibles :**
- ✅ Feasibility (faisabilité)
- ✅ Architect (architecture)
- ✅ Design (design)
- ✅ Dev (développement)
- ✅ Security (sécurité)
- ✅ QA (tests)

**Données de test recommandées :**

**Description de projet :**
```
Créer une API REST pour gérer des utilisateurs avec :
- Authentification JWT
- CRUD complet (Create, Read, Update, Delete)
- Validation des données
- Tests unitaires
- Documentation Swagger
```

### (2) Ce que vous devez voir dans la Band Room

**Actuellement :**
```json
{
  "error": "Mode B not yet implemented",
  "message": "Mode B (Development Pipeline) is being developed by Personne 3 and 4",
  "mode": "B"
}
```

**Comportement attendu :**
- Message d'erreur affiché dans la Band Room
- Pas de bouton PDF
- Statut HTTP 501

**À venir (quand implémenté par Personne 3/4) :**
1. FeasibilityAgent → Analyse de faisabilité
2. ArchitectAgent → Proposition d'architecture
3. DesignAgent → Maquettes et design
4. DevAgent → Code généré
5. SecurityAgent → Revue de sécurité
6. QAAgent → Plan de tests

### (3) Comment vérifier que le PDF se génère bien

**Actuellement :** Pas de PDF disponible (Mode B non implémenté)

**Quand implémenté :**
- Même processus que Mode A
- Le PDF contiendra le code généré, l'architecture, et les recommandations

---

## 📋 MODE C — Rapport PDF (Livrable professionnel)

### ⚠️ Statut : NON IMPLÉMENTÉ (501 Not Implemented)

### (1) Quoi saisir dans le formulaire

**Sélection du mode :**
- Cliquer sur la carte **"Rapport PDF"** (icône document vert)

**Agents disponibles :**
- ✅ Scanner (scan initial)
- ✅ Threat (menaces)
- ✅ Compliance (conformité)
- ✅ Metrics (métriques)
- ✅ Report (rapport final)

**Données de test recommandées :**

**Code complet d'une application :**
```python
# app.py - Application Flask complète
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    user = request.json.get('username')
    pwd = request.json.get('password')
    
    # Vulnérabilité : SQL Injection
    query = f"SELECT * FROM users WHERE user='{user}' AND pwd='{pwd}'"
    conn = sqlite3.connect('users.db')
    result = conn.execute(query).fetchone()
    
    if result:
        return jsonify({"status": "success", "token": "abc123"})
    return jsonify({"status": "error"}), 401

if __name__ == '__main__':
    app.run(debug=True)  # Vulnérabilité : Debug mode en production
```

### (2) Ce que vous devez voir dans la Band Room

**Actuellement :**
```json
{
  "error": "Mode C not yet implemented",
  "message": "Mode C (Complete Report) is being developed by Personne 4",
  "mode": "C"
}
```

**Comportement attendu :**
- Message d'erreur affiché dans la Band Room
- Pas de bouton PDF
- Statut HTTP 501

**À venir (quand implémenté par Personne 4) :**
1. ScannerAgent → Scan complet du code
2. ThreatAgent → Analyse approfondie des menaces
3. ComplianceAgent → Vérification standards
4. MetricsAgent → Métriques de qualité et sécurité
5. ReportAgent → Rapport professionnel formaté

### (3) Comment vérifier que le PDF se génère bien

**Actuellement :** Pas de PDF disponible (Mode C non implémenté)

**Quand implémenté :**

**Le PDF Mode C sera plus détaillé que Mode A :**

```
================================================================================
RAPPORT PROFESSIONNEL SECUREFLOW AI — MODE C
================================================================================

RÉSUMÉ EXÉCUTIF
- Score global : X/10
- Vulnérabilités critiques : X
- Recommandations prioritaires : X

ANALYSE DÉTAILLÉE
[Sections complètes de chaque agent]

MÉTRIQUES DE QUALITÉ
- Couverture de code : XX%
- Complexité cyclomatique : XX
- Dette technique : XX jours

PLAN D'ACTION
1. [Action prioritaire 1]
2. [Action prioritaire 2]
...

ANNEXES
- Références OWASP
- Standards de conformité
- Glossaire technique
```

**Points de validation spécifiques Mode C :**
- [ ] Résumé exécutif en première page
- [ ] Graphiques et métriques visuelles
- [ ] Plan d'action priorisé
- [ ] Annexes techniques complètes
- [ ] Format professionnel (logo, en-têtes, pieds de page)

---

## 🔍 Tests de validation globaux

### Test 1 : Sélection/désélection d'agents

1. Cliquer sur "Tout sélectionner/désélectionner"
2. Vérifier que tous les agents se cochent/décochent
3. Décocher manuellement 2-3 agents
4. Lancer l'analyse
5. **Résultat attendu :** Seuls les agents cochés apparaissent dans la Band Room

### Test 2 : Changement de mode

1. Sélectionner Mode A
2. Vérifier que les agents Mode A sont affichés (Scanner, Threat, etc.)
3. Sélectionner Mode B
4. Vérifier que les agents Mode B sont affichés (Feasibility, Architect, etc.)
5. Sélectionner Mode C
6. Vérifier que les agents Mode C sont affichés (Scanner, Threat, Metrics, Report)

### Test 3 : Validation des champs

1. Laisser tous les champs vides
2. Cliquer sur "Lancer l'analyse"
3. **Résultat attendu :** Alert "Veuillez entrer un lien GitHub ou du texte."

4. Décocher tous les agents
5. Entrer du code
6. Cliquer sur "Lancer l'analyse"
7. **Résultat attendu :** Alert "Veuillez sélectionner au moins un agent."

### Test 4 : Animation de la Band Room

1. Lancer une analyse Mode A
2. Observer l'animation progressive :
   - [ ] Loader initial apparaît
   - [ ] Messages agents apparaissent un par un (délai ~450ms)
   - [ ] Flèches de communication entre agents
   - [ ] Verdict final avec badge
   - [ ] Bouton PDF apparaît à la fin

### Test 5 : Téléchargement PDF multiple

1. Lancer une première analyse Mode A
2. Télécharger le PDF → noter le nom du fichier
3. Lancer une deuxième analyse Mode A (code différent)
4. Télécharger le PDF → noter le nom du fichier
5. **Résultat attendu :** Les deux PDF ont des noms différents (audit_id unique)

---

## 🐛 Problèmes connus et solutions

### Problème 1 : "ModuleNotFoundError: No module named 'corsheaders'"

**Solution :**
```powershell
pip install django-cors-headers
```

### Problème 2 : "OperationalError: no such table: api_analysissession"

**Solution :**
```powershell
python manage.py makemigrations api
python manage.py migrate
```

### Problème 3 : Le PDF ne se télécharge pas

**Vérifications :**
1. Ouvrir la console du navigateur (F12)
2. Vérifier s'il y a une erreur 404 ou 500
3. Vérifier que `session_id` est présent dans la réponse API
4. Tester l'URL directement : `http://127.0.0.1:8000/api/pdf/{session_id}/`

### Problème 4 : La Band Room reste sur "Analyse en cours..."

**Causes possibles :**
1. Erreur dans l'orchestrateur (vérifier les logs Django)
2. Variables d'environnement manquantes (GROQ_API_KEY, BAND_*)
3. Timeout réseau

**Solution :**
```powershell
# Vérifier les logs
python manage.py runserver
# Observer les erreurs dans le terminal
```

---

## 📊 Checklist de validation finale

### Mode A (Fonctionnel)
- [ ] Formulaire accepte du code
- [ ] Les 5 agents s'affichent dans l'ordre
- [ ] Animation progressive fonctionne
- [ ] Verdict final s'affiche
- [ ] Bouton PDF apparaît
- [ ] PDF se télécharge correctement
- [ ] PDF contient toutes les sections
- [ ] Décision est cohérente (VALIDER/CORRIGER/CRITIQUE)

### Mode B (Non implémenté)
- [ ] Message d'erreur 501 s'affiche
- [ ] Pas de crash de l'interface
- [ ] Retour au formulaire possible

### Mode C (Non implémenté)
- [ ] Message d'erreur 501 s'affiche
- [ ] Pas de crash de l'interface
- [ ] Retour au formulaire possible

### Interface générale
- [ ] Design responsive (mobile/desktop)
- [ ] Animations fluides
- [ ] Pas d'erreurs console JavaScript
- [ ] Icônes Tabler s'affichent correctement
- [ ] Couleurs distinctes par agent
- [ ] Scroll automatique vers Band Room

---

## 🎯 Prochaines étapes

### Pour Personne 5 (vous)
1. ✅ Tester Mode A avec les 3 exemples de code
2. ✅ Vérifier le téléchargement PDF
3. ✅ Valider l'animation de la Band Room
4. 🔄 Tester sur différents navigateurs (Chrome, Firefox, Edge)
5. 🔄 Préparer des captures d'écran pour la démo

### Pour l'équipe
1. **Personne 3/4** : Implémenter Mode B et Mode C
2. **Personne 2** : Implémenter ingestion GitHub et ZIP
3. **Personne 1** : Validation finale avant déploiement

---

**Date de création :** 2026-06-17  
**Auteur :** Personne 5  
**Version :** 1.0  
**Statut :** ✅ Prêt pour les tests