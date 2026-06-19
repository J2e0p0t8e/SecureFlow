import requests

s = requests.get("http://127.0.0.1:8000/api/session/2/").json()
print("status", s.get("status"), "room", s.get("room_id"))
r = requests.get(f"http://127.0.0.1:8000/api/room/{s['room_id']}/messages/")
print("messages status", r.status_code)
print(r.text[:1200])
