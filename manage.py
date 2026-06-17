#!/usr/bin/env python
"""Point d'entrée Django pour SecureFlow AI."""
import os
import sys
from dotenv import load_dotenv


def main():
    # Charger les variables d'environnement depuis le fichier .env
    load_dotenv()
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django n'est pas installé. Lance : pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
