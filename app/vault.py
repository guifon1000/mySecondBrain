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
import shutil
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


# --- Inbox dans le vault (artefacts app) ------------------------------------
#
# Une note .md par item : myVault/Inbox/ à l'ingestion, déplacée vers
# myVault/Projets/<slug>/ quand l'item est lié, vers myVault/Archives/ quand
# il est archivé. Ce sont des artefacts gérés par l'app (l'app ne réécrit
# jamais les fichiers ÉCRITS PAR L'UTILISATEUR — ici elle ne fait que créer,
# déplacer et mettre à jour le frontmatter de ses propres notes). Lien par
# `sb_id` frontmatter : renommer une note ne casse que le déplacement auto.

TYPE_LABELS = {"screenshot": "Capture d'écran", "photo": "Photo",
               "bookmark": "Bookmark", "note": "Note", "file": "Fichier"}


def _vault_subdir(name: str) -> Path | None:
    vault = Path(config.VAULT_DIR)
    if not vault.is_dir():
        return None
    d = vault / name
    d.mkdir(exist_ok=True)
    return d


def _item_slug(item) -> str:
    date_part = (item["created_at"] or "")[:10]
    label = item["title"] or (item["ocr_text"] or "")[:40]
    slug = slugify(label) if label else item["type"]
    return f"SB-{item['id']:04d} {date_part} {slug}".strip()


def _item_frontmatter(item, status: str, project_title: str = "") -> str:
    return (
        "---\n"
        f"sb_id: {item['id']}\n"
        f"type: {item['type']}\n"
        f"status: {status}\n"
        f"created: {(item['created_at'] or '')[:10]}\n"
        f"url: {item['url'] or ''}\n"
        f"project: {project_title}\n"
        "---\n"
    )


def _piece_name(item) -> str | None:
    if not item["source_path"]:
        return None
    return Path(item["source_path"]).name


def _copy_piece(item) -> str | None:
    """Copie la pièce jointe (image/pdf) dans myVault/pieces/ — nom unique
    (horodaté) garanti par l'archivage. Retourne le nom pour l'embed."""
    name = _piece_name(item)
    if not name:
        return None
    pieces = _vault_subdir(config.VAULT_PIECES_DIR)
    if pieces is None:
        return None
    src = Path(item["source_path"])
    dest = pieces / name
    if not dest.exists() and src.exists():
        shutil.copy2(src, dest)
    return name


def _item_body(item) -> str:
    lines = [f"# {TYPE_LABELS.get(item['type'], item['type'])} "
             f"{(item['created_at'] or '')[:16]}", ""]
    piece = _copy_piece(item)
    if piece and item["type"] in ("screenshot", "photo"):
        lines += [f"![[{piece}]]", ""]
    elif piece and item["type"] == "file":
        lines += [f"[[{piece}]] — fichier archivé", ""]
    if item["url"]:
        lines += [f"<{item['url']}>" + (f" — {item['title']}" if item["title"] else ""), ""]
    if item["ocr_text"]:
        lines += ["```", item["ocr_text"][:600], "```", ""]
    return "\n".join(lines)


def create_item_note(conn, item) -> Path | None:
    """Crée la note inbox d'un item (idempotent). Appelé après enrichissement."""
    d = _vault_subdir(config.VAULT_INBOX_DIR)
    if d is None or item is None:
        return None
    path = d / f"{_item_slug(item)}.md"
    if not path.exists():
        path.write_text(
            _item_frontmatter(item, "inbox") + "\n" + _item_body(item), encoding="utf-8"
        )
    conn.execute("UPDATE items SET vault_note = ? WHERE id = ?", (str(path), item["id"]))
    return path


def move_item_note(conn, item, new_status: str, project_title: str = "") -> None:
    """Déplace la note quand le statut change, frontmatter mis à jour,
    corps préservé (y compris d'éventuelles notes utilisateur)."""
    vault_root = Path(config.VAULT_DIR)
    if not vault_root.is_dir():
        return
    note = Path(item["vault_note"]) if item["vault_note"] else None
    if note is None or not note.is_file():
        # note renommée/perdue : on retente par sb_id dans les dossiers connus
        for folder in (config.VAULT_INBOX_DIR, config.VAULT_ARCHIVE_DIR,
                       config.VAULT_PROJECTS_DIR):
            base = vault_root / folder
            if base.is_dir():
                for cand in base.rglob("*.md"):
                    if read_frontmatter(cand).get("sb_id") == item["id"]:
                        note = cand
                        break
                if note:
                    break
        if note is None:
            return
    target_dir = (
        vault_root / config.VAULT_PROJECTS_DIR / slugify(project_title)
        if new_status == "linked" and project_title
        else vault_root / config.VAULT_ARCHIVE_DIR
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / note.name
    text = note.read_text(encoding="utf-8")
    new_fm = _item_frontmatter(item, new_status, project_title)
    body = re.sub(r"^---\n.*?\n---\n?", "", text, count=1, flags=re.DOTALL)
    shutil.move(str(note), str(target))
    target.write_text(new_fm + "\n" + body, encoding="utf-8")
    conn.execute("UPDATE items SET vault_note = ? WHERE id = ?", (str(target), item["id"]))


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
