# Écosystème code — carte des projets

> Note d'index tenue par l'agent Pi du second cerveau. Chaque dépôt a son
> fichier détail dans `Projets/` et une instance Pi qui le gère.

## Organisation du vault

- `Projets/` — un fichier par projet (+ éventuellement un sous-dossier par
  projet recevant les notes d'items liés)
- `Inbox/` — **une note par capture en attente de tri** (tenue par l'app) :
  c'est la vue Obsidian du rituel. Quand un item est lié, sa note est
  déplacée vers `Projets/<projet>/` ; archivé → `Archives/`.
- `Archives/` — notes des items archivés (récupérables, jamais supprimés)
- `pieces/` — pièces jointes (images, PDF) embarquées dans les notes

Les notes d'inbox ont un frontmatter `sb_id` : elles sont gérées par l'app
(déplacement auto au tri), mais tu peux les annoter librement — le corps est
préservé lors des déplacements. Les renommer casse juste le déplacement auto.

| Projet (second cerveau) | Dépôt | Instance Pi | Rôle |
|---|---|---|---|
| Rincewind | `C:\Users\guill\rincewind` | dédiée rincewind | noyau géométrique 3D |
| Renardiere | `C:\Users\guill\renardiere` | dédiée renardiere | outil charpente / modeleurs / GH |
| Sapientpearwood | `C:\Users\guill\sapientpearwood` | dédiée sapientpearwood | CLI devis charpente |
| Demonstrateur | `C:\Users\guill\demonstrateur` | dédiée demonstrateur | SaaS local (FastAPI) intégrant les trois |
| Test corpus | `C:\Users\guill\test_corpus` | dédiée « Prospectiviste » | RAG prospectif construction résiliente (actif) |
| Tiles3d | `C:\Users\guill\Rust\tiles3d` | (instance à confirmer) | jeu 3D Bevy/Rust — terrain infini, hobby sentimental |
| Spectral | `C:\Users\guill\Rust\spectral` | (instance à confirmer) | moteur pseudospectral 2D → météo de Tiles3d ; pont doctorat CFD |
| Hex | (à créer — projet neuf) | dédiée à ouvrir | blocking automatique structuré OpenFOAM : CAO → MAT → blocs → blockMesh ; héritier pwnGrid/eikonalFoam/QMAT |

## Projets abandonnés (vestiges)

`RAGCarto`, `RAGDungeon` (Palais des Connaissances), `RAGWizard` — hors
écosystème, mais fouillés pour idées réutilisables :
voir `Vestiges RAG — leçons.md` (racine du vault).

## Dépendances

```
rincewind  (noyau)
   ↑ pip
renardiere (outil charpente)     sapientpearwood (devis charpente)
   ↑ editable                        ↑ editable
          demonstrateur (SaaS local)
```

## Historique connu

- `rhinoscripts` (ponts Rhino/Grasshopper, Windows-only) : mentionné dans
  TODO_LIST.md rincewind comme ancien/possible dépôt — à clarifier.
- États de tests : rincewind 213 verts, renardiere 16 verts (au 2026-09-06).

## Second cerveau

Les captures (screenshots Rhino, détails DTU, définitions Grasshopper,
snippets) sont triées dans l'app (`http://localhost:8420`) et liées à ces
projets. L'agent du second cerveau propose les liens à partir des scans de
dépôts stockés en base.