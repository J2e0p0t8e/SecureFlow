import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")
django.setup()
