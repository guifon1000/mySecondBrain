"""Le graphe de l'archipel — une seule implémentation, deux sorties.

- tools/galaxie.py l'importe pour le PNG (matplotlib).
- tools/archipel_serve.py l'importe pour la page interactive (/api/graphe).

Le graphe :
- nœuds = fiches des types idee / note / source / capture (les projets et
  casquettes sont des fiches aussi, mais ils ne se dessinent pas : ils
  vivent dans les panneaux et les liens)
- arêtes : `lie` (confirmées, weight 3), `suggere` (propositions, weight 1.2),
  courants (domaines partagés, layout uniquement, weight 1)
- positions : spring layout à seed fixe — reproductible, stable d'un appel
  à l'autre tant que la topologie ne change pas
- états de casquette : {nom: {titre_fiche: bool éclairée}} — le score est
  le nombre de domaines partagés avec la casquette active (+3 si la fiche
  est reliée au projet desservant la casquette)
"""
import re
import sqlite3
import sys
import textwrap
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "myVault"
FICHES = VAULT / "Fiches"

STOPWORDS = set("""
le la les un une des de du au aux et ou en dans sur pour par avec sans sous
ce cet cette ces son sa ses leur leurs qui que quoi dont où est sont était
être avoir a ont plus moins très tout toute tous toutes même comme donc
ainsi alors mais car si ne pas chaque avant après entre vers chez hors dès
lors tant déjà encore toujours jamais peut peuvent doit doivent fait faire
cas type types partie point exemple etc cf see the of and in to for with
""".split())

SCORE_SEUIL = 1  # remonter à 2 quand la carte repasse ~15 fiches

TYPES_DESSINES = {"idee", "note", "source", "capture"}


def tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zà-ÿ0-9]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS and not w.isdigit()}


def frontmatter(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    return m.group(1) if m else ""


def champ(block: str, nom: str) -> list[str]:
    # valeurs d'un champ liste du frontmatter : lie: ["[[a]]", "[[b]]"]
    vals = []
    m = re.search(rf"^{nom}:\s*\[(.*?)\]\s*$", block, re.MULTILINE)
    if m:
        vals = re.findall(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]", m.group(1))
    if not vals:
        m = re.search(rf"^{nom}:\s*\"?\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]\"?", block, re.MULTILINE)
        if m:
            vals = [m.group(1)]
    return vals


def champ_simple(block: str, nom: str) -> str:
    m = re.search(rf"^{nom}:\s*(.+)$", block, re.MULTILINE)
    if not m:
        return ""
    v = m.group(1).strip().strip('"')
    # un wikilink [[x]] vaut x ; la fiche est un champ de données, pas du corps
    vm = re.match(r"^\[\[(.+?)\]\]$", v)
    return vm.group(1) if vm else v


def domaines_de(block: str) -> list[str]:
    md = re.search(r"domaines:\s*\[(.*?)\]", block)
    return [d.strip() for d in md.group(1).split(",") if d.strip()] if md else []


def lire_fiche(path: Path) -> dict:
    t = path.read_text(encoding="utf-8")
    block = frontmatter(t)
    corps = re.sub(r"^---\n.*?\n---\n?", "", t, count=1, flags=re.DOTALL)
    type_f = champ_simple(block, "type")
    if path.parent.name == "idees":
        type_f = type_f or "idee"
    return {
        "titre": path.stem,
        "type": type_f or "note",
        "domaines": domaines_de(block),
        "lie": champ(block, "lie"),
        "suggere": champ(block, "suggere"),
        "pdf": champ_simple(block, "pdf"),
        "ouvrage": champ_simple(block, "ouvrage"),
        "code": champ_simple(block, "code"),
        "source": champ_simple(block, "source"),
        "incarnation": champ_simple(block, "incarnation"),
        "corps": corps.strip(),
        "texte": f"{path.stem} {corps}",
    }


def depots():
    # {nom_dépôt: chemin} + {nom_dépôt: tokens du scan} (index dérivé)
    db = ROOT / "data" / "secondbrain.db"
    if not db.exists():
        return {}, {}
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    chemins = {r["title"]: (r["code_path"] or "") for r in conn.execute(
        "SELECT title, code_path FROM projects WHERE kind='projet'")}
    scans = {r["title"]: tokens(r["code_scan_text"] or "") for r in conn.execute(
        "SELECT title, code_scan_text FROM projects WHERE kind='projet'")}
    conn.close()
    return chemins, scans


def chantiers():
    # {titre: {ouvert, projet, lie, path}} — lus dans myVault/Chantiers/
    # (le chantier remplace la casquette : contexte de travail concret,
    # un seul ouvert à la fois)
    out = {}
    d = VAULT / "Chantiers"
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.md")):
        block = frontmatter(p.read_text(encoding="utf-8"))
        out[p.stem] = {
            "ouvert": re.search(r"^ouvert:\s*true", block, re.MULTILINE) is not None,
            "projet": champ_simple(block, "projet") or "",
            "lie": champ(block, "lie") or [],
            "path": p,
        }
    return out


def construire():
    """(fiches, arêtes lie, arêtes suggere, chemins dépôts, chantiers)"""
    fiches = {}
    for p in sorted(FICHES.rglob("*.md")):
        if p.name.startswith("00 —") or p.name == "Galaxie.md":
            continue
        f = lire_fiche(p)
        f["chemin"] = str(p.relative_to(VAULT))
        fiches[f["titre"]] = f

    # projets et chantiers : fiches aussi (lisibles, non dessinées)
    for dossier, type_f in (("Projets", "projet"), ("Chantiers", "chantier")):
        for p in sorted((VAULT / dossier).glob("*.md")):
            f = lire_fiche(p)
            f["type"] = type_f
            f["chemin"] = str(p.relative_to(VAULT))
            if type_f == "projet":
                f["lie"] = champ(frontmatter(p.read_text(encoding="utf-8")), "sert") or f["lie"]
            fiches[f["titre"]] = f

    chemins_dep, scans = depots()
    chant = chantiers()
    # résolution insensible à la casse (les wikilinks visent parfois Rincewind, parfois rincewind)
    par_casse = {t.casefold(): t for t in fiches}

    def resoudre(nom):
        return par_casse.get(nom.casefold())

    ar_edges, su_edges = [], []
    for t, f in fiches.items():
        for b in f["lie"]:
            b = resoudre(b)
            if b and b != t:
                ar_edges.append((t, b))
        for b in f["suggere"]:
            b = resoudre(b)
            if b and b != t:
                su_edges.append((t, b))

    # diamètre = outillage des dépôts
    for t, f in fiches.items():
        best, n_match = 0.0, 0
        tkset = tokens(f["texte"])
        for tk in scans.values():
            common = tkset & tk
            if common and tkset:
                score = min(len(common) / (len(tkset) ** 0.5 * max(len(tk), 1) ** 0.25), 1.0)
                best = max(best, score)
                if score >= 0.15:
                    n_match += 1
        f["outils"] = best
        f["diametre"] = 140 + 520 * best + 90 * n_match
    return fiches, ar_edges, su_edges, chemins_dep, chant


def eclairage(chant: dict, fiches: dict) -> dict:
    # éclairage exact : le chantier ouvert éclaire les fiches qu'il touche
    # (liens directs), plus celles reliées à son projet. Plus de score.
    par_casse = {t.casefold(): t for t in fiches}
    out = {}
    for nom, c in chant.items():
        e = set()
        cibles = list(c["lie"]) + ([c["projet"]] if c["projet"] else [])
        for cible in cibles:
            t = par_casse.get(cible.casefold())
            if t:
                e.add(t)
        out[nom] = {"eclairees": e, "ouvert": c["ouvert"]}
    out["__aucune__"] = {"eclairees": set(fiches), "ouvert": False}
    return out


def positions(fiches, ar_edges, su_edges, largeur=1500, hauteur=950):
    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(fiches)
    for a, b in ar_edges:
        G.add_edge(a, b, weight=3.0)
    for a, b in su_edges:
        G.add_edge(a, b, weight=1.2)
    # courants : fiches de même domaine se rapprochent (le layout sans eux
    # dégénère en boule, les fiches étant peu reliées)
    for a in fiches:
        for b in fiches:
            if a < b:
                shared = set(fiches[a]["domaines"]) & set(fiches[b]["domaines"])
                if shared:
                    G.add_edge(a, b, weight=1.0 * len(shared))
    for a in fiches:
        for b in fiches:
            if a < b:
                shared = set(fiches[a]["domaines"]) & set(fiches[b]["domaines"])
                if shared:
                    G.add_edge(a, b, weight=1.0 * len(shared))
    p = nx.spring_layout(G, k=2.0, iterations=800, weight="weight", seed=42)
    xs = [v[0] for v in p.values()] or [0.5]
    ys = [v[1] for v in p.values()] or [0.5]
    mx = max(max(abs(x) for x in xs), 1e-9)
    my = max(max(abs(y) for y in ys), 1e-9)
    return {n: (v[0] / mx * largeur, -v[1] / my * hauteur) for n, v in p.items()}


def wrap(label, width=24):
    return textwrap.fill(label, width=width)
