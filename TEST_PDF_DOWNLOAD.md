# Test du Téléchargement PDF — SecureFlow AI

## 🎯 Objectif
Vérifier que le bouton de téléchargement PDF fonctionne correctement en Mode C.

---

## 📋 Étapes de Test

### 1. Démarrer le serveur
```bash
cd SecureFlow
.venv\Scripts\Activate.ps1
python manage.py runserver
```

### 2. Ouvrir l'application
Naviguer vers : **http://127.0.0.1:8000/**

### 3. Sélectionner Mode C
- Cliquer sur la carte **"Rapport PDF"** (verte)
- Vérifier que les agents Mode C sont affichés dans le sélecteur

### 4. Saisir des données de test
**Option A — Code vulnérable :**
```python
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    query = f"SELECT * FROM users WHERE username='{username}'"
    cursor.execute(query)
```

**Option B — URL GitHub :**
```
https://github.com/pallets/flask
```

### 5. Lancer l'analyse
- Cliquer sur **"Lancer l'analyse"**
- Attendre l'affichage des 5 agents (Scanner, Threat, Compliance, Metrics, Report)

### 6. Vérifier le bouton PDF
Après l'affichage de tous les agents, un **bouton vert** doit apparaître :
```
📥 Télécharger le rapport PDF
```

### 7. Télécharger le PDF
- Cliquer sur le bouton
- Le PDF doit s'ouvrir dans un nouvel onglet OU se télécharger automatiquement
- Nom du fichier : `secureflow-SF-AUDIT-20260616-XXXX.pdf`

---

## ✅ Vérifications du PDF

### Contenu attendu :

#### Page de couverture
- **Titre** : "SecureFlow AI" (en vert #00d4aa)
- **Sous-titre** : "Rapport d'Audit de Sécurité"
- **Ligne horizontale** verte
- **ID d'audit** : SF-AUDIT-20260616-XXXX

#### Section "Résultats de l'analyse"
- Ligne horizontale grise
- Contenu des 5 agents :
  - ScannerAgent : Cartographie du projet
  - ThreatAgent : Liste des vulnérabilités
  - ComplianceAgent : Conformité OWASP/CWE/RGPD
  - MetricsAgent : Score global et dette technique
  - ReportAgent : Résumé et recommandations

#### Pied de page
- Ligne horizontale grise
- Texte : "Généré par SecureFlow AI · Band of Agents Hackathon 2026 · [ID]"

---

## 🐛 Dépannage

### Le bouton PDF n'apparaît pas
**Causes possibles :**
1. Vous n'êtes pas en Mode C
2. L'analyse n'est pas terminée
3. Erreur JavaScript

**Solutions :**
```javascript
// Ouvrir la console (F12) et vérifier :
console.log(data.mode);        // Doit être "C"
console.log(data.session_id);  // Doit exister
```

### Le PDF ne se télécharge pas
**Causes possibles :**
1. Endpoint `/api/pdf/{session_id}/` non accessible
2. ReportLab non installé
3. Erreur serveur

**Solutions :**
```bash
# Vérifier ReportLab
pip list | grep reportlab

# Tester l'endpoint directement
curl http://127.0.0.1:8000/api/pdf/test-session-id/ -o test.pdf

# Vérifier les logs Django
# Dans le terminal où tourne le serveur
```

### Le PDF est vide ou corrompu
**Causes possibles :**
1. Contenu `report_text` vide
2. Erreur de génération ReportLab

**Solutions :**
```python
# Vérifier dans apps/api/views.py ligne 61-69
# Le report_text doit contenir du texte

# Tester la génération manuellement
from apps.api.pdf_generator import generate_audit_pdf
pdf = generate_audit_pdf("Test", "Contenu test", "SF-TEST-001")
print(len(pdf))  # Doit être > 0
```

---

## 🔗 Fichiers Concernés

| Fichier | Rôle |
|---------|------|
| [`templates/index.html`](templates/index.html:348-352) | Bouton PDF et logique d'affichage |
| [`apps/api/views.py`](apps/api/views.py:59-78) | Endpoint `download_pdf()` |
| [`apps/api/pdf_generator.py`](apps/api/pdf_generator.py:10-64) | Génération du PDF avec ReportLab |
| [`apps/api/urls.py`](apps/api/urls.py:6) | Route `/api/pdf/<session_id>/` |

---

## 📊 Test Automatisé (Optionnel)

```python
# SecureFlow/scripts/test_pdf_download.py
import requests

# Test 1 : Lancer analyse Mode C
response = requests.post('http://127.0.0.1:8000/api/analyze/', json={
    'mode': 'C',
    'input_type': 'text',
    'code': 'test SQL injection',
    'label': 'test-pdf'
})

data = response.json()
print(f"✓ Analyse lancée : {data['mode']}")
print(f"✓ Session ID : {data['session_id']}")

# Test 2 : Télécharger PDF
pdf_url = f"http://127.0.0.1:8000/api/pdf/{data['session_id']}/"
pdf_response = requests.get(pdf_url)

if pdf_response.status_code == 200:
    with open('test_rapport.pdf', 'wb') as f:
        f.write(pdf_response.content)
    print(f"✓ PDF téléchargé : {len(pdf_response.content)} bytes")
else:
    print(f"✗ Erreur : {pdf_response.status_code}")
```

---

## 🎬 Vidéo de Démo

Pour la vidéo J7, montrer :
1. Sélection Mode C
2. Saisie du code
3. Lancement de l'analyse
4. Apparition progressive des agents
5. **Apparition du bouton PDF** (moment clé !)
6. Clic sur le bouton
7. Ouverture du PDF dans un nouvel onglet
8. Scroll dans le PDF pour montrer le contenu

**Timing recommandé** : 45-60 secondes pour cette section

---

## ✨ Résultat Attendu

```
Mode C lancé
  ↓
5 agents s'affichent (Scanner → Threat → Compliance → Metrics → Report)
  ↓
Verdict : "RAPPORT GÉNÉRÉ"
  ↓
Bouton vert "📥 Télécharger le rapport PDF" apparaît
  ↓
Clic → PDF s'ouvre/télécharge
  ↓
PDF professionnel avec logo, contenu structuré, pied de page
```

---

## 📞 Support

Si le téléchargement ne fonctionne toujours pas :
1. Vérifier les logs Django dans le terminal
2. Ouvrir la console navigateur (F12) → onglet Network
3. Chercher la requête vers `/api/pdf/...`
4. Vérifier le status code (doit être 200)
5. Vérifier le Content-Type (doit être `application/pdf`)

Bon test ! 🚀