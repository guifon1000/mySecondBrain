"""Archipel des idées — v0.4 : phares, îlots et climats.

- **Casquettes = phares** : ancrés en périphérie, points d'attraction des
  idées (faisceaux = lignée documentaire). Nommés.
- **Îlots-idées** : positionnés par les courants de domaines partagés +
  l'attraction de leur phare ; colorés par leur grande catégorie (climat) ;
  leur **diamètre** = la boîte à outils disponible dans les dépôts (adéquation
  lexicale avec les scans) — les projets eux-mêmes sont invisibles, ils
  pèsent sans paraître.
- **Satellites** : les croisements de couvée validés (diamants, contour or).

Usage : .venv/Scripts/python tools/galaxie.py
"""
import math
import random
import re
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
IDEES = VAULT / "Idees"
OUT_PNG = VAULT / "biblio" / "img" / "galaxie-idees.png"
OUT_NOTE = IDEES / "Galaxie.md"

IDEA, BEACON = "idee", "phare"

STOPWORDS = set("""
le la les un une des de du au aux et ou en dans sur pour par avec sans sous
ce cet cette ces son sa ses leur leurs qui que quoi dont où est sont était
être avoir a ont plus moins très tout toute tous toutes même comme donc
ainsi alors mais car si ne pas chaque avant après entre vers chez hors dès
lors tant déjà encore toujours jamais peut peuvent doit doivent fait faire
cas type types partie point exemple etc cf see the of and in to for with
""".split())

MER = "#0d1b2a"
PLEINE_MER = "#5f6b7a"


def tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zà-ÿ0-9]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS and not w.isdigit()}


def parse_note(path: Path):
    text = path.read_text(encoding="utf-8")
    doms, croise, source = [], [], None
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if m:
        block = m.group(1)
        md = re.search(r"domaines:\s*\[(.*?)\]", block)
        if md:
            doms = [d.strip() for d in md.group(1).split(",") if d.strip()]
        for line in block.splitlines():
            if line.strip().startswith("croise:"):
                croise = re.findall(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]", line)
            if line.strip().startswith("source:"):
                ms = re.search(r"SB-(\d+)", line)
                if ms:
                    source = int(ms.group(1))
    body = re.sub(r"^---\n.*?\n---", "", text, count=1, flags=re.DOTALL)
    return doms, croise, source, f"{path.stem} {body}"


def wrap(label, width=20):
    return "\n".join(textwrap.wrap(label, width=width))


def load_codebase():
    import sqlite3

    conn = sqlite3.connect(ROOT / "data" / "secondbrain.db")
    conn.row_factory = sqlite3.Row
    # dépôts : la boîte à outils (invisibles sur la carte, présents dans le diamètre)
    depots = {}
    for r in conn.execute("SELECT title, code_scan_text FROM projects WHERE kind='projet'"):
        depots[r["title"]] = tokens(r["code_scan_text"] or "")
    # phares : les casquettes, avec leurs domaines (le pouvoir d'attraction)
    beacons = {}
    lineage = {}
    for r in conn.execute("SELECT id, title FROM projects WHERE kind='casquette'"):
        beacons[r["title"]] = {"id": r["id"], "tokens": set(), "doms": []}
    for p in (VAULT / "Casquettes").glob("*.md"):
        text = p.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        md = re.search(r"domaines:\s*\[(.*?)\]", m.group(1)) if m else None
        doms = [d.strip() for d in md.group(1).split(",")] if md else []
        # relier le fichier à la casquette via son frontmatter id
        mid = re.search(r"^id:\s*(\d+)", m.group(1), re.MULTILINE) if m else None
        if mid:
            for r in conn.execute("SELECT title FROM projects WHERE id = ?", (mid.group(1),)):
                if r["title"] in beacons:
                    beacons[r["title"]]["doms"] = [d.strip() for d in doms]
    for r in conn.execute("SELECT vault_note, linked_project_id FROM items"):
        if not r["vault_note"] or not r["linked_project_id"]:
            continue
        m = re.match(r"SB-(\d+)", Path(r["vault_note"]).name)
        pt = conn.execute("SELECT title, kind FROM projects WHERE id = ?",
                          (r["linked_project_id"],)).fetchone()
        if m and pt and pt["kind"] == "casquette":
            lineage.setdefault(int(m.group(1)), set()).add(pt["title"])
    conn.close()
    return depots, beacons, lineage


def main():
    random.seed(42)
    depots, beacons, lineage = load_codebase()

    ideas, crosses = {}, []
    sub_by_kind = {"atomiques": IDEA, "satellites": IDEA}
    for kind_dir in ("atomiques", "satellites"):
        for p in sorted((IDEES / kind_dir).glob("*.md")):
            doms, croise, source, body = parse_note(p)
            if not doms:
                continue
            ideas[p.stem] = {"doms": doms, "croise": croise, "source": source,
                             "tokens": tokens(body), "satellite": kind_dir == "satellites"}
            if croise:
                crosses.append((p.stem, croise))

    # --- diamètre (outils des dépôts) + phare d'attache (lignée) ------------
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
        d["diameter"] = 140 + 520 * best + 90 * n_match
        d["tool_score"] = best
        d["beacon"] = next((c for c in lineage.get(d["source"] or -1, set())
                            if c in beacons), None)

    # --- relève (phase 1) : chaque îlot-idée se rattache à un phare ----------
    # score = domaines partagés avec la casquette ; bonus fort si lignée.
    for t, d in ideas.items():
        best_b, best_s = None, 0
        for b, bd in beacons.items():
            shared = len(set(d["doms"]) & set(bd["doms"]))
            s = shared + (3.0 if d["beacon"] == b else 0.0)
            if s > best_s:
                best_b, best_s = b, s
        d["relève"] = best_b if best_b and best_s >= 1 else None
        d["relevé_score"] = best_s

    # --- graphe : idées + phares --------------------------------------------
    G = nx.Graph()
    for b in beacons:
        G.add_node((BEACON, b))
    for title, d in ideas.items():
        G.add_node((IDEA, title))
        # attraction du phare : relève (domaines) + lignée
        if d["relève"]:
            G.add_edge((IDEA, title), (BEACON, d["relève"]),
                       weight=1.5 + d["relevé_score"])
    # courants (layout uniquement) : les idées partageant un domaine se rapprochent
    for a, b in ((i, j) for i in ideas for j in ideas if i < j):
        shared = set(ideas[a]["doms"]) & set(ideas[b]["doms"])
        if shared:
            G.add_edge((IDEA, a), (IDEA, b), weight=1.2 * len(shared))
    for sec, bases in crosses:
        for b in bases:
            if b in ideas:
                G.add_edge((IDEA, sec), (IDEA, b), weight=3.0, croise=True)

    # --- layout : phares fixes, îlots gravitent vers leur phare -------------
    pos = {}
    names = list(beacons)
    R = 9.0
    for i, b in enumerate(names):
        a = math.radians(-90 + (360 / max(len(names), 1)) * i)
        pos[(BEACON, b)] = (R * math.cos(a), R * 0.85 * math.sin(a))
    for n in G.nodes:
        if n not in pos:
            attached = [p for p in G.neighbors(n) if p[0] == BEACON]
            if attached:
                x, y = pos[attached[0]]
                pos[n] = (x + random.uniform(-2.5, 2.5), y + random.uniform(-2.5, 2.5))
            else:
                pos[n] = (random.uniform(-4, 4), random.uniform(-4, 4))
    pos = nx.spring_layout(G, pos=pos, fixed=[(BEACON, b) for b in names],
                           k=1.15, iterations=450, weight="weight", seed=42)
    # la pleine mer s'éloigne : les îlots sans phare forment leur propre zone
    for n in pos:
        if n[0] == IDEA and not ideas[n[1]]["relève"]:
            pos[n] = (pos[n][0] * 1.6 - 6.0, pos[n][1] * 1.6)

    # --- palette des climats -------------------------------------------------
    climats = sorted({d["doms"][0] for d in ideas.values()})
    cmap = plt.get_cmap("tab20")
    climate_color = {c: cmap(i % 20 / 20) for i, c in enumerate(climats)}

    # --- rendu ---------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(25, 16.5), facecolor=MER)
    ax.set_facecolor(MER)

    # faisceaux : chaque phare éclaire ses îlots rattachés (relève)
    for b in names:
        node = (BEACON, b)
        targets = [n for n in G.neighbors(node) if n[0] == IDEA]
        for tnode in targets:
            x0, y0 = pos[node]
            x1, y1 = pos[tnode]
            ax.plot([x0, x1], [y0, y1], color="#ffd54f", alpha=0.25, lw=1.2, zorder=1)
        # halo du phare
        ax.scatter(*pos[node], s=5200, color="#ffd54f", alpha=0.10, zorder=1,
                   linewidths=0)

    # seule la couvée est tracée : les courants restent dans le layout,
    # pas sur le rendu (ils étaient le fouillis)
    croise_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("croise")]
    nx.draw_networkx_edges(G, pos, edgelist=croise_edges, edge_color="#e8a13c",
                           width=2.2, ax=ax)

    beacon_nodes = [(BEACON, b) for b in names]
    nx.draw_networkx_nodes(G, pos, nodelist=beacon_nodes, node_shape="^",
                           node_color="#ffd54f", node_size=1900,
                           edgecolors="#0d1b2a", linewidths=1.5, ax=ax)

    base_nodes = [(IDEA, t) for t in ideas
                  if not ideas[t]["satellite"] and ideas[t]["relève"]]
    mer_nodes = [(IDEA, t) for t in ideas
                 if not ideas[t]["satellite"] and not ideas[t]["relève"]]
    sat_nodes = [(IDEA, t) for t in ideas if ideas[t]["satellite"]]
    nx.draw_networkx_nodes(G, pos, nodelist=mer_nodes, node_shape="o",
                           node_color=PLEINE_MER, node_size=110,
                           edgecolors=MER, linewidths=0.4, alpha=0.55, ax=ax)
    for nodes, marker, edge in ((base_nodes, "o", MER), (sat_nodes, "D", "#e8a13c")):
        nx.draw_networkx_nodes(
            G, pos, nodelist=nodes, node_shape=marker,
            node_color=[climate_color[ideas[n[1]]["doms"][0]] for n in nodes],
            node_size=[ideas[n[1]]["diameter"] for n in nodes],
            edgecolors=edge, linewidths=1.2 if marker == "D" else 0.6, ax=ax)

    for node, (x, y) in pos.items():
        kind, label = node
        if kind == BEACON:
            ax.text(x, y - 0.09, wrap(label, 16), ha="center", va="top",
                    fontsize=11.5, color="#ffd54f", fontweight="bold",
                    bbox=dict(facecolor=MER, alpha=0.75, edgecolor="none", pad=2))
        else:
            att = ideas[label]["relève"]
            ax.text(x, y - 0.045, wrap(label, 20), ha="center", va="top",
                    fontsize=7 if att else 5.8,
                    color=climate_color[ideas[label]["doms"][0]] if att
                    else "#48586b",
                    bbox=dict(facecolor=MER, alpha=0.55, edgecolor="none", pad=0.7))

    ax.set_title(
        f"Archipel des idées — {len(ideas)} îlots · {len(climats)} climats · "
        f"{len(crosses)} satellite(s) · {len(names)} phares",
        color="#dce8f5", fontsize=16, pad=18,
    )

    handles = [Line2D([], [], marker="^", linestyle="", markersize=12,
                      markerfacecolor="#ffd54f", color=MER, label=f"phare {b}")
               for b in names]
    handles += [
        Line2D([], [], marker="o", linestyle="", markersize=7,
               markerfacecolor="#8fa3b8", color=MER,
               label="îlot-idée (diamètre = outils dispo, couleur = climat)"),
        Line2D([], [], marker="D", linestyle="", markersize=7,
               markerfacecolor="#8fa3b8", markeredgecolor="#e8a13c", color=MER,
               label="satellite (couvée validée)"),
        Line2D([], [], color="#ffd54f", lw=1.2, alpha=0.5, label="faisceau du phare"),
        Line2D([], [], color="#e8a13c", lw=2, label="couvée"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7.2, ncol=4,
              facecolor="#0d1b2a", edgecolor="#22303f", labelcolor="#dce8f5")
    ax.axis("off")
    fig.tight_layout()
    OUT_PNG.parent.mkdir(exist_ok=True)
    fig.savefig(OUT_PNG, dpi=110, facecolor=fig.get_facecolor())
    print(f"rendu -> {OUT_PNG}")

    # --- note ---------------------------------------------------------------
    lines = ["", "## Diamètres remarquables (boîte à outils des dépôts)", ""]
    ranked = sorted(ideas.items(), key=lambda kv: -kv[1]["tool_score"])
    for t, d in ranked[:10]:
        lines.append(f"- score {d['tool_score']:.2f} — [[{t}]] "
                     f"(climat : {d['doms'][0]})")
    lines += ["", "## Faisceaux par phare", ""]
    for b in names:
        attached = [t for t, d in ideas.items() if d["beacon"] == b]
        if attached:
            lines.append(f"**{b}** : " + ", ".join(f"[[{t}]]" for t in attached))
        else:
            lines.append(f"**{b}** : aucun îlot rattaché — terre à coloniser")
    lines.append("")

    note = (
        "---\n"
        "généré: par tools/galaxie.py\n"
        "---\n\n"
        "# Archipel des idées\n\n"
        f"![[{OUT_PNG.name}]]\n\n"
        "Légende : les **phares** (triangles jaunes) sont les casquettes — les\n"
        "points d'attraction nommés. Les **îlots-idées** : leur couleur = leur\n"
        "**climat** (grande catégorie), leur **diamètre** = la boîte à outils\n"
        "disponible dans les dépôts pour les incarner (les dépôts eux-mêmes\n"
        "sont invisibles — ils pèsent sans paraître). Les **faisceaux** jaunes\n"
        "relient chaque îlot au phare de sa lignée documentaire. Les\n"
        "**satellites** (diamants, contour or) sont les croisements de couvée.\n\n"
        "Climats : " + ", ".join(climats) + "\n"
        + "\n".join(lines)
    )
    OUT_NOTE.write_text(note, encoding="utf-8")
    print(f"note -> {OUT_NOTE}")

    # --- version interactive (pyvis) : navigable, secouable -----------------
    from pyvis.network import Network

    net = Network(height="850px", width="100%", bgcolor="#0d1b2a",
                  font_color="#dce8f5", select_menu=False,
                  filter_menu=False, cdn_resources="remote")
    net.barnes_hut(gravity=-9000, spring_length=140, spring_strength=0.004,
                   damping=0.55)

    def node_id(n):
        return f"{n[0]}:{n[1]}"

    for b in names:
        node = (BEACON, b)
        x, y = pos[node]
        net.add_node(node_id(node), label=b, shape="triangle", size=22,
                     color={"background": "#ffd54f", "border": "#0d1b2a"},
                     title=f"Phare (casquette) — faisceaux vers ses idées",
                     x=x * 40, y=y * 40, fixed=True)
    for t, d in ideas.items():
        node = (IDEA, t)
        x, y = pos[node]
        col = climate_color[d["doms"][0]]
        net.add_node(
            node_id(node),
            label=wrap(t, 26).replace("\n", " "),
            shape="diamond" if d["satellite"] else "dot",
            size=4 + d["diameter"] / 55,
            color={"background": col, "border": "#e8a13c" if d["satellite"] else MER},
            title=f"{t}<br>climat : {d['doms'][0]} · outils : {d['tool_score']:.2f}"
                  f"<br>domaines : {', '.join(d['doms'])}",
            x=x * 40, y=y * 40,
        )
    for u, v, dd in G.edges(data=True):
        cu, cv = node_id(u), node_id(v)
        if dd.get("croise"):
            net.add_edge(cu, cv, color="#e8a13c", width=2.5,
                         title="couvée")
        elif u[0] == BEACON or v[0] == BEACON:
            net.add_edge(cu, cv, color="#ffd54f", width=1.0, alpha=0.25,
                         title="faisceau (relève)")
        else:
            shared = len(set(ideas[u[1]]["doms"]) & set(ideas[v[1]]["doms"]))
            net.add_edge(cu, cv, color="#2c3e50", width=0.4, alpha=0.35,
                         hidden=ideas[u[1]]["relève"] is not None
                         and ideas[v[1]]["relève"] is not None,
                         title=f"courant ({shared} domaine(s) partagé(s))")
    import json as _json
    net.set_options(_json.dumps({
        "physics": {"barnesHut": {"gravitationalConstant": -9000,
                                  "springLength": 140,
                                  "springStrength": 0.004,
                                  "damping": 0.55}},
        "interaction": {"hover": True},
    }))
    html_path = VAULT / "Archipel.html"
    net.write_html(str(html_path), notebook=False)
    print(f"interactif -> {html_path}")


if __name__ == "__main__":
    main()
