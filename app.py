"""Biblioteca Aurora: small CRUD application used by the Selenium assignment."""

from __future__ import annotations

import os
import sqlite3
from functools import wraps
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


ROOT = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", ROOT / "instance" / "biblioteca.db"))
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "solo-para-demostracion-cambiar-en-produccion"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

DEMO_USERNAME = os.environ.get("DEMO_USERNAME", "demo")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Selenium123")
FIELD_LIMITS = {"title": 120, "author": 80, "genre": 40}
YEAR_MIN = 1450
YEAR_MAX = 2100


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


@app.teardown_appcontext
def close_db(_error: BaseException | None = None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db(seed: bool = True) -> None:
    db = get_db()
    db.execute(
        """CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT NOT NULL DEFAULT '',
            year INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    db.commit()
    if seed and db.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO books (title, author, genre, year) VALUES (?, ?, ?, ?)",
            [
                ("Cien años de soledad", "Gabriel García Márquez", "Realismo mágico", 1967),
                ("La casa de los espíritus", "Isabel Allende", "Novela", 1982),
                ("Ficciones", "Jorge Luis Borges", "Cuento", 1944),
            ],
        )
        db.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if "username" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def validate_book(form) -> tuple[dict[str, str], list[str]]:
    values = {
        field: (form.get(field, "") or "").strip()
        for field in ("title", "author", "genre", "year")
    }
    errors: list[str] = []

    for field, label in (("title", "El título"), ("author", "El autor")):
        if not values[field]:
            errors.append(f"{label} es obligatorio.")
    for field, label in (("title", "título"), ("author", "autor"), ("genre", "género")):
        if len(values[field]) > FIELD_LIMITS[field]:
            errors.append(f"El {label} admite como máximo {FIELD_LIMITS[field]} caracteres.")

    try:
        year = int(values["year"])
        if not YEAR_MIN <= year <= YEAR_MAX:
            errors.append(f"El año debe estar entre {YEAR_MIN} y {YEAR_MAX}.")
    except (TypeError, ValueError):
        year = 0
        errors.append("Ingresa un año válido.")

    values["year"] = str(year)
    return values, errors


def duplicate_exists(title: str, author: str, except_id: int | None = None) -> bool:
    sql = "SELECT 1 FROM books WHERE lower(title) = lower(?) AND lower(author) = lower(?)"
    params: list[Any] = [title, author]
    if except_id is not None:
        sql += " AND id != ?"
        params.append(except_id)
    return get_db().execute(sql, params).fetchone() is not None


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = (request.form.get("username", "") or "").strip()
        password = request.form.get("password", "") or ""
        if not username or not password:
            flash("Completa el usuario y la contraseña.", "error")
        elif username == DEMO_USERNAME and password == DEMO_PASSWORD:
            session.clear()
            session["username"] = username
            flash("Sesión iniciada. Bienvenido a tu biblioteca.", "success")
            return redirect(url_for("index"))
        else:
            flash("Usuario o contraseña incorrectos.", "error")
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("login"))


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        values, errors = validate_book(request.form)
        if not errors and duplicate_exists(values["title"], values["author"]):
            errors.append("Ya existe un libro con ese título y autor.")
        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("index"))
        get_db().execute(
            "INSERT INTO books (title, author, genre, year) VALUES (?, ?, ?, ?)",
            (values["title"], values["author"], values["genre"], int(values["year"])),
        )
        get_db().commit()
        flash(f'“{values["title"]}” se agregó a la biblioteca.', "success")
        return redirect(url_for("index"))

    query = (request.args.get("q", "") or "").strip()
    books = get_db().execute(
        """SELECT id, title, author, genre, year FROM books
           WHERE ? = '' OR title LIKE ? OR author LIKE ? OR genre LIKE ?
           ORDER BY title COLLATE NOCASE, id""",
        (query, f"%{query}%", f"%{query}%", f"%{query}%"),
    ).fetchall()
    total = get_db().execute("SELECT COUNT(*) FROM books").fetchone()[0]
    return render_template("index.html", books=books, query=query, total=total)


@app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@login_required
def edit_book(book_id: int):
    db = get_db()
    book = db.execute(
        "SELECT id, title, author, genre, year FROM books WHERE id = ?", (book_id,)
    ).fetchone()
    if book is None:
        flash("El libro solicitado ya no existe.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        values, errors = validate_book(request.form)
        if not errors and duplicate_exists(values["title"], values["author"], book_id):
            errors.append("Ya existe otro libro con ese título y autor.")
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("edit.html", book={**values, "id": book_id})
        db.execute(
            "UPDATE books SET title = ?, author = ?, genre = ?, year = ? WHERE id = ?",
            (values["title"], values["author"], values["genre"], int(values["year"]), book_id),
        )
        db.commit()
        flash(f'“{values["title"]}” se actualizó correctamente.', "success")
        return redirect(url_for("index"))

    return render_template("edit.html", book=book)


@app.post("/books/<int:book_id>/delete")
@login_required
def delete_book(book_id: int):
    db = get_db()
    book = db.execute("SELECT title FROM books WHERE id = ?", (book_id,)).fetchone()
    if book is None:
        flash("El libro solicitado ya no existe.", "error")
    else:
        db.execute("DELETE FROM books WHERE id = ?", (book_id,))
        db.commit()
        flash(f'“{book["title"]}” se eliminó de la biblioteca.', "success")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    with app.app_context():
        init_db(seed=True)
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
        use_reloader=False,
    )
