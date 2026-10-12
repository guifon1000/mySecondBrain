"""PNG de l'archipel — rendu matplotlib, depuis le module partagé graphe.

La version interactive vit dans le serveur (tools/archipel_serve.py) ;
ce PNG est la vue statique d'Obsidian (myVault/biblio/img/galaxie-idees.png).

Usage :  .venv/Scripts/python tools/galaxie.py
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D

import graphe

MER = "#0d1b2a"
DIM = "#2b3a4b"
LIT_LINK = "#e8a13c"
DIM_TXT = "#4a5a6b"
OUT_PNG = ROOT / "myVault" / "biblio" / "img" / "galaxie-idees.png"
OUT_NOTE = ROOT / "myVault" / "Fiches" / "Galaxie.md"


def main():
    fiches, ar, su, chemins, casq = graphe.construire()
    active = next((t for t, c in casq.items() if c["active"]), None)
    etats, scores = graphe.eclairage(casq, fiches)
    etat = etats.get(active or "__aucune__", {})

    # positions : même layout que la page interactive (graphe.py)
    pos = graphe.positions(fiches, ar, su, largeur=9.0, hauteur=5.6)

    dessines = {t: f for t, f in fiches.items() if f["type"] in graphe.TYPES_DESSINES}
    climats = sorted({f["domaines"][0] for f in dessines.values() if f["domaines"]})
    cmap = plt.get_cmap("tab20")
    climate_color = {c: cmap(i % 20 / 20) for i, c in enumerate(climats)}

    fig, ax = plt.subplots(figsize=(25, 15.6), facecolor=MER)
    ax.set_facecolor(MER)

    G = nx.Graph()
    G.add_nodes_from(dessines)
    for a, b in ar:
        if a in dessines and b in dessines:
            G.add_edge(a, b)
    for a, b in su:
        if a in dessines and b in dessines:
            G.add_edge(a, b)

    def ecl(n):
        return active is None or etat.get(n, False)

    # liens : confirmés (trait plein) + suggestions (pointillés)
    for a, b in ar:
        if a in dessines and b in dessines:
            on = ecl(a) and ecl(b)
            ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
                    color="#8fa3b8", alpha=0.55 if on else 0.08,
                    lw=1.6 if on else 0.7, zorder=1)
    for a, b in su:
        if a in dessines and b in dessines:
            on = ecl(a) or ecl(b)
            ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]],
                    color=LIT_LINK, alpha=0.75 if on else 0.15,
                    lw=1.6, linestyle=":", zorder=1)

    # nœuds
    for n, (x, y) in pos.items():
        if n not in dessines:
            continue
        f = dessines[n]
        on = ecl(n)
        couleur = climate_color.get(f["domaines"][0], "#6c7a89") if f["domaines"] else "#6c7a89"
        if not on:
            couleur = DIM
        if f["type"] == "source":
            ax.scatter(x, y, s=f["diametre"] * 0.85, marker="D",
                       color=couleur, edgecolors=LIT_LINK, linewidths=1.4,
                       alpha=1.0 if on else 0.45, zorder=3)
        else:
            ax.scatter(x, y, s=f["diametre"], marker="o",
                       color=couleur, edgecolors=MER, linewidths=0.6,
                       alpha=1.0 if on else 0.45, zorder=3)
        ax.text(x, y - 0.055, graphe.wrap(n, 22), ha="center", va="top",
                fontsize=9.5 if on else 6.5,
                color=climate_color.get(f["domaines"][0], "#6c7a89") if on and f["domaines"]
                else (DIM_TXT if not on else "#6c7a89"),
                bbox=dict(facecolor=MER, alpha=0.55 if on else 0.3,
                          edgecolor="none", pad=1.2), zorder=4)

    titre = f"Archipel — casquette : {active}" if active else "Archipel — carte neutre"
    n_lit = sum(1 for n in dessines if ecl(n))
    ax.set_title(f"{titre} · {n_lit} éclairées / {len(dessines)} · "
                 f"{len(ar)} liens · {len(su)} suggestion(s)",
                 color="#dce8f5", fontsize=15, pad=16)
    handles = [
        Line2D([], [], marker="o", linestyle="", markersize=8, markerfacecolor="#8fa3b8",
               color=MER, label="fiche (couleur = climat, taille = outillage)"),
        Line2D([], [], marker="D", linestyle="", markersize=7, markerfacecolor="#8fa3b8",
               markeredgecolor=LIT_LINK, color=MER, label="source (fiche de lecture)"),
        Line2D([], [], color="#8fa3b8", lw=1.6, alpha=0.6, label="lien confirmé"),
        Line2D([], [], color=LIT_LINK, lw=1.6, linestyle=":", label="suggestion de l'agent"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8, ncol=4,
              facecolor=MER, edgecolor="#22303f", labelcolor="#dce8f5")
    ax.axis("off")
    fig.tight_layout()
    OUT_PNG.parent.mkdir(exist_ok=True)
    fig.savefig(OUT_PNG, dpi=110, facecolor=fig.get_facecolor())
    print(f"rendu -> {OUT_PNG}")

    # note d'Obsidian
    lignes = ["", "## Liens", ""]
    for a, b in sorted(set(ar)):
        lignes.append(f"- [[{a}]] ↔ [[{b}]]")
    if su:
        lignes += ["", "## Suggestions", ""]
        for a, b in sorted(set(su)):
            lignes.append(f"- [[{a}]] ~ [[{b}]]")
    note = ("---\ngénéré: par tools/galaxie.py\n---\n\n"
            "# Archipel\n\n"
            f"![[{OUT_PNG.name}]]\n\n"
            "Vue statique. La carte interactive : `python tools/archipel_serve.py`.\n"
            + "\n".join(lignes) + "\n")
    OUT_NOTE.write_text(note, encoding="utf-8")
    print(f"note -> {OUT_NOTE}")


if __name__ == "__main__":
    main()
