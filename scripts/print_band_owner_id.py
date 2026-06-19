"""Affiche BAND_OWNER_USER_ID (depuis .env ou GET /me via ScannerAgent)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")

import django

django.setup()

from django.conf import settings

from apps.agents.band_registry import get_band_client_for

configured = getattr(settings, "BAND_OWNER_USER_ID", "").strip()
if configured:
    print("BAND_OWNER_USER_ID (from .env):", configured)
    sys.exit(0)

client = get_band_client_for("ScannerAgent")
owner_id = client.resolve_owner_user_id()
if owner_id:
    print("Suggested BAND_OWNER_USER_ID:", owner_id)
    print("Add to .env: BAND_OWNER_USER_ID=" + owner_id)
else:
    print("Could not resolve owner user id.")
    print("Set BAND_OWNER_USER_ID manually (band.ai → Settings → Profile).")
    try:
        me = client.get_me()
        print("GET /me keys:", list((me.get("data") or me).keys())[:20])
    except Exception as exc:
        print("GET /me failed:", exc)
    sys.exit(1)
