import sqlite3
import string
import random
from flask import Flask, request, redirect, jsonify

app = Flask(__name__)
DB = "links.db"


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS links (code TEXT PRIMARY KEY, url TEXT NOT NULL)"
        )


def make_code(n=6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


@app.post("/shorten")
def shorten():
    url = (request.json or {}).get("url")
    if not url:
        return jsonify(error="url required"), 400
    code = make_code()
    with db() as conn:
        conn.execute("INSERT INTO links (code, url) VALUES (?, ?)", (code, url))
    return jsonify(code=code)


@app.get("/<code>")
def follow(code):
    with db() as conn:
        row = conn.execute("SELECT url FROM links WHERE code = ?", (code,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return redirect(row["url"])


if __name__ == "__main__":
    init()
    app.run(port=5000)
