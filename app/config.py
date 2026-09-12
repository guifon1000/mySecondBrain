"""Configuration par variables d'environnement, avec valeurs par défaut.

Un fichier .env à la racine est chargé si présent (sans dépendance externe).
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()


def _path(name: str, default: str) -> Path:
    return Path(os.getenv(name, default))


# --- Dossiers -------------------------------------------------------------
DATA_DIR = _path("SB_DATA_DIR", ROOT / "data")
ARCHIVE_DIR = DATA_DIR / "archives"
WATCH_DIR = _path("SB_WATCH_DIR", DATA_DIR / "watched")
DB_PATH = DATA_DIR / "secondbrain.db"

# --- Sécurité -------------------------------------------------------------
INGEST_TOKEN = os.getenv("SB_INGEST_TOKEN", "change-me")

# --- Réseau ---------------------------------------------------------------
HOST = os.getenv("SB_HOST", "0.0.0.0")
PORT = int(os.getenv("SB_PORT", "8420"))

# --- Ollama ---------------------------------------------------------------
OLLAMA_URL = os.getenv("SB_OLLAMA_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.getenv("SB_EMBED_MODEL", "nomic-embed-text")
# Vision désactivé par défaut (voir cahier des charges) : SB_VISION_MODEL=moondream pour activer
VISION_MODEL = os.getenv("SB_VISION_MODEL", "")

# --- OCR ------------------------------------------------------------------
OCR_LANG = os.getenv("SB_OCR_LANG", "fra+eng")
OCR_MIN_CHARS = int(os.getenv("SB_OCR_MIN_CHARS", "20"))

# --- Rituel ---------------------------------------------------------------
SESSION_MAX_ITEMS = int(os.getenv("SB_SESSION_MAX_ITEMS", "15"))
# Seuil de suggestion de lien : None = désactivé (défaut v0.1, voir cahier des charges).
# Après calibrage sur suggestion_log, fixer par ex. SB_SUGGEST_THRESHOLD=0.45
SUGGEST_THRESHOLD = (
    float(os.getenv("SB_SUGGEST_THRESHOLD")) if os.getenv("SB_SUGGEST_THRESHOLD") else None
)


def ensure_dirs() -> None:
    for d in (DATA_DIR, ARCHIVE_DIR, WATCH_DIR):
        d.mkdir(parents=True, exist_ok=True)
