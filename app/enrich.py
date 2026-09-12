"""Enrichissement des items en arrière-plan : OCR, vision (option), oEmbed, embeddings.

Principes (cahier des charges v0) :
- la capture ne doit jamais échouer parce qu'un service annexe est down ;
- les traitements lourds tournent dans une file, jamais dans le chemin de capture.
"""
import hashlib
import logging
import queue
import sqlite3
import threading
from pathlib import Path
from typing import Optional

import numpy as np
import requests

from . import config, db

log = logging.getLogger("enrich")

_queue: "queue.Queue[int]" = queue.Queue()
_worker: Optional[threading.Thread] = None


# --- Ollama -----------------------------------------------------------------

def ollama_alive() -> bool:
    try:
        return requests.get(f"{config.OLLAMA_URL}/api/tags", timeout=3).ok
    except Exception:
        return False


def embed(text: str) -> Optional[bytes]:
    """Vecteur nomic-embed-text en BLOB numpy float32, ou None si Ollama absent."""
    text = (text or "").strip()
    if not text:
        return None
    try:
        r = requests.post(
            f"{config.OLLAMA_URL}/api/embeddings",
            json={"model": config.EMBED_MODEL, "prompt": text[:4000]},
            timeout=30,
        )
        r.raise_for_status()
        vec = np.asarray(r.json()["embedding"], dtype=np.float32)
        return vec.tobytes()
    except Exception:
        log.warning("embedding indisponible (Ollama down ?) — item ingéré sans vecteur")
        return None


# --- OCR / vision -----------------------------------------------------------

def ocr_image(path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image

        return pytesseract.image_to_string(Image.open(path), lang=config.OCR_LANG).strip()
    except Exception:
        log.info("OCR indisponible pour %s", path.name)
        return ""


def describe_image(path: Path) -> str:
    if not config.VISION_MODEL:
        return ""
    try:
        import base64

        b64 = base64.b64encode(path.read_bytes()).decode()
        r = requests.post(
            f"{config.OLLAMA_URL}/api/generate",
            json={
                "model": config.VISION_MODEL,
                "prompt": "Décris cette image en une phrase concise.",
                "images": [b64],
                "stream": False,
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json().get("response", "").strip()
    except Exception:
        log.warning("vision indisponible pour %s", path.name)
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


# --- Similarité -------------------------------------------------------------

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def similarity(item_emb: bytes, project_emb: bytes) -> Optional[float]:
    if not item_emb or not project_emb:
        return None
    return _cosine(np.frombuffer(item_emb, dtype=np.float32),
                   np.frombuffer(project_emb, dtype=np.float32))


def recompute_project_embedding(conn: sqlite3.Connection, project_id: int) -> None:
    """Moyenne des items liés ; sinon title + description (cahier des charges v0)."""
    rows = conn.execute(
        "SELECT embedding FROM items WHERE linked_project_id = ? AND embedding IS NOT NULL",
        (project_id,),
    ).fetchall()
    if rows:
        vecs = [np.frombuffer(r["embedding"], dtype=np.float32) for r in rows]
        vec = np.mean(vecs, axis=0).astype(np.float32)
    else:
        p = db.project(conn, project_id)
        vec = _embed_sync(f"{p['title']} {p['description']}") if p else None
    conn.execute(
        "UPDATE projects SET embedding = ? WHERE id = ?",
        (vec.tobytes() if vec is not None else None, project_id),
    )


def _embed_sync(text: str) -> Optional[np.ndarray]:
    blob = embed(text)
    return np.frombuffer(blob, dtype=np.float32) if blob else None


# --- Worker -----------------------------------------------------------------

def _enrich_item(item_id: int) -> None:
    with db.db() as conn:
        item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if item is None or item["ingest_done"]:
        return

    ocr_text = item["ocr_text"]
    title = item["title"]
    vision_desc = None

    if item["type"] in ("photo", "screenshot") and item["source_path"]:
        path = Path(item["source_path"])
        if path.exists():
            if not ocr_text:
                ocr_text = ocr_image(path)
            if len(ocr_text) < config.OCR_MIN_CHARS:
                vision_desc = describe_image(path) or None

    if item["type"] == "bookmark" and item["url"] and not title:
        title = fetch_title(item["url"]) or None

    text_for_embedding = " ".join(
        t for t in (ocr_text, vision_desc, item["url"], title) if t
    )
    emb = embed(text_for_embedding)

    with db.db() as conn:
        conn.execute(
            "UPDATE items SET ocr_text = ?, title = ?, vision_description = ?, "
            "embedding = ?, ingest_done = 1 WHERE id = ?",
            (ocr_text, title, vision_desc, emb, item_id),
        )


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
