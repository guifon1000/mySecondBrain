"""API FastAPI : réception des bookmarks (HTTP Shortcuts) + fichiers archivés.

L'endpoint de réception n'insère qu'une ligne : tout le traitement lourd
(oEmbed, embedding) part dans la file d'enrichissement.
Auth : si `SB_INGEST_TOKEN` est défini dans .env, le header `X-Ingest-Token`
ou le champ `token` du body doit correspondre. Vide (défaut v0 locale) = pas
d'auth — l'endpoint n'est joignable qu'en local.
"""
import hashlib
import logging
import sqlite3

from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles

from . import config, db, enrich

log = logging.getLogger("api")

app = FastAPI(title="Second cerveau", docs_url=None, redoc_url=None)


def _insert_bookmark(conn: sqlite3.Connection, url: str) -> tuple[int, str]:
    digest = hashlib.sha256(url.encode()).hexdigest()
    if conn.execute("SELECT 1 FROM items WHERE sha256 = ?", (digest,)).fetchone():
        return 0, "duplicate"
    cur = conn.execute(
        "INSERT INTO items (type, url, sha256) VALUES ('bookmark', ?, ?)",
        (url, digest),
    )
    return cur.lastrowid, "ok"


def ingest_url(url: str) -> tuple[int, str]:
    """Capture d'un bookmark, partagé entre l'API HTTP et le champ URL de l'UI."""
    url = (url or "").strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL invalide")
    with db.db() as conn:
        item_id, status = _insert_bookmark(conn, url)
    if status == "ok":
        enrich.enqueue(item_id)
        log.info("bookmark ingéré : %s", url)
    return item_id, status


def ingest_text(text: str) -> tuple[int, str]:
    """Capture d'un texte/code collé depuis l'UI (type d'item 'note')."""
    text = (text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="texte vide")
    digest = hashlib.sha256(text.encode()).hexdigest()
    with db.db() as conn:
        if conn.execute("SELECT 1 FROM items WHERE sha256 = ?", (digest,)).fetchone():
            return 0, "duplicate"
        cur = conn.execute(
            "INSERT INTO items (type, ocr_text, sha256) VALUES ('note', ?, ?)",
            (text[:enrich.MAX_FILE_TEXT], digest),
        )
        item_id = cur.lastrowid
    enrich.enqueue(item_id)
    log.info("note ingérée (%d caractères)", len(text))
    return item_id, "ok"


@app.post("/ingest/bookmark")
def ingest_bookmark(body: dict, x_ingest_token: str = Header(default="")) -> dict:
    if config.INGEST_TOKEN:
        token = x_ingest_token or str(body.get("token") or "")
        if token != config.INGEST_TOKEN:
            raise HTTPException(status_code=401, detail="token invalide")
    item_id, status = ingest_url(str(body.get("url") or ""))
    return {"status": status, "item_id": item_id}


def mount_archives() -> None:
    """Sert les images archivées à l'UI (accès via Tailscale uniquement)."""
    config.ensure_dirs()
    app.mount(
        "/archives",
        StaticFiles(directory=str(config.ARCHIVE_DIR)),
        name="archives",
    )
