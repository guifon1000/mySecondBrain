"""Pont vers le vault Obsidian — option A (cahier des charges v0).

Règles :
- la DB est la source de vérité ; le vault est l'espace d'écriture ;
- l'app crée un stub .md à la création d'un projet et ne RELIT ensuite que le
  frontmatter (`id`, `description`) ;
- l'app ne réécrit jamais un fichier existant ;
- le lien entre un fichier projet et un projet passe par `id:` en frontmatter,
  pas par le nom du fichier (renommer dans Obsidian ne casse rien).
"""
import logging
import re
import sqlite3
from datetime import date
from pathlib import Path

from . import config

log = logging.getLogger("vault")

FM_ID = re.compile(r"^id:\s*(\d+)\s*$", re.MULTILINE)
FM_DESC = re.compile(r"^description:\s*(.*)$", re.MULTILINE)


def projects_dir() -> Path | None:
    """Dossier Projets du vault — None si le vault n'existe pas (pas d'erreur)."""
    vault = Path(config.VAULT_DIR)
    if not vault.is_dir():
        return None
    d = vault / config.VAULT_PROJECTS_DIR
    d.mkdir(exist_ok=True)
    return d


def slugify(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9àâäéèêëîïôöùûüç]+", "-", s)
    return s.strip("-") or "projet"


def create_project_stub(project_id: int, title: str, description: str) -> Path | None:
    """Crée le fichier projet s'il n'existe pas. Idempotent, jamais destructif."""
    d = projects_dir()
    if d is None:
        return None
    path = d / f"{slugify(title)}.md"
    if path.exists():
        # Conflit de nom : suffixe par id pour garantir l'unicité sans écraser
        path = d / f"{slugify(title)}-{project_id}.md"
        if path.exists():
            return path
    path.write_text(
        "---\n"
        f"id: {project_id}\n"
        f"description: {description.strip()}\n"
        f"created: {date.today().isoformat()}\n"
        "---\n\n"
        f"# {title}\n\n"
        "*Stub créé depuis le tri. Écris ici ce que tu veux — seule la ligne\n"
        "`description:` du frontmatter est relue par l'app (embedding du projet\n"
        "tant qu'il n'a pas d'items liés).*\n",
        encoding="utf-8",
    )
    log.info("stub projet créé : %s", path.name)
    return path


def read_frontmatter(path: Path) -> dict:
    """Lit `id` et `description` du frontmatter. Tolérant : pas de YAML."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    out: dict = {}
    idm = FM_ID.search(block)
    if idm:
        out["id"] = int(idm.group(1))
    dm = FM_DESC.search(block)
    if dm:
        lines = [dm.group(1).strip().strip('"').strip("'")]
        for line in block[dm.end():].splitlines():
            if not line.startswith("  "):
                break
            lines.append(line.strip())
        out["description"] = " ".join(l for l in lines if l)
    return out


def sync_projects(conn: sqlite3.Connection) -> None:
    """Appelé au chargement de la page de tri : relit le frontmatter des fichiers
    projet du vault et met à jour la colonne `description` de la DB. Pas d'IA,
    pas d'embedding — juste garder la DB alignée avec ce que tu écris.
    """
    d = projects_dir()
    if d is None:
        return
    from . import db

    for p in db.all_projects(conn):
        fpath = Path(p["vault_path"]) if p["vault_path"] else None
        if fpath is None or not fpath.is_file():
            # cherche par id si le fichier a été renommé dans Obsidian
            for cand in d.glob("*.md"):
                if read_frontmatter(cand).get("id") == p["id"]:
                    fpath = cand
                    break
            if fpath is None:
                continue
            conn.execute(
                "UPDATE projects SET vault_path = ? WHERE id = ?", (str(fpath), p["id"])
            )
        try:
            mtime = fpath.stat().st_mtime
        except OSError:
            continue
        stored = conn.execute(
            "SELECT vault_mtime, description FROM projects WHERE id = ?", (p["id"],)
        ).fetchone()
        if stored and stored["vault_mtime"] is not None and abs(mtime - stored["vault_mtime"]) < 1:
            continue
        fm = read_frontmatter(fpath)
        if fm.get("id") != p["id"]:
            continue
        desc = fm.get("description", "").strip()
        if desc != (stored["description"] if stored else ""):
            conn.execute(
                "UPDATE projects SET description = ?, vault_mtime = ? WHERE id = ?",
                (desc, mtime, p["id"]),
            )
            log.info("description du projet %s synchronisée depuis le vault", p["id"])
        else:
            conn.execute(
                "UPDATE projects SET vault_mtime = ? WHERE id = ?", (mtime, p["id"])
            )
