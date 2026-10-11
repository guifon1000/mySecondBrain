---
id: 5
description: CLI/outil Python de charpente et modélisation geo au-dessus de rincewind — modeleurs geo, charpente, coupes, hbjson, exports 3dm, API importable pour Grasshopper et tout script.
created: 2026-09-27
---
# Renardiere

**Outil charpente / modeleurs** au-dessus du noyau rincewind. `C:\Users\guill\renardiere`.

- **Rôle** : toute la logique en fonctions importables (`renardiere/api.py`),
  types simples entrée/sortie ; le CLI (`renardiere ...`) n'est qu'un wrapper
  (lit JSON, écrit sorties, logge).
- **Domaines** : modeleurs geo, charpente, coupes, hbjson, exports 3dm,
  composants Grasshopper.
- **État** : 16 tests verts (au 2026-09-06).
- **Liens écosystème** : rincewind (dépendance pip), demonstrateur
  (installé editable pour le SaaS), sapientpearwood (même famille métier
  charpente).