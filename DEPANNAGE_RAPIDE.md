# 🔧 Dépannage Rapide - SecureFlow AI

## ✅ Problème résolu : "Rien ne se passe"

**Cause :** Le JavaScript envoyait `code` mais l'API attendait `content`

**Solution :** Corrigé dans [`templates/index.html`](templates/index.html:359) ligne 359

---

## 🚀 Étapes pour tester maintenant

### 1. Rafraîchir la page
```
Appuyez sur Ctrl+F5 (ou Cmd+Shift+R sur Mac)
```
Cela force le rechargement du JavaScript mis à jour.

### 2. Ouvrir la console du navigateur
```
Appuyez sur F12
Onglet "Console"
```

### 3. Tester avec ce code simple

**Dans le champ "Code ou description" :**
```python
api_key = "sk-secret-key-hardcoded"

def login(user, pwd):
    query = f"SELECT * FROM users WHERE user='{user}' AND pwd='{pwd}'"
    return query
```

**Cliquer sur "Lancer l'analyse"**

---

## 📊 Ce que vous devriez voir

### Dans la console (F12)
```
POST http://127.0.0.1:8000/api/analyze/ 200 OK
```

### Dans la Band Room
1. **Loader** (1-2 secondes)
   ```
   🔄 Analyse en cours...
   ```

2. **Messages des agents** (apparaissent progressivement)
   - ScannerAgent (violet)
   - ThreatAgent (rouge)
   - ComplianceAgent (bleu)
   - RiskAgent (ambre)
   - DecisionAgent (vert)

3. **Verdict final**
   ```
   ✓ Décision : CORRIGER
   ```

4. **Bouton PDF**
   ```
   📥 Télécharger le rapport d'analyse
   ```

---

## ❌ Si ça ne marche toujours pas

### Erreur 1 : "content is required for input_type=text"

**Cause :** Le cache du navigateur n'est pas vidé

**Solution :**
1. Ctrl+Shift+Delete (ouvrir les paramètres de cache)
2. Cocher "Images et fichiers en cache"
3. Cliquer sur "Effacer les données"
4. Rafraîchir la page (Ctrl+F5)

### Erreur 2 : "Failed to fetch" ou "Network error"

**Cause :** Le serveur Django n'est pas démarré

**Solution :**
```powershell
cd SecureFlow
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

Vérifier que vous voyez :
```
Starting development server at http://127.0.0.1:8000/
```

### Erreur 3 : "ModuleNotFoundError: No module named 'apps.orchestrator'"

**Cause :** Dépendances manquantes ou environnement virtuel non activé

**Solution :**
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Erreur 4 : La Band Room reste sur "Analyse en cours..."

**Cause :** Erreur côté serveur (orchestrateur)

**Solution :**
1. Regarder le terminal où tourne `python manage.py runserver`
2. Chercher les erreurs en rouge
3. Vérifier les variables d'environnement :

```powershell
# Vérifier le fichier .env
cat .env

# Doit contenir :
GROQ_API_KEY=...
BAND_SCANNER_AGENT_ID=...
BAND_THREAT_AGENT_ID=...
# etc.
```

### Erreur 5 : "500 Internal Server Error"

**Cause :** Base de données non migrée

**Solution :**
```powershell
python manage.py makemigrations api
python manage.py migrate
```

---

## 🔍 Vérification étape par étape

### Étape 1 : Vérifier que le serveur répond
```powershell
# Dans PowerShell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -Method GET
```

**Résultat attendu :** Code 200 OK

### Étape 2 : Tester l'API directement
```powershell
$body = @{
    mode = "A"
    input_type = "text"
    content = "api_key = 'hardcoded'"
    label = "test"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/analyze/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**Résultat attendu :** JSON avec `room_id`, `agents`, `decision`

### Étape 3 : Vérifier la console JavaScript
1. Ouvrir F12
2. Onglet "Network"
3. Cliquer sur "Lancer l'analyse"
4. Chercher la requête `analyze/`
5. Cliquer dessus
6. Onglet "Response" → voir le JSON retourné

---

## 📝 Logs utiles

### Activer les logs détaillés Django
```python
# Dans secureflow/settings.py (temporaire pour debug)
DEBUG = True

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### Voir les requêtes SQL
```powershell
python manage.py shell

# Dans le shell Python
from apps.api.models import AnalysisSession
import logging
logging.basicConfig(level=logging.DEBUG)

# Tester une requête
sessions = AnalysisSession.objects.all()
print(sessions)
```

---

## ✅ Checklist de validation

Avant de dire "ça marche" :

- [ ] Le serveur Django démarre sans erreur
- [ ] La page http://127.0.0.1:8000/ s'affiche
- [ ] Le formulaire accepte du code
- [ ] Le bouton "Lancer l'analyse" est cliquable
- [ ] La Band Room s'affiche
- [ ] Les messages des agents apparaissent un par un
- [ ] Le verdict final s'affiche
- [ ] Le bouton PDF apparaît
- [ ] Le PDF se télécharge
- [ ] Le PDF s'ouvre et contient les données

---

## 🆘 Besoin d'aide ?

### Vérifier les logs en temps réel
```powershell
# Terminal 1 : Serveur Django
python manage.py runserver

# Terminal 2 : Logs en direct
Get-Content -Path ".\logs\django.log" -Wait -Tail 50
```

### Tester avec curl (alternative)
```bash
curl -X POST http://127.0.0.1:8000/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"mode":"A","input_type":"text","content":"test","label":"test"}'
```

---

## 🎯 Test minimal qui DOIT fonctionner

Si tout est bien configuré, ce test doit passer :

```powershell
# 1. Démarrer le serveur
python manage.py runserver

# 2. Dans un autre terminal
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/analyze/" `
    -Method POST `
    -ContentType "application/json" `
    -Body '{"mode":"A","input_type":"text","content":"test = 1","label":"test"}'

# 3. Vérifier la réponse
$response.room_id  # Doit afficher un UUID
$response.agents   # Doit afficher un tableau
$response.decision # Doit afficher VALIDER/CORRIGER/CRITIQUE
```

Si ce test échoue, le problème est dans le backend (Personne 2), pas dans l'interface.

---

**Date :** 2026-06-17  
**Auteur :** Personne 5  
**Statut :** ✅ Bug corrigé - Prêt pour les tests