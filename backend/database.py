import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "guinness.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS pubs (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            address     TEXT,
            lat         REAL,
            lng         REAL,
            place_id    TEXT UNIQUE
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            pub_id      TEXT NOT NULL,
            author      TEXT,
            text        TEXT,
            rating      INTEGER,
            FOREIGN KEY (pub_id) REFERENCES pubs(id)
        );

        CREATE TABLE IF NOT EXISTS scores (
            pub_id          TEXT PRIMARY KEY,
            guinness_score  REAL,
            summary         TEXT,
            scored_at       TEXT,
            FOREIGN KEY (pub_id) REFERENCES pubs(id)
        );
    """)
    conn.commit()
    conn.close()
