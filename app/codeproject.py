"""Scan des projets de code rattachés à un projet du second cerveau.

Principe : on ne lit pas le code. On extrait ce qui décrit l'intention du
projet — fichiers markdown (README, docs), historique git récent — et on le
stocke en base (`code_scan_text`). C'est la matière que l'agent Pi dédié au
projet lit pour suggérer des liens (il n'y a plus d'IA ni d'embedding dans
l'app elle-même).
"""
import logging
import subprocess
from datetime import datetime
from pathlib import Path

log = logging.getLogger("codeproject")

SKIP_DIRS = {
    "node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build",
    "target", ".obsidian", ".vscode", ".idea", "site-packages", ".next",
    "coverage", "vendor", ".cache",
}
MAX_MD_FILES = 30
MAX_CHARS_PER_FILE = 600
MAX_GIT_COMMITS = 40


def _md_files(root: Path) -> list[Path]:
    """Fichiers *.md du dépôt, hors artefacts. Le README racine d'abord."""
    files: list[Path] = []
    for p in sorted(root.rglob("*.md"), key=lambda x: (x.parts[1:] != (x.name,), str(x))):
        if p.is_symlink() or not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        files.append(p)
        if len(files) >= MAX_MD_FILES:
            break
    return files


def _git_log(root: Path) -> str:
    """Sujets des derniers commits — le 'quoi de neuf' du dépôt."""
    if not (root / ".git").exists():
        return ""
    try:
        r = subprocess.run(
            ["git", "log", f"--oneline", f"-{MAX_GIT_COMMITS}", "--no-decorate"],
            cwd=str(root), capture_output=True, text=True, timeout=15,
        )
        return r.stdout.strip()[:4000] if r.returncode == 0 else ""
    except Exception:
        return ""


def scan(root: Path) -> dict:
    """Retourne {md_files, text} — text = concat cap des md + historique git.
    Ce texte est stocké en base (code_scan_text) et lu par l'agent.
    """
    if not root.is_dir():
        return {"md_files": [], "text": ""}
    files = _md_files(root)
    parts: list[str] = [root.name]
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        parts.append(content[:MAX_CHARS_PER_FILE])
        if sum(len(p) for p in parts) > 8000:
            break
    git = _git_log(root)
    if git:
        parts.append(git)
    return {"md_files": files, "text": "\n".join(parts)[:8000]}


def link_and_scan(conn, project_id: int, path_str: str) -> int:
    """Lie un dossier à un projet et stocke le texte scanné en base.
    Retourne le nombre de fichiers md scannés (-1 si chemin invalide/vide)."""
    from . import db

    root = Path(path_str)
    result = scan(root)
    if not result["text"].strip():
        return -1
    conn.execute(
        "UPDATE projects SET code_scan_text = ?, code_scan_at = ? WHERE id = ?",
        (result["text"], datetime.now().isoformat(), project_id),
    )
    return len(result["md_files"])


def rescan_stale(conn, max_age_hours: int = 24) -> None:
    """Au chargement de la page de tri : rescaner les dépôts liés dont le
    scan est absent ou trop vieux (le contenu md/git évolue)."""
    from . import db

    rows = conn.execute(
        "SELECT id, code_path, code_scan_at FROM projects "
        "WHERE code_path IS NOT NULL AND code_path != ''"
    ).fetchall()
    for r in rows:
        stale = r["code_scan_at"] is None
        if not stale:
            try:
                age = datetime.fromisoformat(r["code_scan_at"])
                stale = (datetime.now() - age).total_seconds() > max_age_hours * 3600
            except ValueError:
                stale = True
        if not stale:
            continue
        try:
            n = link_and_scan_keep_path(conn, r["id"])
            if n >= 0:
                log.info("projet %s rescané (%d fichiers md)", r["id"], n)
        except Exception:
            log.exception("scan du projet %s échoué", r["id"])


def link_and_scan_keep_path(conn, project_id: int) -> int:
    p = db.project(conn, project_id)
    if p is None or not p["code_path"]:
        return -1
    return link_and_scan(conn, project_id, p["code_path"])


def rescan_stale(conn, max_age_hours: int = 24) -> None:
    """Au chargement de la page de tri : rescanner les dépôts liés dont le
    scan est absent ou trop vieux (le contenu md/git évolue)."""
    from . import db

    rows = conn.execute(
        "SELECT id, code_path, code_scan_at FROM projects "
        "WHERE code_path IS NOT NULL AND code_path != ''"
    ).fetchall()
    for r in rows:
        stale = r["code_scan_at"] is None
        if not stale:
            try:
                age = datetime.fromisoformat(r["code_scan_at"])
                stale = (datetime.now() - age).total_seconds() > max_age_hours * 3600
            except ValueError:
                stale = True
        if not stale:
            continue
        try:
            n = recompute_embedding(conn, r["id"])
            if n >= 0:
                log.info("projet %s rescané (%d fichiers md)", r["id"], n)
        except Exception:
            log.exception("scan du projet %s échoué", r["id"])
