---
id: 10
description: Moteur pseudospectral 2D (Rust) en coordonnées polaires — Chebyshev en r, Fourier en θ. Destiné à devenir la météo du jeu Tiles3d. Lien direct avec le doctorat de l'humain (méthodes pseudospectrales).
code_path: C:/Users/guill/Rust/spectral
sert: [Ingénieur CFD, Développeur]
created: 2026-10-11
---
# Spectral

**Moteur pseudospectral 2D** en Rust — l'application de ton doctorat au jeu.
`C:\Users\guill\Rust\spectral`.

- **Domaine** : anneau 2D `[rmin, rmax] × [0, 2π]` — **Chebyshev en r**,
  **Fourier en θ**. C'est le cœur de ta spécialité doctorale : les méthodes
  pseudospectrales.
- **État** : matrices de différentiation (`DiffMatrix` : nodes + matrix),
  faer 0.24 + ndarray, rustfft ; sortie numpy (.npy) pour validation —
  `field.npy`, `laplacian.npy`, `du_dr.npy`... (validation vs Python).
- **Destin** : moteur **météo de Tiles3d** — le jeu de planète procédurale
  recevra une vraie simulation atmosphérique.
- **⚠️ Doc** : `guide.md` est la vraie documentation (session d'apprentissage
  Rust sérieuse sur problème réel) ; pas de README. À consolider.

## Liens second cerveau — le pont est magnifique

- **Casquettes servies** : Ingénieur CFD (ton doctorat), Développeur.
- **La pouponnière a déjà la moitié du pont** : les idées du corpus CFD
  (thèse Wissocq — **LBM**, valve bileaflet, IB-LBM) sont des solveurs de
  **l'autre famille** (cinétique/Boltzmann vs pseudospectral). Contraste
  fertile en attente : *même problème (atmosphère), deux familles de
  solveurs* — quelles idées de l'une transposent dans l'autre ? La méteo
  d'un jeu a des contraintes spécifiques (temps réel, stabilité à long
  pas, rendu visuel avant précision) qui changent les critères de choix.
- **L'index FTS5 couvre la thèse Wissocq** (428 pages) : l'approfondissement
  de ce pont peut interroger le corps même du texte.