"""Archipel — serveur local de l'environnement créatif (v3).

    .venv/Scripts/python tools/archipel_serve.py
    → http://127.0.0.1:8765/

Routes :
  GET    /                       la page (tools/archipel_ui.html)
  GET    /api/graphe             nœuds, arêtes, positions, éclairage chantier
  GET    /api/fiche?titre=       une fiche (frontmatter + corps + métadonnées)
  POST   /api/fiche              créer {titre, type, corps, domaines?}
  PUT    /api/fiche              éditer {titre, corps, nouveau_titre?, domaines?, type?}
  GET    /api/doublons?q=        fiches proches (anti-doublons à la création)
  POST   /api/lien               {a, b}           : lien confirmé (les deux fiches)
  DELETE /api/lien               {a, b}           : retirer le lien
  POST   /api/suggere/valide     {a, b}           : valider une suggestion → lien
  DELETE /api/suggere            {a, b}           : supprimer une suggestion
  GET    /api/cherche?q=         fiches + pages PDF (biblio et E:)
  GET    /api/ordonnance         liste ; ?nom= → une ordonnance résolue
  POST   /api/ordonnance         créer {titre, chantier, question, corps, depot?}
  PUT    /api/ordonnance         éditer {nom, corps} (état préparée seul)
  POST   /api/ordonnance/etat    {nom, etat: signee|confiee}
  GET    /api/codefile?depot=&chemin=  fichier entier (widget code)
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
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "myVault"
FICHES = VAULT / "Fiches"
UI = ROOT / "tools" / "archipel_ui.html"
ARBRE = ROOT / "tools" / "arbre_3d.html"
sys.path.insert(0, str(ROOT / "tools"))
import graphe  # noqa: E402

PDF_RACINES = [VAULT / "biblio" / "pdf", Path("E:/pdf_library")]
PORT = 8765

DOSSIERS = {"idee": "idees", "note": "notes", "source": "sources",
            "capture": "captures", "projet": None, "chantier": None}


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
    """Toute fiche du vault (Fiches, Projets, Chantiers) — sauf les générées."""
    if titre in GENERES or titre.startswith("00 —"):
        return None
    for racine in (FICHES, VAULT / "Projets", VAULT / "Chantiers"):
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


def creer_fiche(titre: str, type_f: str, corps: str, domaines=None,
                genese: str = "") -> dict:
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
    if genese:
        fm.append(f'genese: "{genese}"')
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
    for racine in (FICHES, VAULT / "Projets", VAULT / "Chantiers"):
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
    for racine in (FICHES, VAULT / "Projets", VAULT / "Chantiers"):
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


# ------------------------------------------------------------- ordonnances

# artefacts dérivés : préparées ici (hors vault), confiées au dépôt
SESSIONS = ROOT / "data" / "sessions"
ETATS = ("preparee", "signee", "confiee")


def parse_blocs(corps: str) -> list[dict]:
    """Blocs fence typés — lisible à l'œil et par un agent de codage :

        ```pdf
        doc: Ali et al. 2017
        page: 14

        la décomposition en blocs hexaèdres…
        ```

    En-tête = lignes `clé: valeur` jusqu'à la première ligne vide ;
    le reste est le corps (citation, commentaire, consigne).
    """
    blocs, cur, attrs_done = [], None, False
    for ligne in corps.split("\n"):
        if cur is None:
            m = re.match(r"^```(\w+)\s*$", ligne)
            if m:
                cur, attrs_done = {"type": m.group(1), "attrs": {}, "corps": []}, False
            continue
        if ligne.strip() == "```":
            cur["corps"] = "\n".join(cur["corps"]).strip()
            blocs.append(cur)
            cur = None
            continue
        if not attrs_done:
            m = re.match(r"^([\w-]+):\s*(.*)$", ligne)
            if m:
                cur["attrs"][m.group(1)] = m.group(2).strip()
                continue
            if not ligne.strip():
                attrs_done = True
                continue
            attrs_done = True  # corps direct, pas d'en-tête
        cur["corps"].append(ligne)
    return blocs


def _attrs_lignes(attrs: dict) -> str:
    return "\n".join(f"{k}: {v}" for k, v in attrs.items())


def pdf_de_source(titre: str) -> Path | None:
    """Le PDF attaché à une fiche source (champ pdf:, nom ou [[wikilink]]."""
    p = fichier_de(titre)
    if p is None:
        return None
    _a, fm, _c = sep_crlf(p.read_text(encoding="utf-8"))
    brut = graphe.champ_simple(fm, "pdf")
    if not brut:
        return None
    # [[wikilink]] → nom nu ; sinon le nom est pris tel quel (certains
    # fichiers commencent par un crochet — strip() les dévorait)
    m = re.match(r"^\[\[(.+)\]\]$", brut.strip())
    nom = m.group(1) if m else brut.strip()
    for racine in PDF_RACINES:
        cand = racine / nom
        if cand.is_file():
            return cand
    for racine in PDF_RACINES:
        if racine.is_dir():
            for f in racine.rglob("*.pdf"):
                if f.name.casefold() == nom.casefold():
                    return f
    return None


def _plages(brut: str) -> list[tuple[int, int]]:
    out = []
    for morceau in re.split(r"[,;\s]+", brut or ""):
        m = re.match(r"^(\d+)-(\d+)$", morceau)
        if m:
            out.append((int(m.group(1)), int(m.group(2))))
        elif m2 := re.match(r"^(\d+)$", morceau):
            n = int(m2.group(1))
            out.append((n, n))
    return out


def _resoudre_bloc(b: dict) -> dict:
    """Résout un bloc vers sa matière : chemin PDF réel, fichier de code
    + plages, ou fiche du vault. Ne jette pas : un bloc insoluble reste
    affichable (ok: false + raison)."""
    t, a = b["type"], b["attrs"]
    if t == "pdf":
        doc = a.get("doc", "")
        p = pdf_de_source(doc)
        if p is None:
            return {**b, "ok": False, "erreur": f"PDF introuvable pour la source « {doc} »"}
        return {**b, "ok": True, "chemin_pdf": str(p),
                "page": int(a.get("page", 1) or 1)}
    if t == "code":
        depot, chemin = a.get("depot", ""), a.get("chemin", "")
        p = code_autorise(f"{depot}/{chemin}") if depot and chemin else None
        if p is None:
            return {**b, "ok": False, "erreur": f"fichier introuvable : {depot}/{chemin}"}
        return {**b, "ok": True, "chemin_code": f"{depot}/{chemin}",
                "plages": _plages(a.get("lignes", ""))}
    if t == "fiche":
        try:
            return {**b, "ok": True, "fiche": lire_fiche(a.get("titre", ""))}
        except FileNotFoundError:
            return {**b, "ok": False, "erreur": f"fiche introuvable : {a.get('titre', '')}"}
    return {**b, "ok": True}  # type inconnu : affiché brut (extensible)


def ordonnances() -> list[dict]:
    SESSIONS.mkdir(exist_ok=True)
    out = []
    for p in sorted(SESSIONS.glob("*.md")):
        _a, fm, _c = sep_crlf(p.read_text(encoding="utf-8"))
        etat = graphe.champ_simple(fm, "etat") or "preparee"
        out.append({"nom": p.stem, "etat": etat if etat in ETATS else "preparee",
                    "chantier": graphe.champ_simple(fm, "chantier") or "",
                    "depot": graphe.champ_simple(fm, "depot") or "",
                    "question": graphe.champ_simple(fm, "question") or ""})
    return out


def lire_ordonnance(nom: str) -> dict:
    p = SESSIONS / f"{nom}.md"
    if not re.match(r"^[\w ,…—'’()\[\]-]+$", nom) or not p.is_file():
        raise FileNotFoundError(nom)
    _a, fm, corps = sep_crlf(p.read_text(encoding="utf-8"))
    etat = graphe.champ_simple(fm, "etat") or "preparee"
    return {"nom": p.stem, "etat": etat,
            "chantier": graphe.champ_simple(fm, "chantier") or "",
            "depot": graphe.champ_simple(fm, "depot") or "",
            "question": graphe.champ_simple(fm, "question") or "",
            "corps": corps.strip(),
            "blocs": [_resoudre_bloc(b) for b in parse_blocs(corps)]}


def creer_ordonnance(titre: str, chantier: str, question: str, corps: str,
                     depot: str = "") -> dict:
    titre = titre.strip()
    if not re.match(r"^[^/\\:*?\"<>|]{3,140}$", titre):
        raise ValueError("titre invalide (3-140 car., sans /\\:*?\"<>|)")
    SESSIONS.mkdir(exist_ok=True)
    p = SESSIONS / f"{date.today():%Y%m%d} — {titre}.md"
    i = 1
    while p.exists():
        i += 1
        p = SESSIONS / f"{date.today():%Y%m%d} — {titre} ({i}).md"
    entete = ["type: ordonnance", "author: agent", "etat: preparee",
              f"created: {date.today().isoformat()}"]
    if chantier:
        entete.append(f'chantier: "{chantier}"')
    if depot:
        entete.append(f'depot: "{depot}"')
    if question:
        entete.append(f'question: "{question}"')
    p.write_text("---\n" + "\n".join(entete) + "\n---\n" + normalise(corps) + "\n",
                 encoding="utf-8")
    return lire_ordonnance(p.stem)


def ecrire_ordonnance(nom: str, corps: str, question: str | None = None) -> dict:
    """Édition : réservée à l'état préparée — la signature fige."""
    o = lire_ordonnance(nom)
    if o["etat"] != "preparee":
        raise ValueError(f"ordonnance {o['etat']} : figée, plus éditable")
    p = SESSIONS / f"{nom}.md"
    _a, fm, _c = sep_crlf(p.read_text(encoding="utf-8"))
    if question is not None:
        fm = set_champ_simple(fm, "question", question)
    p.write_text(f"---\n{fm}\n---\n{normalise(corps)}\n", encoding="utf-8")
    return lire_ordonnance(nom)


def etat_ordonnance(nom: str, etat: str) -> dict:
    o = lire_ordonnance(nom)
    if etat == "signee":
        if o["etat"] != "preparee":
            raise ValueError(f"signature impossible depuis {o['etat']}")
    elif etat == "confiee":
        if o["etat"] != "signee":
            raise ValueError("confier exige une ordonnance signée")
        depot = o["depot"]
        chemins, _ = graphe.depots()
        racine = next((r for t, r in chemins.items()
                       if t.casefold() == depot.casefold() and r), None)
        if racine is None:
            raise ValueError(f"dépôt inconnu : {depot!r}")
        cible = Path(racine) / "sessions"
        cible.mkdir(exist_ok=True)
        (cible / f"{nom}.md").write_text(
            (SESSIONS / f"{nom}.md").read_text(encoding="utf-8"), encoding="utf-8")
    else:
        raise ValueError(f"état inconnu : {etat!r}")
    p = SESSIONS / f"{nom}.md"
    _a, fm, _c = sep_crlf(p.read_text(encoding="utf-8"))
    fm = set_champ_simple(fm, "etat", etat)
    p.write_text(f"---\n{fm}\n---\n{_c}", encoding="utf-8")
    return lire_ordonnance(nom)


# ------------------------------------------------------------- compagnon (LLM)

# config des modèles — data/llm.json, éditable à la main
LLM_DEFAUT = {"url": "http://localhost:11434",
              "synthese": "gemma4:12b", "vision": "qwen3-vl",
              "fond": "qwen3.6:27b"}


def llm_config() -> dict:
    p = ROOT / "data" / "llm.json"
    if p.is_file():
        try:
            return {**LLM_DEFAUT, **json.loads(p.read_text(encoding="utf-8"))}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(LLM_DEFAUT)


# ------------------------------------------------------------- panier

# le panier : une liste de blocs (même format que les ordonnances),
# fichier-backed, traversée par le compagnon et les ordonnances

def panier_lire() -> list[dict]:
    p = ROOT / "data" / "panier.json"
    if not p.is_file():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def panier_ecrire(blocs: list[dict]):
    (ROOT / "data" / "panier.json").write_text(
        json.dumps(blocs, ensure_ascii=False, indent=1), encoding="utf-8")


def panier_resolu() -> list[dict]:
    return [_resoudre_bloc(b) for b in panier_lire()]


def _extraire(b: dict) -> str:
    """La matière d'un bloc, en texte — ce que le compagnon lira."""
    t, a = b["type"], b["attrs"]
    if t == "pdf" and b.get("ok"):
        try:
            import pymupdf
            with pymupdf.open(b["chemin_pdf"]) as doc:
                page = min(max(b.get("page", 1), 1), doc.page_count)
                texte = doc[page - 1].get_text()
            return f"[{t} · {a.get('doc', '')} · page {page}]\n{texte[:4000]}"
        except Exception as e:
            return f"[{t} · {a.get('doc', '')}] (illisible : {e})"
    if t == "code" and b.get("ok"):
        p = code_autorise(b["chemin_code"])
        if p:
            lignes = p.read_text(encoding="utf-8", errors="replace").split("\n")
            morceaux = []
            for deb, fin in (b.get("plages") or [(1, min(len(lignes), 120))]):
                sel = lignes[deb - 1:fin]
                num = "\n".join(f"{deb + i:4d} {l}" for i, l in enumerate(sel))
                morceaux.append(num)
            return f"[{t} · {b['chemin_code']}]\n" + "\n…\n".join(morceaux)[:6000]
    if t == "fiche" and b.get("ok"):
        f = b["fiche"]
        return f"[fiche · {f['titre']}]\n{f['corps'][:3000]}"
    return f"[{t}] {b.get('erreur', '(résolution impossible)')}"


def _panier_vers_markdown(blocs: list[dict]) -> str:
    out = []
    for b in blocs:
        entete = "\n".join(f"{k}: {v}" for k, v in b.get("attrs", {}).items())
        out.append(f"```{b['type']}\n{entete}\n\n{b.get('corps', '')}\n```")
    return "\n\n".join(out)


SYSTEME_COMPAGNON = (
    "Tu es le compagnon de session de l'Archipel, l'environnement de travail "
    "d'un artisan-chercheur. On te donne des passages choisis (pages de PDF, "
    "plages de code, fiches) et une question. Ta production est un BROUILLON "
    "de travail : synthétise, croise, pointe les tensions, propose des pistes. "
    "Tu ne décides rien : l'utilisateur élèvera ce qui mérite de l'être. "
    "Quand une structure aide, produis un diagramme en bloc ```mermaid. "
    "Réponds en français, dense, sans remplissage."
)


def llm_stream(self, tache: str, question: str):
    """SSE : le compagnon travaille sur le panier, en streaming."""
    cfg = llm_config()
    modele = cfg.get(tache) or cfg["synthese"]
    blocs = panier_resolu()
    if not blocs:
        self._json(400, {"erreur": "panier vide"})
        return
    matiere = "\n\n".join(_extraire(b) for b in blocs)
    messages = [
        {"role": "system", "content": SYSTEME_COMPAGNON},
        {"role": "user", "content": f"## Question\n{question}\n\n## Passages du panier\n{matiere}"},
    ]
    body = json.dumps({"model": modele, "messages": messages, "stream": True,
                       "options": {"num_ctx": 16384}}).encode()
    self.send_response(200)
    self.send_header("Content-Type", "text/event-stream; charset=utf-8")
    self.send_header("Cache-Control", "no-cache")
    self.end_headers()
    try:
        req = urllib.request.Request(cfg["url"] + "/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as rep:
            for ligne in rep:
                if not ligne.strip():
                    continue
                d = json.loads(ligne)
                msg = d.get("message", {})
                pensee, morceau = msg.get("thinking", ""), msg.get("content", "")
                if pensee:
                    ev = json.dumps({"t": pensee, "reflechit": True}, ensure_ascii=False)
                    self.wfile.write(f"data: {ev}\n\n".encode("utf-8"))
                    self.wfile.flush()
                if morceau:
                    ev = json.dumps({"t": morceau}, ensure_ascii=False)
                    self.wfile.write(f"data: {ev}\n\n".encode("utf-8"))
                    self.wfile.flush()
                if d.get("done"):
                    break
        self.wfile.write(b"data: [DONE]\n\n")
    except (urllib.error.URLError, OSError) as e:
        self.wfile.write(f"data: {json.dumps({'erreur': f'Ollama injoignable : {e}'}, ensure_ascii=False)}\n\n".encode("utf-8"))


def elever(titre: str, type_f: str, corps: str, domaines=None, genese: str = "") -> dict:
    """Élévation d'un brouillon en fiche : l'utilisateur signe, la lignée
    du compagnon reste tracée (genese:)."""
    f = creer_fiche(titre, type_f, corps, domaines)
    if genese:
        p = fichier_de(f["titre"])
        _a, fm, _c = sep_crlf(p.read_text(encoding="utf-8"))
        fm = set_champ_simple(fm, "genese", genese)
        p.write_text(f"---\n{fm}\n---\n{f['corps']}\n", encoding="utf-8")
    return lire_fiche(f["titre"])


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
        fiches, ar, su, chemins_dep, chant = graphe.construire()
        pos = graphe.positions(fiches, ar, su)
        ecl = graphe.eclairage(chant, fiches)
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
        casq_noms = list(chant)
        etats = {nom: {t: (t in v["eclairees"])
                       for t in fiches if fiches[t]["type"] in graphe.TYPES_DESSINES}
                 for nom, v in ecl.items()}
        return {
            "nodes": nodes, "edges": edges,
            "etats": etats,
            "options": [[n, n] for n in casq_noms] + [["__aucune__", "aucun (carte neutre)"]],
            "default": next((n for n, v in ecl.items() if v["ouvert"]), "__aucune__"),
            "fiches_hors_carte": [t for t in fiches if fiches[t]["type"] not in graphe.TYPES_DESSINES],
        }

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(u.query)
        q1 = lambda k: urllib.parse.unquote(qs.get(k, [""])[0])
        if u.path == "/":
            self._fichier(UI, "text/html; charset=utf-8")
        elif u.path == "/arbre":
            self._fichier(ARBRE, "text/html; charset=utf-8")
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
        elif u.path == "/api/ordonnance":
            if q1("nom"):
                try:
                    self._json(200, lire_ordonnance(q1("nom")))
                except FileNotFoundError:
                    self._json(404, {"erreur": "ordonnance introuvable"})
            else:
                self._json(200, {"ordonnances": ordonnances()})
        elif u.path == "/api/panier":
            self._json(200, {"blocs": panier_resolu()})
        elif u.path == "/api/codefile":
            p = code_autorise(f"{q1('depot')}/{q1('chemin')}")
            if p is None:
                self._json(404, {"erreur": "fichier introuvable"})
            else:
                self._json(200, {"texte": p.read_text(encoding="utf-8", errors="replace")})
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
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._json(400, {"erreur": "corps de requête illisible (UTF-8 attendu)"})
            return
        if u == "/api/llm":
            # le flux SSE gère ses propres en-têtes — hors du try JSON
            llm_stream(self, d.get("tache", "synthese"), d.get("question", ""))
            return
        try:
            if u == "/api/fiche":
                self._json(200, creer_fiche(d["titre"], d.get("type", "note"),
                                            d.get("corps", ""), d.get("domaines"),
                                            d.get("genese", "")))
            elif u == "/api/lien":
                lien_modifier(d["a"], d["b"], "lie", True)
                self._json(200, {"ok": True})
            elif u == "/api/suggere/valide":
                lien_modifier(d["a"], d["b"], "suggere", False)
                lien_modifier(d["a"], d["b"], "lie", True)
                self._json(200, {"ok": True})
            elif u == "/api/ordonnance":
                self._json(200, creer_ordonnance(d["titre"], d.get("chantier", ""),
                                                 d.get("question", ""), d.get("corps", ""),
                                                 d.get("depot", "")))
            elif u == "/api/panier":
                blocs = panier_lire()
                blocs.append({"type": d["type"], "attrs": d.get("attrs", {}),
                              "corps": d.get("corps", "")})
                panier_ecrire(blocs)
                self._json(200, {"ok": True, "n": len(blocs)})
            elif u == "/api/panier/vider":
                panier_ecrire([])
                self._json(200, {"ok": True})
            elif u == "/api/panier/ordonnance":
                if not panier_lire():
                    raise ValueError("panier vide")
                corps = _panier_vers_markdown(panier_resolu())
                o = creer_ordonnance(d["titre"], d.get("chantier", ""),
                                     d.get("question", ""), corps, d.get("depot", ""))
                panier_ecrire([])
                self._json(200, o)
            elif u == "/api/elever":
                self._json(200, elever(d["titre"], d.get("type", "note"),
                                       d.get("corps", ""), d.get("domaines"),
                                       d.get("genese", "")))
            elif u == "/api/ordonnance/etat":
                self._json(200, etat_ordonnance(d["nom"], d["etat"]))
            else:
                self.send_error(404)
        except FileNotFoundError as e:
            self._json(404, {"erreur": f"fiche introuvable : {e}"})
        except FileExistsError as e:
            self._json(409, {"erreur": f"titre déjà pris : {e}"})
        except (ValueError, KeyError) as e:
            self._json(400, {"erreur": str(e)})

    def do_PUT(self):
        path = urllib.parse.urlparse(self.path).path
        if path not in ("/api/fiche", "/api/ordonnance"):
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", "0"))
        try:
            d = json.loads(self.rfile.read(n).decode("utf-8"))
            if path == "/api/fiche":
                res = ecrire_fiche(d["titre"], d.get("corps"),
                                   d.get("nouveau_titre"), d.get("domaines"), d.get("type"))
            else:
                res = ecrire_ordonnance(d["nom"], d.get("corps", ""), d.get("question"))
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
            elif u == "/api/panier":
                if q1("tout"):
                    panier_ecrire([])
                else:
                    blocs = panier_lire()
                    i = int(q1("i", "-1")) if q1("i").lstrip("-").isdigit() else -1
                    if 0 <= i < len(blocs):
                        blocs.pop(i)
                        panier_ecrire(blocs)
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
