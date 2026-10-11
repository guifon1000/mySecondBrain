---
id: 6
description: CLI de devis charpente (devis_charpente) — logique métier en fonctions importables (devis_generation/api.py), types simples, ValueError explicite, génération Excel via templates.
created: 2026-09-27
---
# Sapientpearwood

**Outil devis charpente**. `C:\Users\guill\sapientpearwood`.

- **Rôle** : toute la logique métier du devis en fonctions importables
  (`devis_generation/api.py`) — le CLI (`devis ...`) est un wrapper
  interactif (options, questions, sortie).
- **Modules** : `devis_core`, `devis_generation`, `excel_gener`
  (génération Excel), `templates`, `database_materials` (matériaux),
  `input/`, `tasks/`.
- **Liens écosystème** : même famille métier que renardiere ; références
  DTU charpente ; demonstrateur (installé editable pour le SaaS).