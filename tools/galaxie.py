"""Galaxie des idées — visualisation rudimentaire de la pouponnière.

Lit les notes de myVault/Idees/ (frontmatter domaines + croise), construit le
graphe idées ↔ domaines (+ liens de couvée), le dispose par forces
(spring layout — l'embryon de l'archipel de v1) et rend un PNG embarquable
dans le vault.

Usage : .venv/Scripts/python tools/galaxie.py
"""
import re
import sys
import textwrap
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "myVault"
IDEES = VAULT / "Idees"
OUT_PNG = VAULT / "pieces" / "galaxie-idees.png"
OUT_NOTE = IDEES / "Galaxie.md"

IDEA = "idee"
DOM = "domaine"


def parse_note(path: Path):
    text = path.read_text(encoding="utf-8")
    doms, croise = [], []
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if m:
        block = m.group(1)
        md = re.search(r"domaines:\s*\[(.*?)\]", block)
        if md:
            doms = [d.strip() for d in md.group(1).split(",") if d.strip()]
        for line in block.splitlines():
            if line.strip().startswith("croise:"):
                croise = re.findall(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]", line)
    return text, doms, croise


def wrap(label, width=20):
    return "\n".join(textwrap.wrap(label, width=width))


def main():
    ideas = {}  # titre -> domaines
    crosses = []  # (idée secondaire, [idées de base])
    skips = []
    for p in sorted(IDEES.glob("*.md")):
        if p.stem.startswith(("00", "Galaxie", "Couvées")):
            continue
        text, doms, croise = parse_note(p)
        if not doms:
            skips.append(p.stem)
            continue
        ideas[p.stem] = doms
        if croise:
            crosses.append((p.stem, croise))
    if skips:
        print("ignorées (sans domaines) :", skips)

    G = nx.Graph()
    for title, doms in ideas.items():
        G.add_node((IDEA, title))
        for d in doms:
            G.add_node((DOM, d))
            G.add_edge((IDEA, title), (DOM, d))
    for sec, bases in crosses:
        for b in bases:
            if b in ideas:
                G.add_edge((IDEA, sec), (IDEA, b), croise=True)

    # Position par forces — l'embryon d'archipel
    pos = nx.spring_layout(G, k=1.4, seed=42, iterations=300)

    doms_present = sorted({d for (_, d) in G.nodes if _ == DOM})
    cmap = plt.get_cmap("tab20")
    dom_color = {d: cmap(i % 20 / 20) for i, d in enumerate(doms_present)}

    fig, ax = plt.subplots(figsize=(22, 15), facecolor="#12141a")
    ax.set_facecolor("#12141a")

    croise_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("croise")]
    nx.draw_networkx_edges(G, pos, edgelist=list(G.edges() - croise_edges),
                           edge_color="#3a3f4d", width=0.7, alpha=0.6, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=croise_edges,
                           edge_color="#e8a13c", width=2.0, ax=ax)

    idea_nodes = [(IDEA, t) for t in ideas]
    dom_nodes = [(DOM, d) for d in doms_present]
    nx.draw_networkx_nodes(G, pos, nodelist=dom_nodes,
                           node_color=[dom_color[d] for d in doms_present],
                           node_size=900, edgecolors="white", linewidths=0.8, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=idea_nodes,
                           node_color="#cfd3dc", node_size=170,
                           edgecolors="#12141a", linewidths=0.5, ax=ax)

    for node, (x, y) in pos.items():
        kind, label = node
        if kind == DOM:
            ax.text(x, y + 0.06, wrap(label, 14), ha="center", va="bottom",
                    fontsize=9.5, color=dom_color[label], fontweight="bold",
                    bbox=dict(facecolor="#12141a", alpha=0.75, edgecolor="none", pad=1.5))
        else:
            ax.text(x, y - 0.04, wrap(label, 22), ha="center", va="top",
                    fontsize=6.5, color="#9aa2b1",
                    bbox=dict(facecolor="#12141a", alpha=0.65, edgecolor="none", pad=0.8))

    n_croise = len(crosses)
    ax.set_title(
        f"Galaxie des idées — {len(ideas)} idées de base · {len(doms_present)} domaines · "
        f"{n_croise} idée(s) secondaire(s)",
        color="#cfd3dc", fontsize=15, pad=18,
    )
    ax.axis("off")
    fig.tight_layout()
    OUT_PNG.parent.mkdir(exist_ok=True)
    fig.savefig(OUT_PNG, dpi=110, facecolor=fig.get_facecolor())
    print(f"rendu -> {OUT_PNG}")

    # Orphelines : idées dont tous les domaines ne les relient à aucune autre idée
    orphelines = [t for t, doms in ideas.items()
                  if not any(d in ds for t2, ds in ideas.items() if t2 != t for d in doms)]
    print(f"orphelines (aucun domaine partagé) : {orphelines or 'aucune'}")

    note = (
        "---\n"
        "généré: par tools/galaxie.py\n"
        "---\n\n"
        "# Galaxie des idées\n\n"
        f"![[{OUT_PNG.name}]]\n\n"
        f"{len(ideas)} idées de base · {len(doms_present)} domaines · "
        f"{n_croise} idée(s) secondaire(s). Les hubs colorés sont les domaines ; "
        "les liens orange sont les couvées validées. Régénéré par "
        "`tools/galaxie.py`.\n"
    )
    OUT_NOTE.write_text(note, encoding="utf-8")
    print(f"note -> {OUT_NOTE}")


if __name__ == "__main__":
    main()
