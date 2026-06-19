import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")

import django

django.setup()

import requests

from apps.agents.band_registry import get_band_client_for
from apps.api.models import AnalysisSession

session = AnalysisSession.objects.order_by("-id").first()
room_id = session.room_id
c = get_band_client_for("ScannerAgent")

r = requests.get(
    c._url(f"/chats/{room_id}/context"),
    headers=c._headers,
    params={"page": 1, "page_size": 100},
    timeout=30,
)
data = r.json()
print(json.dumps(data, indent=2)[:4000])

print("\n--- get_context parse ---")
msgs = c.get_context(room_id)
print("parsed count", len(msgs))
if msgs:
    print("first", msgs[0])
