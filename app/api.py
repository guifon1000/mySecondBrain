"""API FastAPI : réception des bookmarks (HTTP Shortcuts) + fichiers archivés.

L'endpoint de réception n'insère qu'une ligne : tout le traitement lourd
(oEmbed, embedding) part dans la file d'enrichissement.
Auth par token, via header `X-Ingest-Token` ou champ `token` du body
(les deux sont acceptés pour s'accommoder d'HTTP Shortcuts).
"""
import hashlib
import logging

from fastapi import FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles

from . import config, db, enrich

log = logging.getLogger("api")

app = FastAPI(title="Second cerveau", docs_url=None, redoc_url=None)


@app.post("/ingest/bookmark")
def ingest_bookmark(body: dict, x_ingest_token: str = Header(default="")) -> dict:
    token = x_ingest_token or str(body.get("token") or "")
    if token != config.INGEST_TOKEN:
        raise HTTPException(status_code=401, detail="token invalide")

    url = (body.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL invalide")

    digest = hashlib.sha256(url.encode()).hexdigest()
    with db.db() as conn:
        if conn.execute("SELECT 1 FROM items WHERE sha256 = ?", (digest,)).fetchone():
            return {"status": "duplicate"}
        cur = conn.execute(
            "INSERT INTO items (type, url, sha256) VALUES ('bookmark', ?, ?)",
            (url, digest),
        )
        item_id = cur.lastrowid

    enrich.enqueue(item_id)
    log.info("bookmark ingéré : %s", url)
    return {"status": "ok", "item_id": item_id}


def mount_archives() -> None:
    """Sert les images archivées à l'UI (accès via Tailscale uniquement)."""
    config.ensure_dirs()
    app.mount(
        "/archives",
        StaticFiles(directory=str(config.ARCHIVE_DIR)),
        name="archives",
    )
