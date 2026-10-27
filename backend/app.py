#!/usr/bin/env python3
"""
backend/app.py
Flask API server for the ISTQB CTFL v4.0.1 Practice App.

Endpoints:
  GET /api/chapters
  GET /api/chapters/<id>
  GET /api/questions          ?chapter=<id>
  GET /api/theory-cards       ?chapter=<id>&k_level=<K1|K2|K3>
  GET /                       → serves frontend/index.html
  GET /<path>                 → serves static files from frontend/
"""

import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH      = os.path.join(BASE_DIR, "data", "istqb.db")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = Flask(__name__, static_folder=None)
CORS(app)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def rows_to_list(rows) -> list:
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
@app.route("/api/chapters", methods=["GET"])
def list_chapters():
    with get_db() as conn:
        chapters = rows_to_list(conn.execute(
            "SELECT id, number, title FROM chapters ORDER BY id"
        ).fetchall())
    return jsonify(chapters)


@app.route("/api/chapters/<int:chapter_id>", methods=["GET"])
def get_chapter(chapter_id: int):
    with get_db() as conn:
        chapter = conn.execute(
            "SELECT * FROM chapters WHERE id = ?", (chapter_id,)
        ).fetchone()
        if not chapter:
            abort(404, description="Chapter not found")

        glossary = rows_to_list(conn.execute(
            "SELECT id, term, definition FROM glossary WHERE chapter_id = ? ORDER BY term",
            (chapter_id,)
        ).fetchall())

        math_types = rows_to_list(conn.execute(
            "SELECT * FROM math_types WHERE chapter_id = ? ORDER BY id",
            (chapter_id,)
        ).fetchall())

    result = dict(chapter)
    result["glossary"] = glossary
    result["math_types"] = math_types
    return jsonify(result)


@app.route("/api/math-types", methods=["GET"])
def list_math_types():
    chapter_filter = request.args.get("chapter")
    with get_db() as conn:
        if chapter_filter:
            mts = rows_to_list(conn.execute(
                "SELECT * FROM math_types WHERE chapter_id = ? ORDER BY id",
                (chapter_filter,)
            ).fetchall())
        else:
            mts = rows_to_list(conn.execute(
                "SELECT * FROM math_types ORDER BY chapter_id, id"
            ).fetchall())
    return jsonify(mts)


@app.route("/api/questions", methods=["GET"])
def list_questions():
    chapter_filter = request.args.get("chapter")
    with get_db() as conn:
        if chapter_filter:
            qs = rows_to_list(conn.execute(
                "SELECT * FROM questions WHERE chapter_id = ? ORDER BY id",
                (chapter_filter,)
            ).fetchall())
        else:
            qs = rows_to_list(conn.execute(
                "SELECT * FROM questions ORDER BY id"
            ).fetchall())

        # Attach options to each question
        for q in qs:
            q["options"] = rows_to_list(conn.execute(
                "SELECT id, label, text, is_correct FROM options WHERE question_id = ? ORDER BY label",
                (q["id"],)
            ).fetchall())

    return jsonify(qs)


@app.route("/api/theory-cards", methods=["GET"])
def list_theory_cards():
    chapter_filter = request.args.get("chapter")
    k_level_filter = request.args.get("k_level")

    query = "SELECT * FROM theory_cards WHERE 1=1"
    params = []

    if chapter_filter:
        query += " AND chapter_id = ?"
        params.append(chapter_filter)
    if k_level_filter:
        query += " AND k_level = ?"
        params.append(k_level_filter.upper())

    query += " ORDER BY chapter_id, id"

    with get_db() as conn:
        cards = rows_to_list(conn.execute(query, params).fetchall())

    return jsonify(cards)


# ---------------------------------------------------------------------------
# Frontend serving
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>", methods=["GET"])
def serve_static(filename: str):
    # Security: only serve files inside frontend directory
    safe_path = os.path.realpath(os.path.join(FRONTEND_DIR, filename))
    if not safe_path.startswith(os.path.realpath(FRONTEND_DIR)):
        abort(403)
    if not os.path.exists(safe_path):
        abort(404)
    directory = os.path.dirname(safe_path)
    file_name  = os.path.basename(safe_path)
    return send_from_directory(directory, file_name)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": str(e)}), 404


@app.errorhandler(403)
def forbidden(e):
    return jsonify({"error": "Forbidden"}), 403


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run: python3 ingestion/build_db.py")
        raise SystemExit(1)
    port = int(os.environ.get("PORT", 5050))
    print(f"Starting ISTQB Practice App...")
    print(f"Database: {DB_PATH}")
    print(f"Frontend: {FRONTEND_DIR}")
    print(f"URL:      http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
