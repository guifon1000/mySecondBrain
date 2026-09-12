"""Watcher Syncthing : copie les nouveaux fichiers HORS de la zone synchronisée,
déduplique par hash, puis met en file d'enrichissement.

La copie (pas un simple renvoi vers le dossier watched) est une exigence du
cahier des charges : si le téléphone supprime une capture, l'archive serveur
doit survivre.
"""
import logging
import shutil
import time
from datetime import datetime
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import config, db, enrich

log = logging.getLogger("watcher")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif"}
# Syncthing écrit par morceaux et sur Windows l'événement "created" arrive
# parfois quand le fichier fait encore 0 octet : on attend la stabilité.
_STABLE_CHECKS = 3   # tours consécutifs à taille inchangée pour considérer stable
_STABLE_DELAY = 1    # secondes
_MAX_WAIT = 30       # garde-fou : abandon après 30 s d'instabilité


def _classify(ext: str) -> str:
    return "screenshot" if "screenshot" in ext.parent.name.lower() else "photo"


def _wait_stable(path: Path) -> bool:
    """Attend que la taille du fichier cesse de bouger (sync en cours ?).

    Ne renonce pas au premier changement de taille : un fichier fraîchement
    créé passe par 0 octet avant d'être rempli. La taille doit rester
    identique et non nulle pendant _STABLE_CHECKS tours.
    """
    last_size = -1
    stable_rounds = 0
    for _ in range(_MAX_WAIT // _STABLE_DELAY):
        try:
            size = path.stat().st_size
        except OSError:
            return False
        if size > 0 and size == last_size:
            stable_rounds += 1
            if stable_rounds >= _STABLE_CHECKS:
                return True
        else:
            stable_rounds = 0
        last_size = size
        time.sleep(_STABLE_DELAY)
    return False


def ingest_file(src: Path) -> None:
    if not _wait_stable(src):
        return
    digest = enrich.sha256_file(src)

    with db.db() as conn:
        dup = conn.execute("SELECT id FROM items WHERE sha256 = ?", (digest,)).fetchone()
        if dup:
            log.info("doublon ignoré : %s", src.name)
            return
        # Copie vers l'archive — hors zone Syncthing, survives les suppressions téléphone
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        dest = config.ARCHIVE_DIR / f"{stamp}{src.suffix.lower()}"
        shutil.copy2(src, dest)
        cur = conn.execute(
            "INSERT INTO items (type, source_path, sha256, embedding) VALUES (?, ?, ?, NULL)",
            (_classify(src), str(dest), digest),
        )
        item_id = cur.lastrowid

    enrich.enqueue(item_id)
    log.info("ingéré : %s -> %s", src.name, dest.name)


class Handler(FileSystemEventHandler):
    def on_created(self, event) -> None:
        path = Path(event.src_path)
        if path.suffix.lower() in IMAGE_EXTS:
            ingest_file(path)


def start_watcher() -> None:
    config.ensure_dirs()
    observer = Observer()
    observer.schedule(Handler(), str(config.WATCH_DIR), recursive=True)
    observer.daemon = True
    observer.start()
    # Rattrapage : fichiers déjà présents (première synchro, crash, etc.)
    import threading

    threading.Thread(target=_catch_up, daemon=True).start()
    log.info("surveillance de %s", config.WATCH_DIR)


def _catch_up() -> None:
    known = set()
    with db.db() as conn:
        for row in conn.execute("SELECT source_path FROM items"):
            known.add(row["source_path"])
    # On re-parse par hash via un chemin temporaire : plus simple de hasher les
    # fichiers du dossier watched directement.
    for path in sorted(config.WATCH_DIR.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue
        if str(path) in known:
            continue
        digest = enrich.sha256_file(path)
        with db.db() as conn:
            if conn.execute("SELECT 1 FROM items WHERE sha256 = ?", (digest,)).fetchone():
                continue
        ingest_file(path)
