"""Galaxie des idées — v0.2 : gravité par la base de code.

Les projets deviennent des îles ; chaque idée reçoit une masse selon :
  1. sa lignée documentaire (source fiche SB-xxxx -> item lié à un projet),
  2. l'adéquation lexicale entre son texte et le scan du dépôt (code_scan_text),
La gravité est calculée au rendu, jamais stockée dans les notes.

Rapport : par projet, les idées à fort tirage lexical non incarnées
(matière pour les sessions de tri / les instances Pi des projets).

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

IDEA, DOM, ISLE = "idee", "domaine", "ile"

# --- Lexique : stopwords FR courants + vocabulaire structurel ---------------
STOPWORDS = set("""
le la les un une des de du au aux et ou en dans sur pour par avec sans sous
sur ce cet cette ces son sa ses leur leurs qui que quoi dont où est sont
était étaient être avoir a ont plus moins très tout toute tous toutes même
comme donc ainsi alors mais car si ne pas pas-nul chaque avant après entre
vers chez hors dès lors tant déjà encore toujours parfois parfois jamais
peut peuvent doit doivent fait faire cas type types partie parts point
exemple ex etc cf see the of and in to for with
""".split())


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
    """Projets + scans + liens item->projet, en lecture seule."""
    import sqlite3

    conn = sqlite3.connect(ROOT / "data" / "secondbrain.db")
    conn.row_factory = sqlite3.Row
    projects = {}
    for r in conn.execute(
        "SELECT id, title, kind, code_scan_text FROM projects"
    ):
        projects[r["title"]] = {
            "id": r["id"],
            "kind": r["kind"],
            "tokens": tokens(r["code_scan_text"] or ""),
            "n_tokens": len(tokens(r["code_scan_text"] or "")),
        }
    # lignée : source_id (fiche SB) -> projets via items liés
    lineage = {}  # sb_id -> {titre_projet: True}
    for r in conn.execute(
        "SELECT id, vault_note, linked_project_id FROM items"
    ):
        if not r["vault_note"] or not r["linked_project_id"]:
            continue
        note = Path(r["vault_note"]).name
        m = re.match(r"SB-(\d+)", note)
        if not m:
            continue
        ptitle = conn.execute(
            "SELECT title FROM projects WHERE id = ?", (r["linked_project_id"],)
        ).fetchone()
        if ptitle:
            lineage.setdefault(int(m.group(1)), set()).add(ptitle["title"])
    conn.close()
    return projects, lineage


def main():
    projects, lineage = load_codebase()

    ideas = {}  # titre -> dict(doms, croise, source, tokens)
    crosses = []
    for p in sorted(IDEES.glob("*.md")):
        if p.stem.startswith(("00", "Galaxie", "Couvées")):
            continue
        doms, croise, source, body = parse_note(p)
        if not doms:
            continue
        ideas[p.stem] = {
            "doms": doms,
            "croise": croise,
            "source": source,
            "tokens": tokens(body),
        }
        if croise:
            crosses.append((p.stem, croise))

    # --- masse : lignée + lexical -----------------------------------------
    for t, d in ideas.items():
        mass = 0.0
        pulls = {}
        for ptitle, pdata in projects.items():
            # 1. lignée documentaire
            lineage_hit = bool(d["source"] and d["source"] in lineage
                               and ptitle in lineage[d["source"]])
            if lineage_hit:
                mass += 2.0
            # 2. adéquation lexicale (jaccard pondéré)
            common = d["tokens"] & pdata["tokens"]
            if common and d["tokens"]:
                score = len(common) / (
                    len(d["tokens"]) ** 0.5 * max(pdata["n_tokens"], 1) ** 0.25
                )
                # normalisation douce : une idée courte ne doit pas être écrasée
                score = min(score, 1.0)
                mass += 1.2 * score
                pulls[ptitle] = score + (1.0 if lineage_hit else 0.0)
        d["mass"] = round(mass, 2)
        d["pulls"] = pulls

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
    # îles dans le graphe avec ressorts pondérés par le tirage
    island_titles = []
    for ptitle, pdata in projects.items():
        node = (ISLE, ptitle)
        G.add_node(node)
        island_titles.append(ptitle)
        for t, d in ideas.items():
            w = d["pulls"].get(ptitle, 0.0)
            if w >= 0.35:  # seuil : seule une adéquation notable attire
                G.add_edge(node, (IDEA, t), weight=w)

    pos = nx.spring_layout(G, k=1.5, seed=42, iterations=350, weight="weight")

    doms_present = sorted({d for (_, d) in G.nodes if _ == DOM})
    cmap = plt.get_cmap("tab20")
    dom_color = {d: cmap(i % 20 / 20) for i, d in enumerate(doms_present)}

    fig, ax = plt.subplots(figsize=(24, 16), facecolor="#12141a")
    ax.set_facecolor("#12141a")

    croise_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("croise")]
    plain_edges = [(u, v) for u, v, d in G.edges(data=True) if not d.get("croise")
                   and u[0] != ISLE and v[0] != ISLE]
    grav_edges = [(u, v) for u, v in G.edges() if u[0] == ISLE or v[0] == ISLE]
    nx.draw_networkx_edges(G, pos, edgelist=plain_edges, edge_color="#3a3f4d",
                           width=0.7, alpha=0.55, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=croise_edges, edge_color="#e8a13c",
                           width=2.0, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=grav_edges, edge_color="#4f7fd0",
                           width=1.4, style="dashed", alpha=0.75, ax=ax)

    idea_nodes = [(IDEA, t) for t in ideas]
    sizes = [120 + 260 * ideas[t]["mass"] for t in ideas]  # taille ~ masse
    max_mass = max((d["mass"] for d in ideas.values()), default=1)
    idea_colors = ["#d8dce6" if d["mass"] < 0.4 * max_mass else "#ffffff"
                   for d in (ideas[t] for t in ideas)]
    dom_nodes = [(DOM, d) for d in doms_present]
    nx.draw_networkx_nodes(G, pos, nodelist=dom_nodes,
                           node_color=[dom_color[d] for d in doms_present],
                           node_size=900, edgecolors="white", linewidths=0.8, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=idea_nodes,
                           node_color=idea_colors, node_size=sizes,
                           edgecolors="#12141a", linewidths=0.5, ax=ax)
    isle_nodes = [(ISLE, t) for t in island_titles]
    nx.draw_networkx_nodes(G, pos, nodelist=isle_nodes, node_shape="s",
                           node_color="#e8a13c", node_size=2600,
                           edgecolors="#12141a", linewidths=1.5, ax=ax)

    for node, (x, y) in pos.items():
        kind, label = node
        if kind == DOM:
            ax.text(x, y + 0.06, wrap(label, 14), ha="center", va="bottom",
                    fontsize=9.5, color=dom_color[label], fontweight="bold",
                    bbox=dict(facecolor="#12141a", alpha=0.75, edgecolor="none", pad=1.5))
        elif kind == ISLE:
            kind_p = projects[label]["kind"]
            ax.text(x, y - 0.07, f"île·{kind_p}\n{wrap(label, 16)}",
                    ha="center", va="top", fontsize=10, color="#e8a13c",
                    fontweight="bold",
                    bbox=dict(facecolor="#12141a", alpha=0.8, edgecolor="none", pad=2))
        else:
            ax.text(x, y - 0.04, wrap(label, 22), ha="center", va="top",
                    fontsize=6.5, color="#9aa2b1",
                    bbox=dict(facecolor="#12141a", alpha=0.65, edgecolor="none", pad=0.8))

    n_croise = len(crosses)
    ax.set_title(
        f"Galaxie des idées — {len(ideas)} idées · {len(doms_present)} domaines · "
        f"{n_croise} couvée(s) · {len(island_titles)} îles de code",
        color="#cfd3dc", fontsize=15, pad=18,
    )
    ax.axis("off")
    fig.tight_layout()
    OUT_PNG.parent.mkdir(exist_ok=True)
    fig.savefig(OUT_PNG, dpi=110, facecolor=fig.get_facecolor())
    print(f"rendu -> {OUT_PNG}")

    # --- rapport : tirage lexical non incarné ------------------------------
    lines = ["", "## Tirage lexical par île (idées non incarnées, w >= 0.35)", ""]
    total_pulls = 0
    for ptitle in island_titles:
        ranked = sorted(
            ((t, ideas[t]["pulls"][ptitle]) for t in ideas
             if ptitle in ideas[t]["pulls"]),
            key=lambda x: -x[1],
        )
        # incarnées = avec lien de lignée vers CE projet
        incarnated = {
            t for t in ideas
            if ideas[t]["source"] in lineage and ptitle in lineage[ideas[t]["source"]]
        }
        non_inc = [(t, w) for t, w in ranked if t not in incarnated]
        if not non_inc:
            continue
        lines.append(f"**{ptitle}**")
        for t, w in non_inc[:5]:
            lines.append(f"- w={w:.2f} — [[{t}]]")
            total_pulls += 1
        lines.append("")
    print(f"tirages signalés : {total_pulls}")

    note = (
        "---\n"
        "généré: par tools/galaxie.py\n"
        "---\n\n"
        "# Galaxie des idées\n\n"
        f"![[{OUT_PNG.name}]]\n\n"
        f"{len(ideas)} idées · {len(doms_present)} domaines · {n_croise} couvée(s) · "
        f"{len(island_titles)} îles de code. La **taille** d'une idée = sa masse "
        "(lignée documentaire + adéquation lexicale avec les dépôts). Les îles "
        "(carrés orange) attirent les idées via ressorts pondérés — liens bleus "
        "pointillés = tirage lexical, jamais d'affectation automatique.\n\n"
        + "\n".join(lines)
    )
    OUT_NOTE.write_text(note, encoding="utf-8")
    print(f"note -> {OUT_NOTE}")


if __name__ == "__main__":
    main()
