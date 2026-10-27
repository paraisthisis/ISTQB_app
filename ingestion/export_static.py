#!/usr/bin/env python3
"""
ingestion/export_static.py
Exports data/istqb.db to frontend/data/db.json so the frontend can run on
static hosting (GitHub Pages) without the Flask backend.

The JSON mirrors what the Flask API returns:
  chapters      full rows (id, number, title, content)
  glossary      rows (id, term, definition, chapter_id)
  questions     rows + nested options (id, label, text, is_correct), ordered like /api/questions
  theory_cards  rows ordered like /api/theory-cards

Usage:
  python3 ingestion/build_db.py
  python3 ingestion/export_static.py
"""

import json
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "data", "istqb.db")
OUT_PATH = os.path.join(BASE_DIR, "frontend", "data", "db.json")


def rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def main() -> None:
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run: python3 ingestion/build_db.py")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    chapters = rows(conn, "SELECT * FROM chapters ORDER BY id")
    glossary = rows(conn, "SELECT id, term, definition, chapter_id FROM glossary ORDER BY id")
    questions = rows(conn, "SELECT * FROM questions ORDER BY id")
    for q in questions:
        q["options"] = rows(
            conn,
            "SELECT id, label, text, is_correct FROM options WHERE question_id = ? ORDER BY label",
            (q["id"],),
        )
    theory_cards = rows(conn, "SELECT * FROM theory_cards ORDER BY chapter_id, id")
    math_types = rows(conn, "SELECT * FROM math_types ORDER BY chapter_id, id")
    conn.close()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "chapters": chapters,
                "glossary": glossary,
                "questions": questions,
                "theory_cards": theory_cards,
                "math_types": math_types,
            },
            f,
            ensure_ascii=False,
        )

    print(f"✓ Exported static data to {OUT_PATH}")
    print(f"  chapters: {len(chapters)}, glossary: {len(glossary)}, "
          f"questions: {len(questions)}, theory_cards: {len(theory_cards)}, math_types: {len(math_types)}")


if __name__ == "__main__":
    main()
