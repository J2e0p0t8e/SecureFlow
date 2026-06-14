"""
Script manuel pour tester BaseAgent + Band + LLM.

Usage (après configuration du .env) :
    python manage.py shell < scripts/test_scanner_agent.py

Ou depuis la racine :
    python scripts/test_scanner_agent.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureflow.settings")

import django

django.setup()

from apps.agents.mode_a.scanner import ScannerAgent


def main() -> None:
    sample_project = """
    # mini_app/app.py
    from flask import Flask, request
    import sqlite3

    app = Flask(__name__)
    DB_PATH = "users.db"

    @app.route("/login", methods=["POST"])
    def login():
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        return str(conn.execute(query).fetchone())
    """

    agent = ScannerAgent()
    band = agent.band
    room = band.create_room()
    print(f"Room créée : {room.id}")

    band.seed_room(room.id, sample_project, label="Projet de test")

    result = agent.run(room.id, extra_input=sample_project)
    print(f"\n=== {result.agent_name} ===\n")
    print(result.content)


if __name__ == "__main__":
    main()
