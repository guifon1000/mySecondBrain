"""Index de consultation de la bibliothèque (doctrine cahier v2).

Artefact DÉRIVÉ et JETABLE : détruire index.db ne perd rien, on reconstruit.
Outil de L'AGENT (pas fonctionnalité de l'app) : je l'interroge pour les
approfondissements et les couvées. Jamais exposé dans l'UI.

Couvre :
  - myVault/biblio/pdf/*.pdf        -> texte intégral, page par page
  - myVault/_sources/*.md           -> fiches de lecture
  - myVault/Idees/**/*.md           -> idées (atomiques, satellites)
  - myVault/Casquettes/*.md         -> stubs de casquettes
  - myVault/Projets/*.md            -> stubs de projets

Usage :
  python tools/index_corpus.py            # index complet
  python tools/index_corpus.py --force    # reconstruit depuis zéro
  python tools/querir.py "rupture de bloc"   # (voir querir.py)
"""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import sqlite3

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "myVault"
DB = ROOT / "data" / "corpus-index.db"


def db():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS docs (
            id   INTEGER PRIMARY KEY,
            kind TEXT NOT NULL,        -- pdf_page / fiche / idee / casquette / projet
            ref  TEXT NOT NULL,        -- chemin + localisation (ex. 'page 12')
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            mtime REAL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
            title, text, content=docs, content_rowid=id,
            tokenize='porter unicode61'
        );
        CREATE TRIGGER IF NOT EXISTS docs_ai AFTER INSERT ON docs BEGIN
            INSERT INTO docs_fts(rowid, title, text)
            VALUES (new.id, new.title, new.text);
        END;
        CREATE TRIGGER IF NOT EXISTS docs_ad AFTER DELETE ON docs BEGIN
            INSERT INTO docs_fts(docs_fts, rowid, title, text)
            VALUES ('delete', old.id, old.title, old.text);
        END;
        CREATE TRIGGER IF NOT EXISTS docs_au AFTER UPDATE ON docs BEGIN
            INSERT INTO docs_fts(docs_fts, rowid, title, text)
            VALUES ('delete', old.id, old.title, old.text);
            INSERT INTO docs_fts(rowid, title, text)
            VALUES (new.id, new.title, new.text);
        END;
        """
    )
    conn.commit()


def index_pdf(conn, path: Path) -> int:
    """Texte intégral, UNE LIGNE PAR PAGE (recherche précise + citation)."""
    from pypdf import PdfReader

    conn.row_factory = sqlite3.Row
    title = path.stem
    mtime = path.stat().st_mtime
    cached = conn.execute(
        "SELECT COUNT(*) c, MAX(mtime) m FROM docs WHERE kind='pdf_page' "
        "AND ref LIKE ?", (f"{path.name} | page%",),
    ).fetchone()
    if cached["c"] and cached["m"] and abs(cached["m"] - mtime) < 2:
        return 0
    conn.execute("DELETE FROM docs WHERE kind='pdf_page' AND ref LIKE ?",
                 (f"{path.name} | page%",))
    n = 0
    try:
        reader = PdfReader(str(path))
        for i, page in enumerate(reader.pages):
            try:
                text = (page.extract_text() or "").strip()
            except Exception:
                text = ""
            if not text:
                continue
            conn.execute(
                "INSERT INTO docs (kind, ref, title, text, mtime) VALUES (?,?,?,?,?)",
                ("pdf_page", f"{path.name} | page {i + 1}", title, text, mtime),
            )
            n += 1
    except Exception as e:
        print(f"  !! {path.name}: {e}")
    return n


def index_md(conn, path: Path, kind: str) -> int:
    conn.row_factory = sqlite3.Row
    text = path.read_text(encoding="utf-8", errors="replace")
    mtime = path.stat().st_mtime
    row = conn.execute("SELECT id, mtime FROM docs WHERE kind=? AND ref=?",
                       (kind, str(path.relative_to(VAULT)))).fetchone()
    if row and row["mtime"] and abs(row["mtime"] - mtime) < 2:
        return 0
    if row:
        conn.execute("DELETE FROM docs WHERE id = ?", (row["id"],))
    title = path.stem
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    body = re.sub(r"^---\n.*?\n---", "", text, count=1, flags=re.DOTALL) if m else text
    if m and (dm := re.search(r"description:\s*(.+)", m.group(1))):
        title = f"{path.stem} — {dm.group(1).strip()[:80]}"
    conn.execute("INSERT INTO docs (kind, ref, title, text, mtime) VALUES (?,?,?,?,?)",
                 (kind, str(path.relative_to(VAULT)), title, body.strip(), mtime))
    return 1


import re  # noqa: E402


def main(force: bool = False):
    t0 = time.time()
    if force and DB.exists():
        DB.unlink()
    DB.parent.mkdir(exist_ok=True)
    conn = db()
    init(conn)

    stats = {}
    # 1. PDF de la bibliothèque
    for pdf in sorted((VAULT / "biblio" / "pdf").glob("*.pdf")):
        n = index_pdf(conn, pdf)
        stats[f"pdf:{pdf.name[:40]}"] = n
    # 2. fiches, idées, casquettes, projets
    md_targets = (
        ("_sources/*.md", "fiche"),
        ("Idees/atomiques/*.md", "idee"),
        ("Idees/satellites/*.md", "idee"),
        ("Casquettes/*.md", "casquette"),
        ("Projets/*.md", "projet"),
    )
    for pattern, kind in md_targets:
        for md in sorted(VAULT.glob(pattern)):
            n = index_md(conn, md, kind)
            stats[f"{kind}:{md.name[:40]}"] = n
    conn.commit()

    total = conn.execute("SELECT COUNT(*) c, SUM(LENGTH(text)) l FROM docs").fetchone()
    print(f"index -> {DB.name}")
    print(f"  documents indexés : {total['c']} blocs, {total['l'] // 1000}k caractères")
    for k, v in stats.items():
        if v:
            print(f"  {k}: {v} pages/blocs (re)indexés")
    print(f"  durée : {time.time() - t0:.1f}s")
    conn.close()


if __name__ == "__main__":
    main(force="--force" in sys.argv)
