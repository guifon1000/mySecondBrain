"""Capture v3 — le watcher des fiches.

Surveille le dossier de captures d'écran du PC (détection par registre
Windows, gère FR/EN) et l'inbox du vault. Chaque fichier vu y devient une
**fiche capture** : le fichier image est copié dans Fiches/captures/img/
et une fiche markdown naît à côté (type: capture, author: user).

Usage :  .venv/Scripts/python tools/capture.py     (tourne, Ctrl+C pour arrêter)
"""
import os
import re
import shutil
import sys
import time
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "myVault"
CAPTURES = VAULT / "Fiches" / "captures"
IMG = CAPTURES / "img"


def dossier_captures() -> Path | None:
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
    keywords = ("screenshot", "capture", "écran", "ecran")
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
            value, _ = winreg.QueryValueEx(k, "{B7BEDE81-DF94-4682-A7A8-5715B85EDF16}")
            shots = Path(os.path.expandvars(str(value)))
            if shots.is_dir():
                return shots
    except OSError:
        pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
            value, _ = winreg.QueryValueEx(k, "My Pictures")
            pictures = Path(os.path.expandvars(str(value)))
    except OSError:
        return None
    if pictures.is_dir():
        for child in sorted(pictures.iterdir()):
            if child.is_dir() and any(kw in child.name.lower() for kw in keywords):
                return child
        return pictures
    return None


def fiches_existantes() -> set[str]:
    return {p.name for p in CAPTURES.glob("*.md")}


def creer_fiche_capture(image: Path, dest: Path) -> Path:
    titre_sans_date = re_nom(image.stem)
    nom = f"{date.today().isoformat()} — {titre_sans_date}"
    p = CAPTURES / f"{nom}.md"
    i = 1
    while p.exists():
        i += 1
        p = CAPTURES / f"{nom} ({i}).md"
    cible = IMG / f"{image.name}"
    i = 1
    while cible.exists():
        cible = IMG / f"{image.stem} ({i}){image.suffix}"
        i += 1
    shutil.copy2(image, cible)
    p.write_text(
        "---\n"
        "type: capture\n"
        "author: user\n"
        f"created: {date.today().isoformat()}\n"
        f"source: {image.parent.name}\n"
        'image: "img/' + cible.name + '"\n'
        "---\n\n"
        "*(capture — écrire ici ce qu'elle montre, quand tu la trieras)*\n",
        encoding="utf-8")
    return p


def re_nom(stem: str) -> str:
    s = stem.replace("_", " ").replace("-", " ").strip()
    return s or "capture"


def main():
    CAPTURES.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(exist_ok=True)
    source = dossier_captures()
    inbox = VAULT / "Inbox"
    dossiers = [d for d in (source, inbox) if d and d.is_dir()]
    print("capture : veille sur", ", ".join(str(d) for d in dossiers))
    connus = {p.name for d in dossiers for p in d.iterdir() if p.is_file()}
    try:
        while True:
            for d in dossiers:
                for p in list(d.iterdir()):
                    if p.name in connus or not p.is_file():
                        continue
                    connus.add(p.name)
                    if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
                        # PDFs et autres : déjà gérés par la biblio ; on note
                        continue
                    try:
                        fiche = creer_fiche_capture(p, IMG)
                        print("fiche capture :", fiche.name)
                    except Exception as e:
                        print("échec :", e)
            time.sleep(2)
    except KeyboardInterrupt:
        print("arrêté")


if __name__ == "__main__":
    main()
