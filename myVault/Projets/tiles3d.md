---
id: 9
description: Jeu 3D Rust/Bevy 0.16 — exploration de terrain infini (projection gnomonique, tuiles 3000×1500, précision subpixel), agents autonomes, physique Rapier. Projet hobby auquel l'humain tient beaucoup ; vibe-coding à reprendre en main.
code_path: C:/Users/guill/Rust/tiles3d
sert: [Développeur, Geek]
created: 2026-10-11
---
# Tiles3d

**Jeu de terrain infini** Rust + Bevy 0.16 + Rapier3D. `C:\Users\guill\Rust\tiles3d`.
Projet **hobby, sentimental** — le vibe-coding a pris le dessus, à reprendre en main.

- **Monde** : terrain infini par projection **gnomonique** (coordonnées
  géographiques ↔ espace 3D), grille de tuiles 3000×1500 avec 51 divisions
  subpixel, régénération en temps réel quand le joueur s'éloigne (> 37 tuiles
  du centre) — position synchronisée à travers les recréations.
- **Joueur** : WASD + souris, saut physique, suivi subpixel, balise de tuile.
- **Agents autonomes** : déplacements aléatoires, physique Rapier, collecte
  d'objets et inventaire.
- **Structure src/** : `terrain/`, `planisphere/`, `player/`, `game_object/`,
  `collision/`, `landscape.rs`, `camera.rs`, `ui.rs`.
- **⚠️ Hygiène** : le dépôt traîne `CLAUDE.md.bak`, `CLAUDE_noise.md`,
  `ask.py`, `chunk.md`, `coaching.md`, `answer.md`, `unused_functions.md` —
  sédiments du vibe-coding. Un premier chantier sain : purger et stabiliser
  une doc (CLAUDE.md unique + README à jour).
- **Projet compagnon** : Spectral (moteur pseudospectral destiné à devenir la
  **météo du jeu**) — voir sa note.

## Liens second cerveau

- **Casquettes servies** : Développeur, Geek.
- **Idées pouponnière pouvant peser** : à semer — la projection gnomonique
  et la géométrie sphérique/tuiles rejoignent le climat `géométrie` ;
  la météo Spectral fera le pont avec le climat `CFD`.