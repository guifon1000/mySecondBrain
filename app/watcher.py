"""Watcher local : surveille les dossiers de captures du PC (Screenshots,
Pictures...), copie chaque nouvelle image vers l'archive interne, déduplique
par hash, puis met en file d'enrichissement.

La copie (pas un simple renvoi vers le dossier source) est une exigence du
cahier des charges : si l'utilisateur supprime une capture, l'archive doit
survivre.
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
# parfois quand le fichier fait encore 0 octet (idem si un outil de capture
# écrit lentement) : on attend la stabilité.
_STABLE_CHECKS = 3   # tours consécutifs à taille inchangée pour considérer stable
_STABLE_DELAY = 1    # secondes
_MAX_WAIT = 30       # garde-fou : abandon après 30 s d'instabilité


def _classify(path: Path) -> str:
    parent = path.parent.name.lower()
    return (
        "screenshot"
        if any(k in parent for k in ("screenshot", "capture", "écran", "ecran"))
        else "photo"
    )


def _wait_stable(path: Path) -> bool:
    """Attend que la taille du fichier cesse de bouger (écriture en cours ?).

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
        # Copie vers l'archive — hors du dossier source, survit aux suppressions
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
    watched = [d for d in config.WATCH_DIRS if d.is_dir()]
    for d in watched:
        observer.schedule(Handler(), str(d), recursive=True)
        log.info("surveillance de %s", d)
    observer.daemon = True
    observer.start()
    # Rattrapage : fichiers déjà présents (premier lancement, crash, etc.)
    import threading

    threading.Thread(target=_catch_up, daemon=True).start()


def _catch_up() -> None:
    for watched_dir in config.WATCH_DIRS:
        if not watched_dir.is_dir():
            continue
        for path in sorted(watched_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
                continue
            digest = enrich.sha256_file(path)
            with db.db() as conn:
                if conn.execute("SELECT 1 FROM items WHERE sha256 = ?", (digest,)).fetchone():
                    continue
            ingest_file(path)