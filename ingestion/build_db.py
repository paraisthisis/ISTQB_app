#!/usr/bin/env python3
"""
ingestion/build_db.py
Populates data/istqb.db from seed JSON files.

Schema:
  chapters     (id, number, title, content)
  glossary     (id, term, definition, chapter_id)
  questions    (id, chapter_id, stem, explanation, difficulty)
  options      (id, question_id, label, text, is_correct)
  theory_cards (id, chapter_id, lo_reference, k_level, front_text, back_text)
"""

import json
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_DIR = os.path.join(BASE_DIR, "seed")
DB_PATH  = os.path.join(BASE_DIR, "data", "istqb.db")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS chapters (
    id      INTEGER PRIMARY KEY,
    number  TEXT    NOT NULL,
    title   TEXT    NOT NULL,
    content TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS glossary (
    id         INTEGER PRIMARY KEY,
    term       TEXT    NOT NULL,
    definition TEXT    NOT NULL,
    chapter_id INTEGER REFERENCES chapters(id)
);

CREATE TABLE IF NOT EXISTS questions (
    id          INTEGER PRIMARY KEY,
    chapter_id  INTEGER REFERENCES chapters(id),
    stem        TEXT    NOT NULL,
    explanation TEXT    NOT NULL DEFAULT '',
    difficulty  TEXT    NOT NULL DEFAULT 'K2'
);

CREATE TABLE IF NOT EXISTS options (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL REFERENCES questions(id),
    label       TEXT    NOT NULL,
    text        TEXT    NOT NULL,
    is_correct  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS theory_cards (
    id           INTEGER PRIMARY KEY,
    chapter_id   INTEGER REFERENCES chapters(id),
    lo_reference TEXT    NOT NULL DEFAULT '',
    k_level      TEXT    NOT NULL DEFAULT 'K2',
    front_text   TEXT    NOT NULL,
    back_text    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS math_types (
    id          INTEGER PRIMARY KEY,
    chapter_id  INTEGER REFERENCES chapters(id),
    title       TEXT    NOT NULL,
    simple_rule TEXT    NOT NULL,
    formula     TEXT    NOT NULL,
    example     TEXT    NOT NULL,
    tip         TEXT    NOT NULL DEFAULT ''
);
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_json(filename: str) -> list:
    path = os.path.join(SEED_DIR, filename)
    if not os.path.exists(path):
        print(f"  ✗ Seed file not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def drop_tables(conn: sqlite3.Connection) -> None:
    tables = ["options", "math_types", "theory_cards", "questions", "glossary", "chapters"]
    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()


# ---------------------------------------------------------------------------
# Population functions
# ---------------------------------------------------------------------------
def populate_chapters(conn: sqlite3.Connection, data: list) -> None:
    rows = [(c["id"], c["number"], c["title"], c.get("content", "")) for c in data]
    conn.executemany(
        "INSERT INTO chapters (id, number, title, content) VALUES (?,?,?,?)", rows
    )
    conn.commit()
    print(f"  ✓ Inserted {len(rows)} chapters")


def populate_glossary(conn: sqlite3.Connection, data: list) -> None:
    rows = [(g["id"], g["term"], g["definition"], g.get("chapter_id")) for g in data]
    conn.executemany(
        "INSERT INTO glossary (id, term, definition, chapter_id) VALUES (?,?,?,?)", rows
    )
    conn.commit()
    print(f"  ✓ Inserted {len(rows)} glossary entries")


def populate_questions(conn: sqlite3.Connection, data: list) -> None:
    q_rows = [
        (q["id"], q["chapter_id"], q["stem"], q.get("explanation", ""), q.get("difficulty", "K2"))
        for q in data
    ]
    conn.executemany(
        "INSERT INTO questions (id, chapter_id, stem, explanation, difficulty) VALUES (?,?,?,?,?)",
        q_rows,
    )

    opt_rows = []
    for q in data:
        for opt in q["options"]:
            opt_rows.append((
                q["id"],
                opt["label"],
                opt["text"],
                1 if opt["is_correct"] else 0,
            ))
    conn.executemany(
        "INSERT INTO options (question_id, label, text, is_correct) VALUES (?,?,?,?)",
        opt_rows,
    )
    conn.commit()
    print(f"  ✓ Inserted {len(q_rows)} questions with {len(opt_rows)} options")


def populate_theory_cards(conn: sqlite3.Connection, data: list) -> None:
    rows = [
        (
            c["id"],
            c["chapter_id"],
            c.get("lo_reference", ""),
            c.get("k_level", "K2"),
            c["front_text"],
            c["back_text"],
        )
        for c in data
    ]
    conn.executemany(
        "INSERT INTO theory_cards (id, chapter_id, lo_reference, k_level, front_text, back_text)"
        " VALUES (?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    print(f"  ✓ Inserted {len(rows)} theory cards")


def populate_math_types(conn: sqlite3.Connection, data: list) -> None:
    rows = [
        (
            m["id"],
            m["chapter_id"],
            m["title"],
            m["simple_rule"],
            m["formula"],
            m["example"],
            m.get("tip", ""),
        )
        for m in data
    ]
    conn.executemany(
        "INSERT INTO math_types (id, chapter_id, title, simple_rule, formula, example, tip)"
        " VALUES (?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()
    print(f"  ✓ Inserted {len(rows)} math types")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    print(f"Building database: {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)

    print("Dropping existing tables...")
    drop_tables(conn)

    print("Creating schema...")
    conn.executescript(SCHEMA)
    print("  ✓ Schema created\n")

    print("Loading seed data...")
    chapters     = load_json("chapters.json")
    glossary     = load_json("glossary.json")
    questions    = load_json("questions.json")
    theory_cards = load_json("theory_cards.json")
    math_types   = load_json("math_types.json")

    print("\nPopulating database...")
    populate_chapters(conn, chapters)
    populate_glossary(conn, glossary)
    populate_questions(conn, questions)
    populate_theory_cards(conn, theory_cards)
    populate_math_types(conn, math_types)

    # Verify
    print("\nVerification:")
    for table in ["chapters", "glossary", "questions", "options", "theory_cards", "math_types"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} rows")

    conn.close()
    print("\n✓ Database built successfully!")


if __name__ == "__main__":
    main()
