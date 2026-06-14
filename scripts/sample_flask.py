# mini_app/app.py — sample volontairement vulnérable pour tester Mode A
from flask import Flask, request
import sqlite3

app = Flask(__name__)
SECRET_KEY = "hardcoded-secret-key-12345"
DB_PATH = "users.db"

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return str(conn.execute(query).fetchone())

@app.route("/search")
def search():
    q = request.args.get("q", "")
    return f"<h1>Résultats pour : {q}</h1>"
