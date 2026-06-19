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
print("room", room_id)

c = get_band_client_for("ScannerAgent")
for path in [
    f"/chats/{room_id}/messages",
    f"/chats/{room_id}/events",
    f"/chats/{room_id}/context",
]:
    url = c._url(path)
    r = requests.get(url, headers=c._headers, params={"page": 1, "page_size": 50}, timeout=30)
    print(path, r.status_code, len(r.text))
    if r.ok:
        data = r.json()
        print(" keys", list(data.keys())[:8])
        inner = data.get("data") or data
        if isinstance(inner, dict):
            for k, v in inner.items():
                if isinstance(v, list):
                    print(" ", k, "len", len(v))
                    if v:
                        print("  first", str(v[0])[:400])
