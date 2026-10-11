#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""pdf_cherche — pêcher dans le vrac de E:/pdf_library.

Le tri du répertoire distant est ignoré : on indexe le TEXTE intégral
(page par page) de tous les PDF, et on cherche par mots via FTS5.

Usage :
    python tools/pdf_cherche.py index              # indexer (incrémental, skip les inchangés)
    python tools/pdf_cherche.py "vis sarking"      # tous les mots (ET)
    python tools/pdf_cherche.py -o "LBM|stabilité" # au moins un mot (OU)
    python tools/pdf_cherche.py "kigumi*"          # préfixe (trailing *)
    python tools/pdf_cherche.py stats              # état de l'index
    python tools/pdf_cherche.py scans              # les PDF sans couche texte

Options de recherche : --limit N (défaut 25), --pages N (extraits/fichier, défaut 3), --json
"""
import argparse
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pymupdf as fitz

LIBRARY = Path(os.environ.get("PDF_LIBRARY", "E:/pdf_library"))
DB = Path(__file__).resolve().parent.parent / "data" / "pdf-library-index.db"
MAX_CHARS_PER_PAGE = 20_000


def connect() -> sqlite3.Connection:
    DB.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            path TEXT UNIQUE,
            folder TEXT,
            name TEXT,
            size INTEGER,
            mtime REAL,
            n_pages INTEGER DEFAULT 0,
            has_text INTEGER DEFAULT 0,
            error TEXT,
            indexed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS pages (
            rowid INTEGER PRIMARY KEY,
            file_id INTEGER,
            page INTEGER,
            text TEXT
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
            text, content='pages', content_rowid='rowid',
            tokenize='unicode61 remove_diacritics 2'
        );
        CREATE TRIGGER IF NOT EXISTS pages_ai AFTER INSERT ON pages BEGIN
            INSERT INTO pages_fts(rowid, text) VALUES (new.rowid, new.text);
        END;
        CREATE TRIGGER IF NOT EXISTS pages_ad AFTER DELETE ON pages BEGIN
            INSERT INTO pages_fts(pages_fts, rowid, text) VALUES ('delete', old.rowid, old.text);
        END;
        CREATE INDEX IF NOT EXISTS pages_file ON pages(file_id);
    """)
    return conn


# ---------------------------------------------------------------- indexation

def delete_file(conn: sqlite3.Connection, file_id: int):
    conn.execute("DELETE FROM pages WHERE file_id = ?", (file_id,))
    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))


def index(incremental: bool = True):
    if not LIBRARY.is_dir():
        sys.exit(f"répertoire introuvable : {LIBRARY}")
    conn = connect()
    # rglob est insensible à la casse sous Windows : un seul motif suffit
    pdfs = sorted(LIBRARY.rglob("*.pdf"))
    seen = set()
    t0 = time.time()
    n_new = n_skip = n_scan = n_err = 0
    total = len(pdfs)
    for i, path in enumerate(pdfs, 1):
        posix = path.as_posix()
        seen.add(posix.lower())
        if path.name.startswith("._"):
            continue  # déchets macOS (AppleDouble), pas de vrais PDF
        try:
            st = path.stat()
        except OSError:
            continue
        row = conn.execute(
            "SELECT id, size, mtime, has_text FROM files WHERE path = ?", (posix,)
        ).fetchone()
        if incremental and row and row["size"] == st.st_size and abs(row["mtime"] - st.st_mtime) < 2:
            n_skip += 1
            continue
        if row:
            delete_file(conn, row["id"])
        try:
            doc = fitz.open(posix)
            n_pages = doc.page_count
            texts = []
            has_text = 0
            for pno in range(n_pages):
                t = (doc[pno].get_text() or "")[:MAX_CHARS_PER_PAGE]
                if t.strip():
                    has_text = 1
                texts.append(t)
            doc.close()
        except Exception as e:  # corrompu / chiffré
            conn.execute(
                "INSERT INTO files (path, folder, name, size, mtime, error, indexed_at) VALUES (?,?,?,?,?,?,?)",
                (posix, path.parent.name, path.name, st.st_size, st.st_mtime, str(e)[:200],
                 datetime.now().isoformat(timespec="seconds")),
            )
            n_err += 1
            continue
        cur = conn.execute(
            "INSERT INTO files (path, folder, name, size, mtime, n_pages, has_text, indexed_at) VALUES (?,?,?,?,?,?,?,?)",
            (posix, path.parent.name, path.name, st.st_size, st.st_mtime, n_pages, has_text,
             datetime.now().isoformat(timespec="seconds")),
        )
        fid = cur.lastrowid
        conn.executemany(
            "INSERT INTO pages (file_id, page, text) VALUES (?,?,?)",
            [(fid, p, t) for p, t in enumerate(texts, 1)],
        )
        if has_text:
            n_new += 1
        else:
            n_scan += 1
        conn.commit()
        dt = time.time() - t0
        eta = dt / i * (total - i)
        print(f"[{i}/{total}] {path.name} ({n_pages} p.) — reste ~{eta/60:.0f} min", end="\r")
    # purge des fichiers disparus
    # purge : fichiers disparus + déchets macOS déjà enregistrés
    gone = [r["id"] for r in conn.execute("SELECT id, path FROM files")
            if r["path"].lower() not in seen or Path(r["path"]).name.startswith("._")]
    for fid in gone:
        delete_file(conn, fid)
    conn.commit()
    mins = (time.time() - t0) / 60
    print(f"\nindexé : {n_new} nouveaux, {n_skip} inchangés (skip), "
          f"{n_scan} sans texte (scans), {n_err} erreurs, {len(gone)} purgés — {mins:.1f} min")


# ---------------------------------------------------------------- recherche

def parse_terms(mots: list[str]) -> list[str]:
    """['kigumi|sarking'] ou ['vis', 'sarking'] -> ['kigumi', 'sarking', ...]"""
    return [w for m in mots for w in m.split("|") if w]


def build_query(terms: list[str], mode: str) -> str:
    """mots -> requête FTS5 ; un mot finissant par * reste préfixe."""
    parts = []
    for t in terms:
        prefix = t.endswith("*")
        word = t.rstrip("*").replace('"', '""')
        parts.append(f'"{word}"*' if prefix else f'"{word}"')
    return " OR ".join(parts) if mode == "or" else " AND ".join(parts)


def search(terms: list[str], mode: str, limit: int, pages_per: int, as_json: bool):
    conn = connect()
    q = build_query(parse_terms(terms), mode)
    if not q:
        sys.exit("aucun terme de recherche")
    try:
        rows = conn.execute("""
            SELECT f.id, f.path, f.folder, f.name, f.n_pages,
                   COUNT(*) AS hits,
                   MIN(p.page) AS first_page
            FROM pages_fts
            JOIN pages p ON p.rowid = pages_fts.rowid
            JOIN files f ON f.id = p.file_id
            WHERE pages_fts MATCH ?
            GROUP BY f.id
            ORDER BY hits DESC, f.name
            LIMIT ?
        """, (q, limit)).fetchall()
    except sqlite3.OperationalError as e:
        sys.exit(f"requête invalide : {e}\n  (requête FTS5 : {q})")
    if not rows:
        print("aucun résultat")
        return
    out = []
    for r in rows:
        snips = conn.execute("""
            SELECT p.page, snippet(pages_fts, 0, '»', '«', ' … ', 14) AS snip
            FROM pages_fts
            JOIN pages p ON p.rowid = pages_fts.rowid
            WHERE pages_fts MATCH ? AND p.file_id = ?
            ORDER BY p.page LIMIT ?
        """, (q, r["id"], pages_per)).fetchall()
        item = {"path": r["path"], "hits": r["hits"], "pages": r["n_pages"],
                "extraits": [{"page": s["page"], "texte": s["snip"].replace("\n", " ")} for s in snips]}
        out.append(item)
        if not as_json:
            print(f"\n■ {r['path']}  [{r['hits']} pages touchées / {r['n_pages']} p.]")
            for s in snips:
                print(f"   p.{s['page']:>4} : {s['snip'].replace(chr(10), ' ').strip()}")
    if as_json:
        import json
        print(json.dumps(out, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- stats

def stats():
    conn = connect()
    (n,) = conn.execute("SELECT COUNT(*) FROM files").fetchone()
    (t,) = conn.execute("SELECT COUNT(*) FROM files WHERE has_text=1").fetchone()
    (s,) = conn.execute("SELECT COUNT(*) FROM files WHERE has_text=0 AND error IS NULL").fetchone()
    (e,) = conn.execute("SELECT COUNT(*) FROM files WHERE error IS NOT NULL").fetchone()
    (p,) = conn.execute("SELECT COUNT(*) FROM pages").fetchone()
    gb = sum(r[0] for r in conn.execute("SELECT size FROM files")) / 1e9
    print(f"{LIBRARY} — {n} PDF indexés ({gb:.1f} Go), {p} pages")
    print(f"  texte : {t}   |  scans sans texte : {s}  |  erreurs : {e}")


def scans():
    conn = connect()
    for r in conn.execute(
        "SELECT path, n_pages FROM files WHERE has_text=0 AND error IS NULL ORDER BY n_pages DESC"
    ):
        print(f"{r['path']}  ({r['n_pages']} p.)")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="chercher dans E:/pdf_library")
    ap.add_argument("mots", nargs="*", help="mots, ou 'index' / 'stats' / 'scans'")
    ap.add_argument("-o", dest="mode", action="store_const", const="or", default="and",
                    help="au moins un mot (OU) au lieu de tous (ET)")
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--pages", type=int, default=3, help="extraits par fichier")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--rebuild", action="store_true", help="index : tout réanalyser")
    a = ap.parse_args()
    if not a.mots:
        ap.print_help()
        return
    cmd = a.mots[0].lower()
    if cmd == "index":
        index(incremental=not a.rebuild)
    elif cmd == "stats":
        stats()
    elif cmd == "scans":
        scans()
    else:
        search(a.mots, a.mode, a.limit, a.pages, a.json)


if __name__ == "__main__":
    main()
