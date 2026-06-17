# ✅ SOLUTION : Variables d'environnement manquantes

## 🔴 Problème identifié

```
RuntimeError: Configuration incomplète pour SecureFlow :
- BAND_SCANNER_AGENT_ID manquant (ScannerAgent)
- BAND_SCANNER_API_KEY manquant (ScannerAgent)
- BAND_THREAT_AGENT_ID manquant (ThreatAgent)
- BAND_THREAT_API_KEY manquant (ThreatAgent)
- BAND_COMPLIANCE_AGENT_ID manquant (ComplianceAgent)
- BAND_COMPLIANCE_API_KEY manquant (ComplianceAgent)
- BAND_RISK_AGENT_ID manquant (RiskAgent)
- BAND_RISK_API_KEY manquant (RiskAgent)
- BAND_DECISION_AGENT_ID manquant (DecisionAgent)
- BAND_DECISION_API_KEY manquant (DecisionAgent)
- GROQ_API_KEY manquante (LLM_PROVIDER=groq)
```

**Cause :** Le fichier `.env` existe mais Django ne le charge pas automatiquement.

## ✅ Solution 1 : Installer python-dotenv (RECOMMANDÉ)

```powershell
pip install python-dotenv
```

Puis modifiez `secureflow/settings.py` :

```python
# Au tout début du fichier, après les imports
from pathlib import Path
from dotenv import load_dotenv
import os

# Charger le fichier .env
load_dotenv()

# Le reste du fichier settings.py...
```

Puis redémarrez le serveur :
```powershell
python manage.py runserver
```

## ✅ Solution 2 : Charger manuellement dans manage.py

Modifiez `manage.py` :

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from dotenv import load_dotenv

def main():
    """Run administrative tasks."""
    # Charger les variables d'environnement
    load_dotenv()
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secureflow.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
```

## ✅ Solution 3 : Charger manuellement avant de lancer (TEMPORAIRE)

```powershell
# Charger les variables dans la session PowerShell
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2]
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

# Puis lancer le serveur
python manage.py runserver
```

## ✅ Solution 4 : Vérifier que .env est au bon endroit

```powershell
# Le fichier .env doit être à la racine du projet
Test-Path .env

# Afficher le contenu (sans les valeurs sensibles)
Get-Content .env | Select-String "BAND_|GROQ_" | ForEach-Object { $_.Line.Split('=')[0] }
```

Vous devriez voir :
```
BAND_SCANNER_AGENT_ID
BAND_SCANNER_API_KEY
BAND_THREAT_AGENT_ID
BAND_THREAT_API_KEY
BAND_COMPLIANCE_AGENT_ID
BAND_COMPLIANCE_API_KEY
BAND_RISK_AGENT_ID
BAND_RISK_API_KEY
BAND_DECISION_AGENT_ID
BAND_DECISION_API_KEY
GROQ_API_KEY
```

## 🎯 Étapes à suivre MAINTENANT

### Étape 1 : Installer python-dotenv
```powershell
pip install python-dotenv
```

### Étape 2 : Vérifier requirements.txt
```powershell
# Ajouter python-dotenv si absent
echo "python-dotenv>=1.0.0" >> requirements.txt
```

### Étape 3 : Modifier manage.py
Ajoutez ces lignes au début de `manage.py` :
```python
from dotenv import load_dotenv
load_dotenv()
```

### Étape 4 : Redémarrer le serveur
```powershell
python manage.py runserver
```

### Étape 5 : Tester
Ouvrez http://127.0.0.1:8000/ et testez une analyse.

## 🔍 Vérification

Pour vérifier que les variables sont chargées :

```powershell
python manage.py shell
```

Puis dans le shell :
```python
import os
print("GROQ_API_KEY:", os.getenv("GROQ_API_KEY")[:10] + "..." if os.getenv("GROQ_API_KEY") else "MANQUANT")
print("BAND_SCANNER_AGENT_ID:", os.getenv("BAND_SCANNER_AGENT_ID")[:10] + "..." if os.getenv("BAND_SCANNER_AGENT_ID") else "MANQUANT")
exit()
```

Si vous voyez "MANQUANT", les variables ne sont pas chargées.
Si vous voyez des valeurs tronquées, c'est bon !

## 📝 Note importante

Le fichier `.env` doit contenir toutes ces variables avec leurs vraies valeurs.
Si vous n'avez pas les valeurs, contactez Personne 1 ou Personne 2 qui ont configuré les agents Band.

## ✅ Après la correction

Une fois les variables chargées, l'interface devrait fonctionner :
1. Band Room s'affiche
2. Messages des agents apparaissent
3. Verdict final
4. Bouton PDF

Bonne chance ! 🚀