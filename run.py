"""Point d'entrée unique : API + watcher + worker d'enrichissement + UI.

Un seul process, conformément au cahier des charges v0 (moins de services,
moins de choses qui cassent).

Usage : .venv/Scripts/python run.py   (ou python run.py après activation)
"""
import logging

from app import config, db, enrich
from app.api import app, mount_archives
from app import watcher
from app import ui  # noqa: F401 — enregistre les pages NiceGUI
from nicegui import ui as nicegui

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


def main() -> None:
    config.ensure_dirs()
    db.init_db()
    enrich.start_worker()
    watcher.start_watcher()
    mount_archives()

    nicegui.run_with(
        app,
        title="Second cerveau",
        storage_secret="second-brain-v0",
        dark=None,
    )

    import uvicorn

    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")


if __name__ == "__main__":
    main()
