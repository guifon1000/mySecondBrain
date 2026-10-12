"""Archipel — serveur local de l'environnement créatif (v3).

    .venv/Scripts/python tools/archipel_serve.py
    → http://127.0.0.1:8765/

Routes :
  GET    /                       la page (tools/archipel_ui.html)
  GET    /api/graphe             nœuds, arêtes, positions, états de casquette
  GET    /api/fiche?titre=       une fiche (frontmatter + corps + métadonnées)
  POST   /api/fiche              créer {titre, type, corps, domaines?}
  PUT    /api/fiche              éditer {titre, corps, nouveau_titre?, domaines?, type?}
  GET    /api/doublons?q=        fiches proches (anti-doublons à la création)
  POST   /api/lien               {a, b}           : lien confirmé (les deux fiches)
  DELETE /api/lien               {a, b}           : retirer le lien
  POST   /api/suggere/valide     {a, b}           : valider une suggestion → lien
  DELETE /api/suggere            {a, b}           : supprimer une suggestion
  GET    /api/cherche?q=         fiches + pages PDF (biblio et E:)
  GET    /pdf?p=&page=           sert un PDF (racines en liste blanche)
  GET    /code?p=dépôt/chemin    sert un fichier de code d'un dépôt connu

Principes :
  - le vault est la source unique ; les fiches sont author: user
  - un lien confirmé est écrit dans les DEUX fiches (le graphe est
    symétrique) ; une suggestion vit dans le champ suggere des deux
  - l'écriture reste réservée à l'utilisateur via cette interface
"""
import json
import re
import sqlite3
import sys
import urllib.parse
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "myVault"
FICHES = VAULT / "Fiches"
UI = ROOT / "tools" / "archipel_ui.html"
sys.path.insert(0, str(ROOT / "tools"))
import graphe  # noqa: E402

PDF_RACINES = [VAULT / "biblio" / "pdf", Path("E:/pdf_library")]
PORT = 8765

DOSSIERS = {"idee": "idees", "note": "notes", "source": "sources",
            "capture": "captures", "projet": None, "casquette": None}


# ------------------------------------------------------------- frontmatter

def sep_crlf(texte: str) -> tuple[str, str, str]:
    """-> (avant_fm, fm, après_fm) ; normalise LF."""
    texte = texte.replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n?", texte, re.DOTALL)
    if m:
        return "", m.group(1), texte[m.end():]
    return "", "", texte


def set_champ(fm: str, nom: str, valeurs: list[str] | None) -> str:
    """Réécrit (ou supprime/ajoute) un champ liste du frontmatter."""
    lignes = [l for l in fm.split("\n") if not l.startswith(f"{nom}:")]
    if valeurs:
        vals = ", ".join(f'"[[{v}]]"' for v in valeurs)
        lignes.append(f"{nom}: [{vals}]")
    return "\n".join(lignes)


def set_champ_simple(fm: str, nom: str, valeur: str | None) -> str:
    lignes = [l for l in fm.split("\n") if not l.startswith(f"{nom}:")]
    if valeur:
        lignes.append(f'{nom}: "{valeur}"')
    return "\n".join(lignes)


def lire_fm_valeurs(fm: str, nom: str) -> list[str]:
    return graphe.champ(fm, nom)


# ------------------------------------------------------------- fiches

GENERES = {"Galaxie"}


def fichier_de(titre: str) -> Path | None:
    """Toute fiche du vault (Fiches, Projets, Casquettes) — sauf les générées."""
    if titre in GENERES or titre.startswith("00 —"):
        return None
    for racine in (FICHES, VAULT / "Projets", VAULT / "Casquettes"):
        for p in racine.rglob(f"{titre}.md"):
            return p
    return None


def normalise(texte: str) -> str:
    texte = texte.replace("\r\n", "\n")
    return re.sub(r"\n{3,}", "\n\n", texte).strip()


def lire_fiche(titre: str) -> dict:
    p = fichier_de(titre)
    if p is None:
        raise FileNotFoundError(titre)
    f = graphe.lire_fiche(p)
    f["chemin"] = str(p.relative_to(VAULT))
    return f


def ecrire_fiche(titre: str, corps: str, nouveau_titre=None,
                 domaines=None, type_f=None) -> dict:
    p = fichier_de(titre)
    if p is None:
        raise FileNotFoundError(titre)
    avant_fm, fm, _corps = sep_crlf(p.read_text(encoding="utf-8"))
    if domaines is not None:
        fm = set_champ(fm, "domaines", [d.strip() for d in domaines if d.strip()])
    if type_f and type_f in DOSSIERS and DOSSIERS[type_f]:
        fm = set_champ_simple(fm, "type", type_f)
    if nouveau_titre:
        nouveau_titre = nouveau_titre.strip()
        if not re.match(r"^[^/\\:*?\"<>|]{3,140}$", nouveau_titre):
            raise ValueError("titre invalide (3-140 car., sans /\\:*?\"<>|)")
        if fichier_de(nouveau_titre):
            raise FileExistsError(nouveau_titre)
    p.write_text(f"---\n{fm}\n---\n{normalise(corps)}\n", encoding="utf-8")
    if nouveau_titre:
        renommer(p, nouveau_titre)
        return lire_fiche(nouveau_titre)
    return lire_fiche(titre)


def creer_fiche(titre: str, type_f: str, corps: str, domaines=None) -> dict:
    titre = titre.strip()
    if not re.match(r"^[^/\\:*?\"<>|]{3,140}$", titre):
        raise ValueError("titre invalide (3-140 car., sans /\\:*?\"<>|)")
    if fichier_de(titre):
        raise FileExistsError(titre)
    dossier = DOSSIERS.get(type_f)
    if dossier is None:
        raise ValueError(f"type inconnu : {type_f!r} (idee/note/source/capture)")
    doms = [d.strip() for d in (domaines or []) if d.strip()]
    fm = ["type: " + type_f, "author: user"]
    if doms:
        fm.append("domaines: [" + ", ".join(doms) + "]")
    fm.append(f"created: {date.today().isoformat()}")
    p = FICHES / dossier / f"{titre}.md"
    p.parent.mkdir(exist_ok=True)
    p.write_text("---\n" + "\n".join(fm) + "\n---\n" + normalise(corps) + "\n",
                 encoding="utf-8")
    return lire_fiche(titre)


def renommer(p: Path, nouveau_titre: str):
    ancien = p.stem
    cible = p.with_name(nouveau_titre + ".md")
    p.rename(cible)
    # propagation : corps ([[ancien]]) et champs (lie/suggere) de toutes les fiches
    for racine in (FICHES, VAULT / "Projets", VAULT / "Casquettes"):
        for f in racine.rglob("*.md"):
            t = f.read_text(encoding="utf-8")
            n = t.replace(f"[[{ancien}]]", f"[[{nouveau_titre}]]")
            if n == t:
                continue
            _a, fm, corps = sep_crlf(n)
            for champ_nom in ("lie", "suggere"):
                vals = lire_fm_valeurs(fm, champ_nom)
                if ancien in vals:
                    fm = set_champ(fm, champ_nom,
                                   [nouveau_titre if v == ancien else v for v in vals])
            f.write_text(f"---\n{fm}\n---\n{corps}", encoding="utf-8")


def lien_modifier(a: str, b: str, champ_nom: str, ajouter: bool):
    """Modifie un lien (lie/suggere) dans les deux fiches — symétrique."""
    pa, pb = fichier_de(a), fichier_de(b)
    if pa is None or pb is None:
        raise FileNotFoundError(a if pa is None else b)
    for p in (pa, pb):
        _av, fm, corps = sep_crlf(p.read_text(encoding="utf-8"))
        vals = lire_fm_valeurs(fm, champ_nom)
        autre = (b if p == pa else a)
        if ajouter and autre not in vals:
            vals.append(autre)
        elif not ajouter and autre in vals:
            vals.remove(autre)
        fm = set_champ(fm, champ_nom, vals)
        p.write_text(f"---\n{fm}\n---\n{corps}", encoding="utf-8")


# ------------------------------------------------------------- doublons

def doublons(q: str) -> list[dict]:
    # faux-stemming : 6 premiers caractères (gabarit/gabarits → gabari)
    mots = {t[:6] for t in graphe.tokens(q)}
    fiches, *_ = graphe.construire()
    if not mots:
        return []
    cands = []
    for t, f in fiches.items():
        if t in GENERES or t.startswith("00 —"):
            continue
        tk = {v[:6] for v in graphe.tokens(f["texte"])}
        inter = mots & tk
        if not inter:
            continue
        jaccard = len(inter) / len(mots | tk)
        if jaccard >= 0.08 or len(inter) >= 3:
            cands.append({"titre": t, "type": f["type"], "score": round(jaccard, 2),
                          "mots": sorted(inter)[:6]})
    return sorted(cands, key=lambda c: -c["score"])[:6]


# ------------------------------------------------------------- recherche

def _fts_query(q: str) -> str:
    mots = re.findall(r"[\wà-ÿÀ-Ÿ]{2,}", q)
    return " AND ".join(f'"{w}"*' for w in mots) if mots else ""


def chercher(q: str, n_pdf: int = 30) -> dict:
    mots = q.split()
    fiches = []
    for racine in (FICHES, VAULT / "Projets", VAULT / "Casquettes"):
        for p in sorted(racine.rglob("*.md")):
            if p.stem in GENERES or p.stem.startswith("00 —"):
                continue
            t = p.read_text(encoding="utf-8").replace("\r\n", "\n")
            if all(re.search(re.escape(w), t, re.IGNORECASE) for w in mots):
                i = t.find(mots[0]) if mots else 0
                fiches.append({"titre": p.stem,
                               "extrait": t[max(0, i - 60):i + 160].replace("\n", " ")})
    pdf = []
    fts = _fts_query(q)
    if fts:
        for db, label in ((ROOT / "data" / "corpus-index.db", "biblio"),
                          (ROOT / "data" / "pdf-library-index.db", "lib")):
            if not db.exists():
                continue
            c = sqlite3.connect(db)
            c.row_factory = sqlite3.Row
            if label == "biblio":
                rows = c.execute(
                    "SELECT d.ref, d.title, snippet(docs_fts, 1, '«', '»', ' … ', 24) s "
                    "FROM docs_fts JOIN docs d ON d.id = docs_fts.rowid "
                    "WHERE docs_fts MATCH ? AND d.kind='pdf_page' ORDER BY bm25(docs_fts) LIMIT ?",
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
    # regrouper par document
    par_doc = {}
    for h in pdf:
        cle = (h["source"], h["fichier"])
        d = par_doc.setdefault(cle, {"source": h["source"], "fichier": h["fichier"],
                                     "titre": h["titre"], "page": h["page"],
                                     "pages": [], "extrait": h["extrait"]})
        if h["page"] not in d["pages"]:
            d["pages"].append(h["page"])
    docs = sorted(par_doc.values(), key=lambda d: -len(d["pages"]))[:n_pdf]
    return {"fiches": fiches, "pdf": docs}


# ------------------------------------------------------------- fichiers servis

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


def code_autorise(chemin: str) -> Path | None:
    """depot/sous/chemin.py — le dépôt vient de la DB (chemins connus)."""
    chemins, _ = graphe.depots()
    premier, restant = chemin.split("/", 1)[0], chemin.split("/", 1)[1]
    for titre, racine in chemins.items():
        if titre.casefold() == premier.casefold() and racine:
            p = (Path(racine) / restant).resolve()
            if p.is_file() and p.suffix in (".py", ".md", ".rs", ".toml", ".json", ".txt"):
                return p
            # le chemin peut inclure le package du dépôt (rincewind/geometry/...)
            p2 = (Path(racine) / chemin).resolve()
            if p2.is_file():
                return p2
    return None


# ------------------------------------------------------------- HTTP

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

    def _fichier(self, chemin: Path, mime: str):
        body = chemin.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _graphe_data(self):
        fiches, ar, su, chemins_dep, casq = graphe.construire()
        pos = graphe.positions(fiches, ar, su)
        etats, scores = graphe.eclairage(casq, fiches)
        _, climate_color = _climats(fiches)
        nodes = []
        for t, f in fiches.items():
            if f["type"] not in graphe.TYPES_DESSINES:
                continue
            x, y = pos.get(t, (0, 0))
            # vis-network travaille en unités monde : l'échelle du fit
            # déforme tout si les positions restent en unités normalisées —
            # on livre les positions directement en pixels écran
            x *= 10.0
            y *= 10.0
            col = climate_color.get(f["domaines"][0] if f["domaines"] else "", "#6c7a89")
            col_hex = "#%02x%02x%02x" % tuple(int(c * 255) for c in col[:3]) \
                if isinstance(col, tuple) else col
            nodes.append({
                "id": t, "label": graphe.wrap(t, 26), "type": f["type"],
                "domaines": f["domaines"], "chemin": f.get("chemin", ""),
                "n_liens": len(f["lie"]),
                "x": x, "y": y,
                "size": 6 + f["diametre"] / 55,
                "size_off": 4 + f["diametre"] / 110,
                "fond": col_hex,
                "satellite": f["type"] == "source",
            })
        ids = {n["id"] for n in nodes}
        edges = []
        vus = set()
        for a, b in ar:
            if (a, b) not in vus and a in ids and b in ids:
                edges.append({"from": a, "to": b, "kind": "lie"})
                vus.add((a, b))
        vus = set()
        for a, b in su:
            if (a, b) not in vus and a in ids and b in ids:
                edges.append({"from": a, "to": b, "kind": "suggere"})
                vus.add((a, b))
        casq_noms = list(casq)
        return {
            "nodes": nodes, "edges": edges,
            "etats": etats, "scores": scores,
            "options": [[n, n] for n in casq_noms] + [["__aucune__", "aucune (carte neutre)"]],
            "default": next((n for n in casq_noms if casq[n]["active"]), "__aucune__"),
            "fiches_hors_carte": [t for t in fiches if fiches[t]["type"] not in graphe.TYPES_DESSINES],
        }

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        q1 = lambda k: urllib.parse.unquote(qs.get(k, [""])[0])
        if u.path == "/":
            self._fichier(UI, "text/html; charset=utf-8")
        elif u.path == "/api/graphe":
            self._json(200, self._graphe_data())
        elif u.path == "/api/fiche":
            try:
                self._json(200, lire_fiche(q1("titre")))
            except FileNotFoundError:
                self._json(404, {"erreur": "fiche introuvable"})
        elif u.path == "/api/doublons":
            self._json(200, {"candidats": doublons(q1("q"))})
        elif u.path == "/api/cherche":
            self._json(200, chercher(q1("q")))
        elif u.path == "/pdf":
            p = pdf_autorise(q1("p"))
            if p is None:
                self.send_error(404)
                return
            self._fichier(p, "application/pdf")
        elif u.path == "/code":
            p = code_autorise(q1("p"))
            if p is None:
                self.send_error(404)
                return
            self._fichier(p, "text/plain; charset=utf-8")
        else:
            self.send_error(404)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path).path
        n = int(self.headers.get("Content-Length", "0"))
        try:
            d = json.loads(self.rfile.read(n).decode("utf-8"))
            if u == "/api/fiche":
                self._json(200, creer_fiche(d["titre"], d.get("type", "note"),
                                            d.get("corps", ""), d.get("domaines")))
            elif u == "/api/lien":
                lien_modifier(d["a"], d["b"], "lie", True)
                self._json(200, {"ok": True})
            elif u == "/api/suggere/valide":
                lien_modifier(d["a"], d["b"], "suggere", False)
                lien_modifier(d["a"], d["b"], "lie", True)
                self._json(200, {"ok": True})
            else:
                self.send_error(404)
        except FileNotFoundError as e:
            self._json(404, {"erreur": f"fiche introuvable : {e}"})
        except FileExistsError as e:
            self._json(409, {"erreur": f"titre déjà pris : {e}"})
        except (ValueError, KeyError) as e:
            self._json(400, {"erreur": str(e)})

    def do_PUT(self):
        if urllib.parse.urlparse(self.path).path != "/api/fiche":
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", "0"))
        try:
            d = json.loads(self.rfile.read(n).decode("utf-8"))
            res = ecrire_fiche(d["titre"], d.get("corps"),
                               d.get("nouveau_titre"), d.get("domaines"), d.get("type"))
            self._json(200, res)
        except FileNotFoundError:
            self._json(404, {"erreur": "fiche introuvable"})
        except FileExistsError as e:
            self._json(409, {"erreur": f"titre déjà pris : {e}"})
        except (ValueError, KeyError) as e:
            self._json(400, {"erreur": str(e)})

    def do_DELETE(self):
        u = urllib.parse.urlparse(self.path).path
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        q1 = lambda k: urllib.parse.unquote(qs.get(k, [""])[0])
        try:
            if u == "/api/lien":
                lien_modifier(q1("a"), q1("b"), "lie", False)
                self._json(200, {"ok": True})
            elif u == "/api/suggere":
                lien_modifier(q1("a"), q1("b"), "suggere", False)
                self._json(200, {"ok": True})
            else:
                self.send_error(404)
        except FileNotFoundError as e:
            self._json(404, {"erreur": f"fiche introuvable : {e}"})


def _climats(fiches):
    import matplotlib.pyplot as plt
    climats = sorted({f["domaines"][0] for f in fiches.values() if f["domaines"]})
    cmap = plt.get_cmap("tab20")
    return climats, {c: cmap(i % 20 / 20) for i, c in enumerate(climats)}


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Archipel : http://127.0.0.1:{PORT}/  (Ctrl+C pour arrêter)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
