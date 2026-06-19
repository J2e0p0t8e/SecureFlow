import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")

import django

django.setup()

import requests

from apps.agents.band_registry import ALL_BAND_AGENT_NAMES, get_band_client_for
from apps.api.models import AnalysisSession

session = AnalysisSession.objects.order_by("-id").first()
print("session", session.id, session.status, session.room_id)

room_id = session.room_id
for name in ["ScannerAgent", "ThreatAgent", "DecisionAgent", "DevAgent"]:
    try:
        client = get_band_client_for(name)
        raw = client.get_context(room_id)
        print(name, "count", len(raw))
        if raw:
            print(" sample keys", raw[0].keys())
            print(" sample", str(raw[0])[:300])
    except Exception as e:
        print(name, "ERR", e)

# Try list messages endpoint if exists
c = get_band_client_for("ScannerAgent")
url = c._url(f"/chats/{room_id}/messages")
try:
    r = requests.get(url, headers=c._headers, params={"page": 1, "page_size": 50}, timeout=30)
    print("GET messages", r.status_code, r.text[:500])
except Exception as e:
    print("GET messages ERR", e)
