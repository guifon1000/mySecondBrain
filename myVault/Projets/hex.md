---
id: 19
description: Blocking automatique structuré pour OpenFOAM — CAO → champ de distance → axe médian (MAT) → topologie multi-blocs → blockMesh, avec couches offset pour la couche-limite. Successeur de pwnGrid, fondé sur Ali et al. 2017.
sert: [Ingénieur CFD]
created: 2026-10-11
---
# Hex

**Blocking automatique structuré pour OpenFOAM** — projet CFD, nom de
famille Discworld (Rincewind, GreatATuin, Sapientpearwood) et double sens
blockMesh : les cellules **hexa**édriques + **Hex**, l'ordinateur pensant
de l'Université invisible.

## La thèse

snappyHexMesh et cfMesh maillent en non-structuré ; pour les écoulements
internes et l'hydrodynamique, le structuré multi-blocs reste supérieur
(précision, orthogonalité, couche-limite) mais son blocking est manuel et
trop lent. Le papier fondateur (**Ali, Dhanasekaran, Tucker, Watson,
Shahpar 2017 — « Optimal multi-block mesh generation for CFD »**, dans
l'inbox) montre que les approches **par axe médian** produisent le
blocking optimal. Le projet recompose un écosystème déjà croisé :

```
CAO → champ de distance (eikonalFoam / fast-marching)
    → axe médian simplifié (QMAT)
    → topologie multi-blocs (MAT → blocs)
    → blockMesh + couches offset couche-limite
```

## Héritage (les trois côtés du triangle, déjà entre nos mains)

- **QMAT** (fork SIGGRAPH 2015) + **blender-mat-addon** : simplification
  de MAT, maillages médians — github guifon1000
- **eikonalFoam** (2018) : solveur OpenFOAM de distribution de distance
  (dérivé de laplacianFoam)
- **pwnGrid** : continuation d'enGrid (mailleur à couches prismatiques
  pour Navier-Stokes) — import gmsh entrepris, jamais un maillage
  OpenFOAM sorti ; leçon : la force brute (300k lignes C++) n'est pas
  la voie, le pipeline par le MAT est la taille d'un hobby

## Montée en difficulté

1. **2D d'abord** : blocking d'une section par MAT 2D, extrusion/
   révolution en 3D — déjà énormément utile
2. **Templates H-O-H** sur les topologies connues (passages internes)
3. **Couches offset couche-limite** multi-blocs, qualité blockMesh
   (orthogonalité près des bords — le MAT la donne naturellement)

## Destinations possibles (faisceau, pas promesse)

- **Levier freelance** : relancer l'hydro OpenFOAM avec un atelier de
  maillage 10× plus rapide (activité suspendue, pas morte)
- **Produit** : « vendre le maillage, pas le mailleur » — service
  productisé (CAO envoyée, polyMesh validé rendu), la mécanique SaaS
  étant déjà le rôle de Demonstrateur. Jamais en premier.

## Liens second cerveau

- **Casquette servie** : Ingénieur CFD.
- **Pouponnière** : « Le même offset sert la couche-limite et la
  trajectoire CNC », « Vendre le maillage, pas le mailleur ».
- **Portes documentaires** : papier Ali (inbox → à classer) ;
  OpenFOAMUserGuide-A4.pdf (grammaire blockMesh) ; User Guide cfMesh
  (l'adversaire) ; jethro_report.pdf, Skuric_Master_2014.pdf (99_a_trier
  de E:/pdf_library, via pdf_cherche).
