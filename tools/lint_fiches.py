"""Lint des fiches : liens cassés, chemins de code périmés, PDF absents,
citations invérifiables, orphelines, domaines dérivants.

Usage :  .venv/Scripts/python tools/lint_fiches.py [--json]

Ce que ça vérifie (tout déterministe, zéro IA) :
- **Liens** : tout [[wikilink]] du corps et tout champ lie/suggere doit
  pointer vers une fiche existante (casse corrigée si possible).
- **Chemins de code** : les champs code/incarnation citent des chemins
  rincewind/... ; le lint vérifie l'existence, et interroge git si le
  chemin a disparu (renommage détectable : git log --follow). La fiche
  cite aussi bien des fichiers réels que disparus ; les disparus sont
  listés avec le successeur git quand il existe.
- **PDF** : le champ pdf doit exister dans myVault/biblio/pdf (ou E:/pdf_library).
- **Citations** : dans les fiches source, les pages citées (p. N, pages N-M)
  doivent exister dans le PDF, et toute citation longue entre guillemets
  doit se retrouver (à tolérance proche) dans le texte de la page citée.
- **Orphelines** : aucune fiche sans lien ni suggestion (rappel doux :
  une fiche ne survit qu'en se reliant).
- **Domaines** : un domaine qui n'est utilisé par aucune casquette ni
  aucune autre fiche (>= 2 occurrences ailleurs) est signalé (dérive
  lexicale possible).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "myVault"
sys.path.insert(0, str(ROOT / "tools"))
import graphe  # noqa: E402

ERREUR, AVERT, INFO = "erreur", "avertissement", "info"


def git_renommage(depot: Path, chemin: str) -> str | None:
    """Si le chemin a disparu du dépôt, git connaît-il un renommage ?"""
    if not (depot / ".git").exists():
        return None
    try:
        r = subprocess.run(
            ["git", "-C", str(depot), "log", "--follow", "--diff-filter=R",
             "--name-status", "--all", "-n", "5", "--", chemin],
            capture_output=True, text=True, timeout=10)
        for ligne in r.stdout.splitlines():
            m = re.match(r"^R\d+\t(.+)\t(.+)$", ligne)
            if m and m.group(2).endswith(chemin.split("/")[-1]):
                return m.group(2)
        return None
    except Exception:
        return None


def pages_pdf(chemin_pdf: Path) -> int:
    try:
        import pymupdf
        return pymupdf.open(str(chemin_pdf)).page_count
    except Exception:
        return 0


def lint():
    fiches, ar, su, chemins_dep, chant = graphe.construire()
    par_casse = {t.casefold(): t for t in fiches}
    trouver = graphe.FICHES
    rapport = []

    def signaler(niveau, fiche, message):
        rapport.append({"niveau": niveau, "fiche": fiche, "message": message})

    # 1. liens
    for t, f in fiches.items():
        corps = f["corps"]
        for l in set(re.findall(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]", corps)):
            if l.casefold() not in par_casse and not l.startswith("_sources"):
                signaler(ERREUR, t, f"lien cassé vers « {l} »")
        for champ_nom in ("lie", "suggere"):
            for l in f[champ_nom]:
                if l.casefold() not in par_casse:
                    signaler(ERREUR, t, f"{champ_nom}: cassé vers « {l} »")

    # 2. chemins de code
    for t, f in fiches.items():
        cites = []
        for champ_nom in ("code", "incarnation"):
            if f.get(champ_nom):
                cites += re.findall(r"[\w\-]+/[\w\-./]+\.py", f[champ_nom])
        if not cites:
            continue
        # dépôt : premier segment du chemin
        for chemin in set(cites):
            depot_nom = chemin.split("/")[0]
            cible = None
            for titre, c in chemins_dep.items():
                if titre.casefold() == depot_nom.casefold():
                    cible = Path(c) if c else None
                    break
            if cible is None:
                signaler(INFO, t, f"chemin « {chemin} » : dépôt « {depot_nom} » inconnu")
                continue
            rel = chemin.split("/", 1)[1]
            # le chemin peut viser le package du dépôt (rincewind/geometry/...
            # dans le dépôt rincewind) ou être relatif à sa racine
            if (cible / rel).exists() or (cible / chemin).exists():
                continue
            succ = git_renommage(cible, rel)
            if succ:
                signaler(AVERT, t, f"chemin périmé « {chemin} » → renommé « {succ} » (vérifier et mettre à jour)")
            else:
                signaler(AVERT, t, f"chemin « {chemin} » introuvable dans le dépôt (ni renommage git)")

    # 3. PDF + citations des fiches source
    biblio = VAULT / "biblio" / "pdf"
    for t, f in fiches.items():
        if f["type"] != "source" or not f["pdf"]:
            continue
        pdf = biblio / f["pdf"]
        if not pdf.exists():
            pdf = Path(f["pdf"]) if Path(f["pdf"]).exists() else None
        if pdf is None:
            signaler(ERREUR, t, f"pdf introuvable : {f['pdf']}")
            continue
        n_pages = pages_pdf(pdf)
        # pages citées
        pages_citees = set()
        for m in re.finditer(r"pp?\.?\s*(\d+)(?:\s*[-–]\s*(\d+))?", f["corps"]):
            d, fi = int(m.group(1)), int(m.group(2) or m.group(1))
            pages_citees.update(range(d, fi + 1))
        pages_citees = {p for p in pages_citees if 0 < p <= max(n_pages, 4000)}
        for p in sorted(pages_citees):
            if p > n_pages:
                signaler(ERREUR, t, f"page citée {p} hors document ({n_pages} pages)")
        # citations longues : vérifiables sur la page
        if n_pages:
            import pymupdf
            doc = pymupdf.open(str(pdf))
            for m in re.finditer(r"«\s*([^«»]{40,})\s*»", f["corps"]):
                # ne vérifier que les guillemets accrochés à une page citée :
                # les autres guillemets sont du style de rédaction, pas des
                # affirmations de provenance
                contexte = f["corps"][max(0, m.start() - 120):m.end() + 120]
                if not re.search(r"pp?\.?\s*\d+", contexte):
                    continue
                cite = re.sub(r"\s+", " ", m.group(1)).strip()
                trouve = False
                for p in (pages_citees or {1}):
                    if p > n_pages:
                        continue
                    texte = re.sub(r"\s+", " ", doc[p - 1].get_text() or "")
                    if cite[:60] in texte:
                        trouve = True
                        break
                if not trouve:
                    signaler(AVERT, t, f"citation (page citée à proximité) introuvable : « {cite[:50]}… »")

    # 4. orphelines
    pour_fiche = {t: set() for t in fiches}
    for a, b in ar + su:
        pour_fiche[a].add(b)
        pour_fiche[b].add(a)
    for t, voisins in pour_fiche.items():
        if fiches[t]["type"] in ("idee", "note") and not voisins:
            signaler(AVERT, t, "fiche orpheline : aucun lien, aucune suggestion")

    # 5. domaines
    usage = {}
    for t, f in fiches.items():
        for d in f["domaines"]:
            usage.setdefault(d, []).append(t)
    doms_chant = {d for c in chant.values() for d in graphe.domaines_de(graphe.frontmatter(c["path"].read_text(encoding="utf-8")))}
    for d, fs in usage.items():
        if d not in doms_chant and len(fs) == 1:
            signaler(INFO, fs[0], f"domaine « {d} » isolé (ni chantier, ni autre fiche) — dérive lexicale ?")

    return rapport, fiches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rapport, fiches = lint()
    if a.json:
        print(json.dumps(rapport, ensure_ascii=False, indent=1))
        return
    if not rapport:
        print("lint : rien à signaler")
        return
    poids = {ERREUR: 0, AVERT: 1, INFO: 2}
    for e in sorted(rapport, key=lambda x: (poids[x["niveau"]], x["fiche"])):
        symbole = {"erreur": "✗", "avertissement": "!", "info": "·"}[e["niveau"]]
        print(f"{symbole} [{e['niveau']:<14}] {e['fiche'][:44]:<44} {e['message']}")
    n = {}
    for e in rapport:
        n[e["niveau"]] = n.get(e["niveau"], 0) + 1
    print(f"\n{len(rapport)} signalements : " + ", ".join(f"{v} {k}s" for k, v in n.items()))


if __name__ == "__main__":
    main()
