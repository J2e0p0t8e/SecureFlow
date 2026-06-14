"""Configuration WSGI pour déploiement (Render, Railway)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")

application = get_wsgi_application()
