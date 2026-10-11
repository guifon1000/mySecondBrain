---
id: 4
description: Bibliothèque Python de modélisation géométrique 3D (noyau de l'écosystème) — primitives, courbes/surfaces paramétriques, triangulation, générateurs métiers (coques, ailes, maison, comble, zomes), TimberFrame. renardiere en dépend (pip).
created: 2026-09-27
---
# Rincewind

**Noyau géométrique** de l'écosystème. `C:\Users\guill\rincewind`.

- **Rôle** : primitives (points, vecteurs, plans, frames), courbes/surfaces
  (Bézier, splines, UV), extrusion, triangulation, import/export (STL, OBJ,
  JSON, MSH), visualisation matplotlib.
- **Modélisateurs métiers** : `modelers/` (`maison`, `comble`, `tourangelle`,
  zomes...), `TimberFrame` (ossature/charpente d'une face).
- **État** : branche `dev`, 213 tests verts (au 2026-09-06, cf. TODO_LIST.md).
- **Priorité en cours** : solver de comble `resoudre_comble`
  (`rincewind/modelers/comble.py`), fondation du futur optimiseur.
- **Docs clés** : `TODO_LIST.md` (état + priorités, tient aussi le suivi
  renardiere), `TD_RINCEWIND.md` (historique technique).
- **Liens écosystème** : renardiere (CLI qui le consomme), sapientpearwood
  (devis, métier charpente), demonstrateur (SaaS, installations editable).