"""Archipel des idées — v0.5 : une casquette active, qui éclaire.

- **Casquette active** : une seule à la fois (`active: true` dans le
  frontmatter de `myVault/Casquettes/*.md`). Ses idées sont éclairées :
  partage au moins un domaine avec elle, ou vient de sa lignée documentaire.
  Les autres idées restent visibles, atténuées.
- **Liens éclairés** : les courants (domaines partagés) entre idées
  éclairées, et les couvées qui touchent une idée éclairée.
  Les autres liens sont à peine tracés.
- **Îlots-idées** : positionnés par leurs courants de domaines partagés ;
  colorés par climat (premier domaine) ; diamètre = outillage disponible
  dans les dépôts.
- **Satellites** : couvées validées (diamants, contour or).
- Sans casquette active : carte neutre, toutes les idées au même régime.

Usage :
    .venv/Scripts/python tools/galaxie.py                    # carte avec la casquette active
    .venv/Scripts/python tools/galaxie.py --casquette "Menuisier"   # change l'active
    .venv/Scripts/python tools/galaxie.py --aucune          # carte neutre
"""
import argparse
import json
import re
import sqlite3
import sys
import textwrap
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "myVault"
IDEES = VAULT / "Fiches"
NOTES = IDEES / "notes"
CASQ = VAULT / "Casquettes"
OUT_PNG = VAULT / "biblio" / "img" / "galaxie-idees.png"
OUT_NOTE = IDEES / "Galaxie.md"
OUT_HTML = VAULT / "Archipel.html"

STOPWORDS = set("""
le la les un une des de du au aux et ou en dans sur pour par avec sans sous
ce cet cette ces son sa ses leur leurs qui que quoi dont où est sont était
être avoir a ont plus moins très tout toute tous toutes même comme donc
ainsi alors mais car si ne pas chaque avant après entre vers chez hors dès
lors tant déjà encore toujours jamais peut peuvent doit doivent fait faire
cas type types partie point exemple etc cf see the of and in to for with
""".split())

MER = "#0d1b2a"
DIM = "#2b3a4b"
DIM_TXT = "#4a5a6b"
LIT_LINK = "#e8a13c"
NEUTRE = "#8fa3b8"
LIEN_LIT = "#8fa3b8"
SCORE_SEUIL = 1  # remonter à 2 quand la carte regrossit (au-delà de ~15 fiches)


def tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zà-ÿ0-9]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS and not w.isdigit()}


def frontmatter(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    return m.group(1) if m else ""


def domaines_de(block: str) -> list[str]:
    md = re.search(r"domaines:\s*\[(.*?)\]", block)
    return [d.strip() for d in md.group(1).split(",") if d.strip()] if md else []


def parse_idea(path: Path):
    text = path.read_text(encoding="utf-8")
    block = frontmatter(text)
    doms = domaines_de(block)
    croise, source = [], None
    for line in block.splitlines():
        if line.strip().startswith("croise:"):
            croise = re.findall(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]", line)
        if line.strip().startswith("source:"):
            ms = re.search(r"SB-(\d+)", line)
            if ms:
                source = int(ms.group(1))
    body = re.sub(r"^---\n.*?\n---", "", text, count=1, flags=re.DOTALL)
    return doms, croise, source, f"{path.stem} {body}"


def load_casquettes():
    """{titre_db: {'doms': [...], 'active': bool, 'path': Path, 'id': int}}"""
    conn = sqlite3.connect(ROOT / "data" / "secondbrain.db")
    conn.row_factory = sqlite3.Row
    titres = {r["id"]: r["title"] for r in
              conn.execute("SELECT id, title FROM projects WHERE kind='casquette'")}
    conn.close()
    casq = {}
    for p in sorted(CASQ.glob("*.md")):
        block = frontmatter(p.read_text(encoding="utf-8"))
        mid = re.search(r"^id:\s*(\d+)", block, re.MULTILINE)
        if not mid or int(mid.group(1)) not in titres:
            continue
        titre = titres[int(mid.group(1))]
        casq[titre] = {
            "id": int(mid.group(1)),
            "doms": domaines_de(block),
            "active": re.search(r"^active:\s*true\s*$", block, re.MULTILINE) is not None,
            "path": p,
        }
    return casq


def set_active(casq: dict, nom: str | None):
    """Une seule casquette porte `active: true` ; nom=None désactive tout."""
    if nom is not None and nom not in casq:
        sys.exit(f"casquette inconnue : {nom!r} — choix : {', '.join(casq)}")
    for titre, c in casq.items():
        text = c["path"].read_text(encoding="utf-8")
        m = re.match(r"^(---\n)(.*?)(\n---)", text, re.DOTALL)
        if not m:
            continue
        lines = [l for l in m.group(2).splitlines() if not l.startswith("active:")]
        if titre == nom:
            lines.append("active: true")
        new = m.group(1) + "\n".join(lines) + m.group(3) + text[m.end():]
        if new != text:
            c["path"].write_text(new, encoding="utf-8")
        c["active"] = titre == nom


def load_depots():
    conn = sqlite3.connect(ROOT / "data" / "secondbrain.db")
    conn.row_factory = sqlite3.Row
    depots = {r["title"]: tokens(r["code_scan_text"] or "")
              for r in conn.execute("SELECT title, code_scan_text FROM projects WHERE kind='projet'")}
    lignee = {}
    for r in conn.execute("SELECT vault_note, linked_project_id FROM items"):
        if not r["vault_note"] or not r["linked_project_id"]:
            continue
        m = re.match(r"SB-(\d+)", Path(r["vault_note"]).name)
        pt = conn.execute("SELECT title, kind FROM projects WHERE id = ?",
                          (r["linked_project_id"],)).fetchone()
        if m and pt and pt["kind"] == "casquette":
            lignee.setdefault(int(m.group(1)), set()).add(pt["title"])
    conn.close()
    return depots, lignee


def wrap(label, width=20):
    return "\n".join(textwrap.wrap(label, width=width))


def build(active: str | None):
    casq = load_casquettes()
    depots, lignee = load_depots()
    doms_active = set(casq[active]["doms"]) if active else set()

    ideas, crosses = {}, []
    for kind_dir in ("idees", "notes"):
        for p in sorted((IDEES / kind_dir).glob("*.md")):
            doms, croise, source, body = parse_idea(p)
            if not doms:
                continue
            ideas[p.stem] = {"doms": doms, "croise": croise, "source": source,
                             "tokens": tokens(body), "satellite": False}
            if croise:
                crosses.append((p.stem, croise))

    # diamètre = outillage disponible ; lignée = casquette documentaire
    for t, d in ideas.items():
        best, n_match = 0.0, 0
        for tk in depots.values():
            common = d["tokens"] & tk
            if common and d["tokens"]:
                score = min(len(common) / (len(d["tokens"]) ** 0.5
                                           * max(len(tk), 1) ** 0.25), 1.0)
                best = max(best, score)
                if score >= 0.15:
                    n_match += 1
        d["tool_score"] = best
        d["diameter"] = 140 + 520 * best + 90 * n_match
        d["lignee"] = lignee.get(d["source"] or -1, set())

    # éclairage : score = domaines partagés avec la casquette active (+3 si lignée)
    for t, d in ideas.items():
        if active is None:
            d["score"], d["eclairee"] = None, True
            continue
        shared = len(set(d["doms"]) & doms_active)
        bonus = 3 if active in d["lignee"] else 0
        d["score"] = shared + bonus
        d["eclairee"] = d["score"] >= SCORE_SEUIL

    # graphe : courants (domaines partagés) + couvées ; sert au layout
    G = nx.Graph()
    G.add_nodes_from(ideas)
    for a in ideas:
        for b in ideas:
            if a < b:
                shared = set(ideas[a]["doms"]) & set(ideas[b]["doms"])
                if shared:
                    G.add_edge(a, b, kind="courant", weight=1.0 * len(shared))
    for sec, bases in crosses:
        for b in bases:
            if b in ideas:
                G.add_edge(sec, b, kind="couvee", weight=3.0)

    pos = nx.spring_layout(G, k=1.1, iterations=400, weight="weight", seed=42)
    return casq, ideas, crosses, G, pos


def climats_couleurs(ideas):
    climats = sorted({d["doms"][0] for d in ideas.values()})
    cmap = plt.get_cmap("tab20")
    return climats, {c: cmap(i % 20 / 20) for i, c in enumerate(climats)}


def dessiner_png(casq, ideas, crosses, G, pos, active):
    climats, climate_color = climats_couleurs(ideas)
    neutre = active is None
    n_lit = sum(1 for d in ideas.values() if d["eclairee"])

    fig, ax = plt.subplots(figsize=(25, 16.5), facecolor=MER)
    ax.set_facecolor(MER)

    def lit(n):
        return neutre or ideas[n]["eclairee"]

    # liens : couvées (toujours, atténuées hors éclairage) + courants éclairés
    for u, v, dd in G.edges(data=True):
        if dd["kind"] == "couvee":
            on = lit(u) or lit(v)
            ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                    color=LIT_LINK if on else DIM, alpha=1.0 if on else 0.35,
                    lw=2.2 if on else 0.8, zorder=2)
        elif not neutre and lit(u) and lit(v):
            ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                    color=LIEN_LIT, alpha=0.30, lw=0.9, zorder=1)

    names_lit = [n for n in ideas if lit(n) and not ideas[n]["satellite"]]
    names_mer = [n for n in ideas if not lit(n) and not ideas[n]["satellite"]]
    sat = [n for n in ideas if ideas[n]["satellite"]]

    def draw(nodes, marker, edge, alpha, size_factor=1.0, color_of=None):
        if not nodes:
            return
        nx.draw_networkx_nodes(
            G, pos, nodelist=nodes, node_shape=marker,
            node_color=[color_of(n) for n in nodes],
            node_size=[ideas[n]["diameter"] * size_factor for n in nodes],
            edgecolors=edge, linewidths=1.2 if marker == "D" else 0.6,
            alpha=alpha, ax=ax)

    draw(names_mer, "o", MER, 0.45, 0.55, lambda n: DIM)
    draw(names_lit, "o", MER, 1.0, 1.0, lambda n: climate_color[ideas[n]["doms"][0]])
    draw(sat, "D", LIT_LINK if not neutre else LIT_LINK, 1.0, 1.0,
         lambda n: climate_color[ideas[n]["doms"][0]] if lit(n) else DIM)

    for n, (x, y) in pos.items():
        d = ideas[n]
        if lit(n):
            ax.text(x, y - 0.045, wrap(n, 20), ha="center", va="top", fontsize=7,
                    color=climate_color[d["doms"][0]],
                    bbox=dict(facecolor=MER, alpha=0.6, edgecolor="none", pad=0.7))
        else:
            ax.text(x, y - 0.035, wrap(n, 20), ha="center", va="top", fontsize=5.2,
                    color=DIM_TXT,
                    bbox=dict(facecolor=MER, alpha=0.3, edgecolor="none", pad=0))

    titre_actif = f"casquette active : {active}" if active else "carte neutre"
    ax.set_title(
        f"Archipel des idées — {titre_actif} · {n_lit} idées éclairées / {len(ideas)} · "
        f"{len(climats)} climats · {len(crosses)} couvée(s)",
        color="#dce8f5", fontsize=16, pad=18,
    )
    handles = [
        Line2D([], [], marker="o", linestyle="", markersize=8,
               markerfacecolor=NEUTRE, color=MER, label="idée éclairée (couleur = climat)"),
        Line2D([], [], marker="o", linestyle="", markersize=6,
               markerfacecolor=DIM, color=MER, label="idée hors éclairage"),
        Line2D([], [], marker="D", linestyle="", markersize=7,
               markerfacecolor=NEUTRE, markeredgecolor=LIT_LINK, color=MER, label="satellite (couvée validée)"),
        Line2D([], [], color=LIEN_LIT, lw=1.2, alpha=0.6, label="courant entre idées éclairées"),
        Line2D([], [], color=LIT_LINK, lw=2, label="couvée"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7.2, ncol=3,
              facecolor=MER, edgecolor="#22303f", labelcolor="#dce8f5")
    ax.axis("off")
    fig.tight_layout()
    OUT_PNG.parent.mkdir(exist_ok=True)
    fig.savefig(OUT_PNG, dpi=110, facecolor=fig.get_facecolor())
    print(f"rendu -> {OUT_PNG}")


def ecrire_note(casq, ideas, crosses, active):
    climats, _ = climats_couleurs(ideas)
    lit = [t for t, d in ideas.items() if d["eclairee"]] if active else []
    lines = []
    if active:
        lines += [f"**Casquette active** : {active}", "",
                  "## Idées éclairées", ""]
        for t in sorted(lit, key=lambda t: -(ideas[t]["score"] or 0)):
            lines.append(f"- [[{t}]] (score {ideas[t]['score']})")
    else:
        lines.append("Aucune casquette active : carte neutre.")
    lines += ["", "## Diamètres remarquables (boîte à outils des dépôts)", ""]
    for t, d in sorted(ideas.items(), key=lambda kv: -kv[1]["tool_score"])[:10]:
        lines.append(f"- score {d['tool_score']:.2f} — [[{t}]] (climat : {d['doms'][0]})")
    note = (
        "---\n"
        "généré: par tools/galaxie.py\n"
        "---\n\n"
        "# Archipel des idées\n\n"
        f"![[{OUT_PNG.name}]]\n\n"
        "Une seule **casquette active** éclaire la carte : ses idées sont\n"
        "lisibles, leurs liens (courants et couvées) sont tracés. Les autres\n"
        "idées restent visibles, atténuées. Changer d'éclairage :\n"
        "`python tools/galaxie.py --casquette \"Nom\"`.\n\n"
        "Climats : " + ", ".join(climats) + "\n\n"
        + "\n".join(lines) + "\n"
    )
    OUT_NOTE.write_text(note, encoding="utf-8")
    print(f"note -> {OUT_NOTE}")


def eclairage_par_casquette(casq, ideas):
    """{nom_casquette | '__aucune__': {idee: bool éclairée}} — pour chaque état."""
    etats = {}
    for nom in list(casq) + [None]:
        doms = set(casq[nom]["doms"]) if nom else set()
        for t, d in ideas.items():
            if nom is None:
                lit = True
            else:
                shared = len(set(d["doms"]) & doms)
                bonus = 3 if nom in d["lignee"] else 0
                lit = shared + bonus >= SCORE_SEUIL
            etats.setdefault(nom or "__aucune__", {})[t] = lit
    return etats


GABARIT_UI = Path(__file__).resolve().parent / "archipel_ui.html"


def disposition_html(G, largeur=1500, hauteur=950):
    """Positions en pixels pour la page : layout plus écarté, étalé sur l'écran."""
    p = nx.spring_layout(G, k=2.0, iterations=800, weight="weight", seed=42)
    xs = [v[0] for v in p.values()]
    ys = [v[1] for v in p.values()]
    mx = max(max(abs(x) for x in xs), 1e-9)
    my = max(max(abs(y) for y in ys), 1e-9)
    return {n: (v[0] / mx * largeur, v[1] / my * hauteur) for n, v in p.items()}


def dessiner_html(casq, ideas, crosses, G, pos, active):
    """Archipel HTML autonome : une page, un sélecteur de casquette, positions figées."""
    _, climate_color = climats_couleurs(ideas)
    etats = eclairage_par_casquette(casq, ideas)
    pos_px = disposition_html(G)

    def hex_(c):
        return "#%02x%02x%02x" % tuple(int(x * 255) for x in c[:3])

    nodes = []
    for n, d in ideas.items():
        x, y = pos_px[n]
        col = hex_(climate_color[d["doms"][0]])
        nodes.append({
            "id": f"idee:{n}",
            "label": wrap(n, 26).replace("\n", " "),
            "shape": "diamond" if d["satellite"] else "dot",
            "x": x, "y": -y,  # vis : y vers le bas
            "size": 4 + d["diameter"] / 55,
            "_size": 4 + d["diameter"] / 55,
            "_size_off": 3 + d["diameter"] / 110,
            "_fond": col,
            "_bord": LIT_LINK if d["satellite"] else MER,
            "title": f"{n}<br>climat : {d['doms'][0]} · outils : {d['tool_score']:.2f}"
                     f"<br>domaines : {', '.join(d['doms'])}",
            "font": {"color": "#dce8f5", "size": 28},
        })
    edges = []
    for i, (u, v, dd) in enumerate(G.edges(data=True)):
        edges.append({"id": f"e{i}", "from": f"idee:{u}", "to": f"idee:{v}",
                      "_u": u, "_v": v, "_kind": dd["kind"],
                      "arrows": "", "smooth": False})

    casq_noms = list(casq)
    options = [[nom, nom] for nom in casq_noms] + [["__aucune__", "aucune (carte neutre)"]]
    default = next((nom for nom in casq_noms if casq[nom]["active"]), "__aucune__")
    data = {"nodes": nodes, "edges": edges, "etats": etats,
            "options": options, "default": default}
    payload = json.dumps(data, ensure_ascii=False)
    OUT_HTML.write_text(GABARIT_UI.read_text(encoding="utf-8").replace("__DATA__", payload),
                        encoding="utf-8")
    print(f"interactif -> {OUT_HTML}")


def main():
    ap = argparse.ArgumentParser(description="Archipel des idées — une casquette active")
    ap.add_argument("--casquette", help="définit la casquette active (une seule)")
    ap.add_argument("--aucune", action="store_true", help="aucune casquette active : carte neutre")
    a = ap.parse_args()

    casq = load_casquettes()
    if a.aucune:
        set_active(casq, None)
    elif a.casquette:
        set_active(casq, a.casquette)
    # ré-lecture après éventuelle écriture
    casq = load_casquettes()
    active = next((t for t, c in casq.items() if c["active"]), None)

    casq, ideas, crosses, G, pos = build(active)
    n_lit = sum(1 for d in ideas.values() if d["eclairee"])
    print(f"casquette active : {active or 'aucune'} — {n_lit} idée(s) éclairée(s) / {len(ideas)}")
    dessiner_png(casq, ideas, crosses, G, pos, active)
    ecrire_note(casq, ideas, crosses, active)
    dessiner_html(casq, ideas, crosses, G, pos, active)


if __name__ == "__main__":
    main()
