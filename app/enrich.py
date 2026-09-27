"""Enrichissement des items en arrière-plan : OCR (optionnel), oEmbed, extraction
fichier. PAS d'appel IA : le sémantique est géré par l'agent Pi dédié au projet,
qui lit la base directement.

Principe (cahier des charges v0) : la capture ne doit jamais échouer ; les
traitements tournent dans une file, jamais dans le chemin de capture.
"""
import hashlib
import logging
import queue
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from . import config, db

log = logging.getLogger("enrich")

_queue: "queue.Queue[int]" = queue.Queue()
_worker: Optional[threading.Thread] = None


# --- OCR --------------------------------------------------------------------

def ocr_image(path: Path) -> str:
    """OCR local (Tesseract) — optionnel, indépendant de tout service IA."""
    try:
        import pytesseract
        from PIL import Image

        return pytesseract.image_to_string(Image.open(path), lang=config.OCR_LANG).strip()
    except Exception:
        log.info("OCR indisponible pour %s", path.name)
        return ""


# --- Bookmarks --------------------------------------------------------------

def fetch_title(url: str) -> str:
    """Titre via oEmbed quand disponible (YouTube oui, X non). Échec = URL brute."""
    try:
        r = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=10,
        )
        if r.ok:
            return r.json().get("title", "")
    except Exception:
        pass
    return ""


# --- Extraction de texte des fichiers --------------------------------------

MAX_FILE_TEXT = 8000  # caractères gardés pour l'embedding / l'affichage


def extract_file_text(path: Path) -> str:
    """Texte d'un fichier non-image (PDF via pypdf, autres = lecture directe)."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return "\n".join(
                (page.extract_text() or "") for page in reader.pages
            ).strip()[:MAX_FILE_TEXT]
        except Exception:
            log.info("texte PDF non extractible : %s", path.name)
            return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_TEXT]
    except OSError:
        return ""


# --- Worker -----------------------------------------------------------------

def _enrich_item(item_id: int) -> None:
    """Enrichissement local uniquement : oEmbed pour les bookmarks, extraction
    de texte pour les fichiers. Pas d'IA, pas de réseau (hors oEmbed)."""
    with db.db() as conn:
        item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if item is None or item["ingest_done"]:
        return

    ocr_text = item["ocr_text"]
    title = item["title"]

    if item["type"] in ("photo", "screenshot") and item["source_path"]:
        path = Path(item["source_path"])
        if path.exists() and not ocr_text:
            ocr_text = ocr_image(path)
    elif item["type"] == "file" and item["source_path"]:
        path = Path(item["source_path"])
        if path.exists():
            ocr_text = ocr_text or extract_file_text(path)
            title = title or path.name

    if item["type"] == "bookmark" and item["url"] and not title:
        title = fetch_title(item["url"]) or None

    with db.db() as conn:
        conn.execute(
            "UPDATE items SET ocr_text = ?, title = ?, ingest_done = 1 WHERE id = ?",
            (ocr_text, title, item_id),
        )
        # Note inbox dans le vault (si le vault existe)
        try:
            from . import vault

            item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
            vault.create_item_note(conn, item)
        except Exception:
            log.exception("note vault non créée pour l'item %s", item_id)


def _worker_loop() -> None:
    while True:
        item_id = _queue.get()
        try:
            _enrich_item(item_id)
        except Exception:
            log.exception("enrichissement échoué pour l'item %s", item_id)
        finally:
            _queue.task_done()


def start_worker() -> None:
    global _worker
    if _worker is None:
        _worker = threading.Thread(target=_worker_loop, name="enrich", daemon=True)
        _worker.start()


def enqueue(item_id: int) -> None:
    """Traite les items en attente restés à 0 (après crash) puis celui-ci."""
    start_worker()
    with db.db() as conn:
        pending = conn.execute(
            "SELECT id FROM items WHERE ingest_done = 0 AND id != ? ORDER BY id",
            (item_id,),
        ).fetchall()
    for row in pending:
        _queue.put(row["id"])
    _queue.put(item_id)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
