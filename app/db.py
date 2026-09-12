"""SQLite unique : métadonnées ET vecteurs (BLOB). Pas de service séparé."""
import sqlite3
import threading
from contextlib import contextmanager
from typing import Iterator, Optional

from . import config

_local = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    embedding   BLOB,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS items (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    type               TEXT NOT NULL CHECK (type IN ('photo', 'screenshot', 'bookmark')),
    source_path        TEXT,
    url                TEXT,
    title              TEXT,
    ocr_text           TEXT NOT NULL DEFAULT '',
    vision_description TEXT,
    embedding          BLOB,
    sha256             TEXT UNIQUE,
    created_at         TEXT NOT NULL DEFAULT (datetime('now')),
    status             TEXT NOT NULL DEFAULT 'inbox'
                       CHECK (status IN ('inbox', 'archived', 'linked')),
    linked_project_id  INTEGER REFERENCES projects(id),
    ingest_done        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at       TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at         TEXT,
    items_reviewed   INTEGER NOT NULL DEFAULT 0,
    archived         INTEGER NOT NULL DEFAULT 0,
    linked           INTEGER NOT NULL DEFAULT 0,
    projects_created INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS suggestion_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id    INTEGER NOT NULL REFERENCES items(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    score      REAL,
    action     TEXT NOT NULL CHECK (action IN ('shown', 'accepted', 'rejected')),
    ts         TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_project ON items(linked_project_id);
CREATE INDEX IF NOT EXISTS idx_items_ingest ON items(ingest_done) WHERE ingest_done = 0;
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    """Connexion par thread (SQLite n'aime pas partager les connexions)."""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _connect()
        _local.conn = conn
    yield conn
    conn.commit()


def init_db() -> None:
    config.ensure_dirs()
    with db() as conn:
        conn.executescript(SCHEMA)


# --- Requêtes utilitaires ---------------------------------------------------

def project(conn: sqlite3.Connection, project_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()


def all_projects(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT p.*, COUNT(i.id) AS item_count,
                  (SELECT COUNT(*) FROM items i2
                   WHERE i2.linked_project_id = p.id
                     AND i2.created_at >= datetime('now', '-7 days')) AS items_this_week
           FROM projects p LEFT JOIN items i ON i.linked_project_id = p.id
           GROUP BY p.id ORDER BY p.created_at"""
    ).fetchall()


def inbox_items(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM items WHERE status = 'inbox' ORDER BY created_at LIMIT ?", (limit,)
    ).fetchall()


def inbox_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) c FROM items WHERE status = 'inbox'").fetchone()["c"]


def linked_items(conn: sqlite3.Connection, project_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM items WHERE linked_project_id = ? ORDER BY created_at DESC",
        (project_id,),
    ).fetchall()
