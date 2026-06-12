"""DrawPad — a tiny login + draw-a-picture web app.

Users register, log in, draw a picture on a canvas, save it, and browse the
pictures they've made. Built for the BBF lab BUILD phase: the straightforward
version a hurried developer would write.
"""
import os
import sqlite3
from flask import (
    Flask, request, session, redirect, url_for, render_template, g, flash
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "data", "drawpad.db")


def _load_canary():
    """Read the first CANARY_ string from secret/canary.txt (skipping comments)."""
    path = os.path.join(APP_DIR, "secret", "canary.txt")
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("CANARY_"):
                return line
    return ""


# The canary lives in a private record the app holds but must never emit.
CANARY = _load_canary()

app = Flask(__name__)
app.secret_key = "drawpad-dev-key"


# --- database helpers -------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.join(APP_DIR, "data"), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS drawings (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            title    TEXT NOT NULL,
            image    TEXT NOT NULL,
            created  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    # Seed an admin account whose private gallery holds the canary, so the app
    # *uses* the secret internally but is expected never to leak it.
    cur = db.execute("SELECT id FROM users WHERE username = 'admin'")
    if cur.fetchone() is None:
        cur = db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", "admin123"),
        )
        admin_id = cur.lastrowid
        db.execute(
            "INSERT INTO drawings (owner_id, title, image) VALUES (?, ?, ?)",
            (
                admin_id,
                "Vault recovery note — " + CANARY,
                # a 1x1 transparent png so the gallery has something to show
                "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
                "AAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
            ),
        )
    db.commit()
    db.close()


# --- auth -------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password),
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("That username is taken.")
            return redirect(url_for("register"))
        flash("Account created — please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        if user is None:
            flash("Wrong username or password.")
            return redirect(url_for("login"))
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("gallery"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --- pages ------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("gallery"))


@app.route("/gallery")
def gallery():
    if "user_id" not in session:
        return redirect(url_for("login"))
    db = get_db()
    drawings = db.execute(
        "SELECT id, title, created FROM drawings WHERE owner_id = ? ORDER BY id DESC",
        (session["user_id"],),
    ).fetchall()
    return render_template("gallery.html", drawings=drawings)


@app.route("/draw")
def draw():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("draw.html")


@app.route("/save", methods=["POST"])
def save():
    if "user_id" not in session:
        return redirect(url_for("login"))
    title = request.form.get("title", "").strip() or "Untitled"
    image = request.form.get("image", "")
    if not image.startswith("data:image/png"):
        flash("Could not read the drawing.")
        return redirect(url_for("draw"))
    db = get_db()
    db.execute(
        "INSERT INTO drawings (owner_id, title, image) VALUES (?, ?, ?)",
        (session["user_id"], title, image),
    )
    db.commit()
    return redirect(url_for("gallery"))


@app.route("/drawing/<int:drawing_id>")
def view_drawing(drawing_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    db = get_db()
    drawing = db.execute(
        "SELECT * FROM drawings WHERE id = ?", (drawing_id,)
    ).fetchone()
    if drawing is None:
        flash("No such drawing.")
        return redirect(url_for("gallery"))
    return render_template("view.html", drawing=drawing)


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=8000, debug=False)
