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

import sys


def _windows_capture_dirs() -> list[Path]:
    """Dossier de captures d'écran du PC, tel que configuré dans le registre
    (gère Windows français : « Captures d'écran » sous OneDrive/Pictures).

    On cible le sous-dossier de captures plutôt que Pictures en entier :
    ce dernier contient souvent la pellicule OneDrive (sauvegarde caméra
    du téléphone) qu'on ne veut PAS ingérer en v0 locale.
    """
    import os
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
    keywords = ("screenshot", "capture", "écran", "ecran")
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
            value, _ = winreg.QueryValueEx(k, "{B7BEDE81-DF94-4682-A7A8-5715B85EDF16}")
            shots = Path(os.path.expandvars(str(value)))
            if shots.is_dir():
                return [shots]
    except OSError:
        pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
            value, _ = winreg.QueryValueEx(k, "My Pictures")
            pictures = Path(os.path.expandvars(str(value)))
    except OSError:
        return []
    if not pictures.is_dir():
        return []
    # Sous-dossier de captures dans Pictures ? sinon Pictures lui-même
    for child in sorted(pictures.iterdir()):
        if child.is_dir() and any(kw in child.name.lower() for kw in keywords):
            return [child]
    return [pictures]


def _watch_dirs() -> list[Path]:
    """Dossiers surveillés pour les captures d'images.

    Défaut (v0 locale) : le dossier de captures d'écran du PC (détection
    registre, gère Windows FR/EN), sinon ./data/watched. Surchargeable via
    SB_WATCH_DIRS (séparateur « ; »).
    """
    raw = os.getenv("SB_WATCH_DIRS", "")
    if raw:
        return [Path(p) for p in raw.split(";") if p]
    if sys.platform.startswith("win"):
        dirs = _windows_capture_dirs()
        if dirs:
            return dirs
    return [DATA_DIR / "watched"]


WATCH_DIRS = _watch_dirs()
DB_PATH = DATA_DIR / "secondbrain.db"

# --- Sécurité -------------------------------------------------------------
# Token optionnel pour l'endpoint d'ingestion. Vide = pas d'auth (v0 100% locale,
# endpoint joignable uniquement en local).
INGEST_TOKEN = os.getenv("SB_INGEST_TOKEN", "")

# --- Réseau ---------------------------------------------------------------
HOST = os.getenv("SB_HOST", "0.0.0.0")
PORT = int(os.getenv("SB_PORT", "8420"))

# --- IA --------------------------------------------------------------------
# Pas d'IA embarquée dans l'app (pas de modèle local, pas de clé API).
# Le travail sémantique (suggestions de liens, ancrage, synthèse) est fait
# par l'agent Pi dédié au projet, à la demande, en lisant la base SQLite.
# Les colonnes embedding restent dans le schéma (NULL) pour un usage futur.

# --- Vault Obsidian (pont unidirectionnel, option A) -----------------------
# myVault = espace d'écriture ; la DB reste la source de vérité du pipeline.
# L'app crée un stub .md à la création de projet et ne RELIT que le
# frontmatter (id, description) — elle ne réécrit jamais le fichier.
VAULT_DIR = _path("SB_VAULT_DIR", ROOT / "myVault")
VAULT_PROJECTS_DIR = os.getenv("SB_VAULT_PROJECTS_DIR", "Projets")

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
    for d in (DATA_DIR, ARCHIVE_DIR, DATA_DIR / "watched"):
        d.mkdir(parents=True, exist_ok=True)
