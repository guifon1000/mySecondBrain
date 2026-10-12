"""Serveur local de l'Archipel : édition d'idées, recherche, ouverture des PDF.

Lancer :  .venv/Scripts/python tools/archipel_serve.py
Puis ouvrir http://127.0.0.1:8765/

Routes :
  GET  /                      la page Archipel.html
  GET  /api/idee?titre=...    lit une idée (frontmatter + corps)
  PUT  /api/idee              écrit une idée  {titre, corps, nouveau_titre?}
  GET  /api/cherche?q=...     idées + pages PDF correspondant aux mots
  GET  /pdf?p=...&page=N      sert un PDF (racines en liste blanche uniquement)

Garde-fous :
  - toutes les fiches sont `author: user` : l'utilisateur édite les siennes
  - seuls les fichiers sous Fiches/ sont écrits
  - PDF : seules les racines autorisées sont servies (pas d'accès au disque)
  - écoute sur 127.0.0.1 uniquement
"""
import json
import re
import sqlite3
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "myVault"
FICHES = VAULT / "Fiches"
HTML = VAULT / "Archipel.html"
CORPUS_DB = ROOT / "data" / "corpus-index.db"
LIB_DB = ROOT / "data" / "pdf-library-index.db"
PDF_RACINES = [VAULT / "biblio" / "pdf", Path("E:/pdf_library")]
PORT = 8765


# ---------------------------------------------------------------- idées

def trouver_idee(titre: str) -> Path | None:
    for sous in ("idees", "notes", "sources"):
        p = FICHES / sous / f"{titre}.md"
        if p.exists():
            return p
    return None


def lire_idee(titre: str) -> dict:
    p = trouver_idee(titre)
    if p is None:
        raise FileNotFoundError(titre)
    texte = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?", texte, re.DOTALL)
    fm = m.group(1) if m else ""
    corps = texte[m.end():] if m else texte
    return {"titre": titre, "frontmatter": fm, "corps": corps.lstrip("\n"),
            "chemin": str(p.relative_to(VAULT))}


def ecrire_idee(titre: str, corps: str, nouveau_titre: str | None) -> dict:
    p = trouver_idee(titre)
    if p is None:
        raise FileNotFoundError(titre)
    texte = p.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?", texte, re.DOTALL)
    fm = m.group(0) if m else ""
    nouveau = f"{fm}{corps.strip()}\n"
    cible = p
    if nouveau_titre and nouveau_titre != titre:
        if not re.match(r"^[^/\\:*?\"<>|]{3,120}$", nouveau_titre):
            raise ValueError("titre invalide")
        cible = p.with_name(nouveau_titre + ".md")
        if cible.exists():
            raise FileExistsError(nouveau_titre)
    cible.write_text(nouveau, encoding="utf-8")
    if cible != p:
        p.unlink()
        # réécriture des liens internes vers l'ancien titre (idées agent seulement)
        for f in VAULT.rglob("*.md"):
            t = f.read_text(encoding="utf-8")
            if f"[[{titre}]]" in t and not re.search(r"^author:\s*guill", t, re.M):
                f.write_text(t.replace(f"[[{titre}]]", f"[[{nouveau_titre}]]"), encoding="utf-8")
    return lire_idee(cible.stem)


# ---------------------------------------------------------------- recherche

def _fts_query(q: str) -> str:
    mots = [w for w in re.findall(r"[\wà-ÿÀ-Ÿ]{2,}", q)]
    return " AND ".join(f'"{w}"*' for w in mots) if mots else ""


def chercher(q: str, n_pdf: int = 30) -> dict:
    fts = _fts_query(q)
    if not fts:
        return {"idees": [], "pdf": []}
    mots = q.split()
    idees = []
    for sous in ("idees", "notes", "sources"):
        for p in sorted((FICHES / sous).glob("*.md")):
            t = p.read_text(encoding="utf-8")
            if all(re.search(re.escape(w), t, re.IGNORECASE) for w in mots):
                m = re.search(re.escape(mots[0]), t, re.IGNORECASE)
                debut = max(0, m.start() - 60) if m else 0
                idees.append({"titre": p.stem,
                              "extrait": t[debut:debut + 160].replace("\n", " ")})
    pdf = []
    for db, label in ((CORPUS_DB, "biblio"), (LIB_DB, "lib")):
        if not db.exists():
            continue
        c = sqlite3.connect(db)
        c.row_factory = sqlite3.Row
        if label == "biblio":
            rows = c.execute(
                "SELECT d.ref, d.title, bm25(docs_fts) r, "
                "snippet(docs_fts, 1, '«', '»', ' … ', 24) s "
                "FROM docs_fts JOIN docs d ON d.id = docs_fts.rowid "
                "WHERE docs_fts MATCH ? AND d.kind='pdf_page' ORDER BY r LIMIT ?",
                (fts, n_pdf)).fetchall()
            for r in rows:
                nom, _, page = r["ref"].partition(" | page ")
                pdf.append({"source": "biblio", "fichier": nom, "page": int(page or 1),
                            "titre": r["title"], "extrait": r["s"]})
        else:
            rows = c.execute(
                "SELECT f.path, f.name, p.page, snippet(pages_fts, 0, '«', '»', ' … ', 24) s "
                "FROM pages_fts JOIN pages p ON p.rowid = pages_fts.rowid "
                "JOIN files f ON f.id = p.file_id "
                "WHERE pages_fts MATCH ? ORDER BY bm25(pages_fts) LIMIT ?",
                (fts, n_pdf)).fetchall()
            for r in rows:
                pdf.append({"source": "lib", "fichier": r["path"], "page": r["page"],
                            "titre": r["name"], "extrait": r["s"]})
        c.close()
    return {"idees": idees, "pdf": regrouper(pdf)[:n_pdf]}


def regrouper(hits: list[dict]) -> list[dict]:
    """Un document = une entrée ; ses pages sont listées (la première sert de lien)."""
    par_doc: dict[tuple, dict] = {}
    for h in hits:
        cle = (h["source"], h["fichier"])
        if cle not in par_doc:
            par_doc[cle] = {"source": h["source"], "fichier": h["fichier"], "titre": h["titre"],
                            "page": h["page"], "pages": [], "extrait": h["extrait"]}
        if h["page"] not in par_doc[cle]["pages"]:
            par_doc[cle]["pages"].append(h["page"])
    return sorted(par_doc.values(), key=lambda d: -len(d["pages"]))


# ---------------------------------------------------------------- PDF

def pdf_autorise(chemin: str) -> Path | None:
    p = Path(chemin).resolve()
    if p.suffix.lower() != ".pdf" or not p.is_file():
        return None
    for racine in PDF_RACINES:
        try:
            p.relative_to(racine.resolve())
            return p
        except ValueError:
            continue
    return None


def pdf_source(chemin: str) -> Path | None:
    """Résout un nom de la biblio (relatif) ou un chemin de E: (absolu)."""
    if Path(chemin).is_absolute():
        return pdf_autorise(chemin)
    return pdf_autorise(str(PDF_RACINES[0] / chemin))


# ---------------------------------------------------------------- HTTP

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        if u.path == "/":
            body = HTML.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif u.path == "/api/idee":
            try:
                self._json(200, lire_idee(qs.get("titre", [""])[0]))
            except FileNotFoundError:
                self._json(404, {"erreur": "idée introuvable"})
        elif u.path == "/api/cherche":
            self._json(200, chercher(qs.get("q", [""])[0]))
        elif u.path == "/pdf":
            p = pdf_source(qs.get("p", [""])[0])
            if p is None:
                self.send_error(404)
                return
            body = p.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_PUT(self):
        if urllib.parse.urlparse(self.path).path != "/api/idee":
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", "0"))
        try:
            d = json.loads(self.rfile.read(n).decode("utf-8"))
            res = ecrire_idee(d["titre"], d["corps"], d.get("nouveau_titre"))
            self._json(200, res)
        except PermissionError as e:
            self._json(403, {"erreur": str(e)})
        except FileNotFoundError:
            self._json(404, {"erreur": "idée introuvable"})
        except FileExistsError:
            self._json(409, {"erreur": "ce titre existe déjà"})
        except (ValueError, KeyError) as e:
            self._json(400, {"erreur": str(e)})


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Archipel : http://127.0.0.1:{PORT}/  (Ctrl+C pour arrêter)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
