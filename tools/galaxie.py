"""Galaxie des idées — v0.3 : la carte d'archipel.

Les projets/casquettes sont des ÎLES ancrées (structurent le plan) ; les
idées sont des débris flottants caractérisés par :
  - position   : layout par forces pondéré par les domaines partagés
  - climat     : couleur = destination dominante (tirage lexical + lignée)
  - masse      : taille (lignée + lexical)
  - forêt      : richesse du scan du dépôt derrière l'idée (densité du fond)
Les idées secondaires validées sont des satellites (diamants).
La gravité est calculée au rendu, jamais stockée.

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
OUT_PNG = VAULT / "pieces" / "galaxie-idees.png"
OUT_NOTE = IDEES / "Galaxie.md"

IDEA, DOM, ISLE = "idee", "domaine", "ile"

STOPWORDS = set("""
le la les un une des de du au aux et ou en dans sur pour par avec sans sous
ce cet cette ces son sa ses leur leurs qui que quoi dont où est sont était
être avoir a ont plus moins très tout toute tous toutes même comme donc
ainsi alors mais car si ne pas chaque avant après entre vers chez hors dès
lors tant déjà encore toujours jamais peut peuvent doit doivent fait faire
cas type types partie point exemple etc cf see the of and in to for with
""".split())

PALETTE = {
    # projets (froids / techniques)
    "Rincewind": "#4fc3f7", "Renardiere": "#81c784",
    "Sapientpearwood": "#ffb74d", "Demonstrateur": "#ba68c8",
    "Test corpus": "#a1887f",
    # casquettes métier (chaudes terre)
    "Charpentier": "#e57373", "Couvreur": "#ff8a65", "Menuisier": "#ffd54f",
    "Zingueur": "#90a4ae", "Maçon": "#bcaaa4",
    # casquettes tech (froides)
    "Geek": "#4db6ac", "Développeur": "#64b5f6", "Ingénieur CFD": "#9575cd",
}
MER = "#12141a"
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
    projects = {}
    for r in conn.execute("SELECT id, title, kind, code_scan_text FROM projects"):
        tk = tokens(r["code_scan_text"] or "")
        projects[r["title"]] = {"id": r["id"], "kind": r["kind"], "tokens": tk,
                                "richesse": min(len(tk) / 60.0, 1.0)}
    lineage = {}
    for r in conn.execute("SELECT vault_note, linked_project_id FROM items"):
        if not r["vault_note"] or not r["linked_project_id"]:
            continue
        m = re.match(r"SB-(\d+)", Path(r["vault_note"]).name)
        pt = conn.execute("SELECT title FROM projects WHERE id = ?",
                          (r["linked_project_id"],)).fetchone()
        if m and pt:
            lineage.setdefault(int(m.group(1)), set()).add(pt["title"])
    conn.close()
    return projects, lineage


def main():
    random.seed(42)
    projects, lineage = load_codebase()

    ideas, crosses = {}, []
    for p in sorted(IDEES.glob("*.md")):
        if p.stem.startswith(("00", "Galaxie", "Couvées")):
            continue
        doms, croise, source, body = parse_note(p)
        if not doms:
            continue
        ideas[p.stem] = {"doms": doms, "croise": croise, "source": source,
                         "tokens": tokens(body)}
        if croise:
            crosses.append((p.stem, croise))

    # --- masse + tirage -----------------------------------------------------
    for t, d in ideas.items():
        mass, pulls = 0.0, {}
        for ptitle, pdata in projects.items():
            lineage_hit = bool(d["source"] and d["source"] in lineage
                               and ptitle in lineage[d["source"]])
            if lineage_hit:
                mass += 2.0
            common = d["tokens"] & pdata["tokens"]
            if common and d["tokens"]:
                score = min(len(common) / (len(d["tokens"]) ** 0.5
                                           * max(len(pdata["tokens"]), 1) ** 0.25), 1.0)
                mass += 1.2 * score
                pulls[ptitle] = score + (1.0 if lineage_hit else 0.0)
        d["mass"] = round(mass, 2)
        d["pulls"] = pulls
        d["dest"] = max(pulls, key=pulls.get) if pulls else None

    # --- graphe -------------------------------------------------------------
    G = nx.Graph()
    for title, d in ideas.items():
        G.add_node((IDEA, title))
        for dom in d["doms"]:
            G.add_node((DOM, dom))
            G.add_edge((IDEA, title), (DOM, dom))
    for sec, bases in crosses:
        for b in bases:
            if b in ideas:
                G.add_edge((IDEA, sec), (IDEA, b), croise=True)
    island_nodes = []
    for ptitle in projects:
        node = (ISLE, ptitle)
        G.add_node(node)
        island_nodes.append(node)
        for t, d in ideas.items():
            w = d["pulls"].get(ptitle, 0.0)
            if w >= 0.35:
                G.add_edge(node, (IDEA, t), weight=0.4 + w)

    # --- layout : îles ancrées d'abord, le reste gravite --------------------
    pos = {}
    projets = [i for i in projects if projects[i]["kind"] == "projet"]
    casquettes = [i for i in projects if projects[i]["kind"] == "casquette"]
    for i, p in enumerate(projets):   # arc droit
        a = math.radians(-50 + (100 / max(len(projets) - 1, 1)) * i)
        pos[(ISLE, p)] = (11 * math.cos(a), 11 * math.sin(a))
    for i, c in enumerate(casquettes):  # arc gauche
        a = math.radians(115 + (130 / max(len(casquettes) - 1, 1)) * i)
        pos[(ISLE, c)] = (11 * math.cos(a), 11 * math.sin(a))
    for n in G.nodes:
        if n not in pos:
            dest = None
            if n[0] == IDEA:
                dest = ideas[n[1]]["dest"]
            if dest:
                x, y = pos[(ISLE, dest)]
                pos[n] = (x + random.uniform(-2, 2), y + random.uniform(-2, 2))
            else:
                pos[n] = (random.uniform(-4, 4), random.uniform(-4, 4))
    pos = nx.spring_layout(G, pos=pos, fixed=island_nodes, k=1.3,
                           iterations=400, weight="weight", seed=42)

    doms_present = sorted({d for (_, d) in G.nodes if _ == DOM})

    # --- rendu --------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(26, 17), facecolor="#0d1b2a")
    ax.set_facecolor("#0d1b2a")

    # forêt : densité du scan derrière les idées qui tirent
    for t, d in ideas.items():
        if d["dest"]:
            col = PALETTE.get(d["dest"], PLEINE_MER)
            pull = d["pulls"][d["dest"]]
            ax.scatter(*pos[(IDEA, t)], s=(400 + 2600 * pull),
                       color=col, alpha=0.05 + 0.10 * pull, zorder=1, linewidths=0)
    for ptitle in projects:
        x, y = pos[(ISLE, ptitle)]
        ax.scatter(x, y, s=9000 * projects[ptitle]["richesse"] + 2500,
                   color=PALETTE.get(ptitle, "#e8a13c"), alpha=0.08,
                   zorder=1, linewidths=0)

    croise_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("croise")]
    grav_edges = [(u, v) for u, v in G.edges() if u[0] == ISLE or v[0] == ISLE]
    plain_edges = [(u, v) for u, v, d in G.edges(data=True)
                   if not d.get("croise") and u[0] != ISLE and v[0] != ISLE]
    nx.draw_networkx_edges(G, pos, edgelist=plain_edges, edge_color="#3a5266",
                           width=0.7, alpha=0.5, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=croise_edges, edge_color="#e8a13c",
                           width=2.2, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=grav_edges, edge_color="#6f9fd8",
                           width=1.3, style="dashed", alpha=0.7, ax=ax)

    isle_nodes = [(ISLE, t) for t in projects]
    dom_nodes = [(DOM, d) for d in doms_present]
    nx.draw_networkx_nodes(G, pos, nodelist=isle_nodes, node_shape="s",
                           node_color=[PALETTE.get(t, "#e8a13c") for t in projects],
                           node_size=3000, edgecolors="#0d1b2a", linewidths=2, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=dom_nodes,
                           node_color="#22303f", node_size=650,
                           edgecolors="#8fa3b8", linewidths=1.0, ax=ax)

    # idées : couleur = climat ; satellites = diamants
    base_nodes, sat_nodes = [], []
    for t in ideas:
        (sat_nodes if ideas[t]["croise"] else base_nodes).append((IDEA, t))
    for nodes, marker, edge in ((base_nodes, "o", "#0d1b2a"),
                                (sat_nodes, "D", "#e8a13c")):
        nx.draw_networkx_nodes(
            G, pos, nodelist=nodes, node_shape=marker,
            node_color=[PALETTE.get(ideas[n[1]]["dest"], PLEINE_MER)
                        if ideas[n[1]]["dest"] else PLEINE_MER for n in nodes],
            node_size=[140 + 240 * ideas[n[1]]["mass"] for n in nodes],
            edgecolors=edge, linewidths=1.2 if marker == "D" else 0.5, ax=ax)

    for node, (x, y) in pos.items():
        kind, label = node
        if kind == ISLE:
            ax.text(x, y - 0.09, f"{wrap(label, 16)}\n({projects[label]['kind']})",
                    ha="center", va="top", fontsize=10.5, color=PALETTE.get(label, "#e8a13c"),
                    fontweight="bold",
                    bbox=dict(facecolor="#0d1b2a", alpha=0.8, edgecolor="none", pad=2))
        elif kind == DOM:
            ax.text(x, y + 0.05, label, ha="center", va="bottom", fontsize=8.5,
                    color="#8fa3b8",
                    bbox=dict(facecolor="#0d1b2a", alpha=0.7, edgecolor="none", pad=1.2))
        else:
            col = PALETTE.get(ideas[label]["dest"], PLEINE_MER) \
                if ideas[label]["dest"] else PLEINE_MER
            ax.text(x, y - 0.035, wrap(label, 20), ha="center", va="top",
                    fontsize=6.2, color=col if ideas[label]["dest"] else PLEINE_MER,
                    bbox=dict(facecolor="#0d1b2a", alpha=0.55, edgecolor="none", pad=0.7))

    ax.set_title(
        f"Archipel des idées — {len(ideas)} débris · {len(doms_present)} courants · "
        f"{len(crosses)} satellite(s) · {len(projects)} îles",
        color="#dce8f5", fontsize=16, pad=18,
    )
    handles = [Line2D([], [], marker="s", linestyle="", markersize=11,
                      markerfacecolor=PALETTE[t], color="#0d1b2a",
                      label=f"île {t}") for t in projects]
    handles += [
        Line2D([], [], marker="o", linestyle="", markersize=7, markerfacecolor="#8fa3b8",
               label="débris (idée de base, couleur = climat)"),
        Line2D([], [], marker="D", linestyle="", markersize=7, markerfacecolor="#8fa3b8",
               markeredgecolor="#e8a13c", label="satellite (couvée validée)"),
        Line2D([], [], color="#e8a13c", lw=2, label="couvée"),
        Line2D([], [], color="#6f9fd8", lw=1.4, ls="--", label="tirage lexical"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=7.5, ncol=3,
              facecolor="#0d1b2a", edgecolor="#22303f", labelcolor="#dce8f5")
    ax.axis("off")
    fig.tight_layout()
    OUT_PNG.parent.mkdir(exist_ok=True)
    fig.savefig(OUT_PNG, dpi=110, facecolor=fig.get_facecolor())
    print(f"rendu -> {OUT_PNG}")

    # --- rapport -------------------------------------------------------------
    lines = ["", "## Tirage lexical par île (idées non incarnées, w >= 0.35)", ""]
    for ptitle in projects:
        ranked = sorted(((t, ideas[t]["pulls"][ptitle]) for t in ideas
                         if ptitle in ideas[t]["pulls"]), key=lambda x: -x[1])
        incarnated = {t for t in ideas
                      if ideas[t]["source"] in lineage
                      and ptitle in lineage[ideas[t]["source"]]}
        non_inc = [(t, w) for t, w in ranked if t not in incarnated]
        if not non_inc:
            continue
        lines.append(f"**{ptitle}**")
        for t, w in non_inc[:5]:
            lines.append(f"- w={w:.2f} — [[{t}]]")
        lines.append("")

    note = (
        "---\n"
        "généré: par tools/galaxie.py\n"
        "---\n\n"
        "# Archipel des idées\n\n"
        f"![[{OUT_PNG.name}]]\n\n"
        "Légende : les **îles** (carrés) sont les projets et casquettes — les\n"
        "ancrages stables. Les **débris** (ronds) sont les idées de base, leur\n"
        "**couleur = leur climat** (destination dominante), leur **taille = leur\n"
        "masse** (lignée documentaire + adéquation lexicale avec les dépôts).\n"
        "Le fond derrière chaque idée = la **forêt** (richesse du code disponible\n"
        "pour l'incarner). La **pleine mer** (gris-bleu) = idées sans tirage —\n"
        "les candidates des couvées. Les **satellites** (diamants) sont les\n"
        "croisements validés.\n\n"
        + "\n".join(lines)
    )
    OUT_NOTE.write_text(note, encoding="utf-8")
    print(f"note -> {OUT_NOTE}")


if __name__ == "__main__":
    main()
