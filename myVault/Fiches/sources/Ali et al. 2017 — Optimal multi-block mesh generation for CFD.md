---
type: source
author: user
domaines: [CFD, maillage, numérique]
pdf: "[[Ali et al. 2017 - Optimal multi-block mesh generation for CFD.pdf]]"
relève: "[[Hex]]"
lu: 2026-10-11
---
# Ali et al. 2017 — Optimal multi-block mesh generation for CFD

Zaib Ali, P. Caleb Dhanasekaran, Paul G. Tucker, Rob Watson, Shahrokh
Shahpar — *International Journal of Computational Fluid Dynamics*, 2017.
DOI : 10.1080/10618562.2017.1339351. Cambridge University / Cambridge
Flow Solutions / Rolls-Royce.

## Résumé

Le papier compare des méthodes de **blocking automatique** (génération de
topologie de blocs structurés) à l'aide d'une **estimation d'erreur
adjointe**, puis utilise ce même indicateur pour **adapter la topologie**.
Conclusion : les approches par **axe médian** (medial axis) produisent le
blocking optimal — meilleur alignement avec l'écoulement, taille de
cellules plus uniforme — en particulier pour les écoulements internes.

## Les méthodes comparées

- **d-MAT** : axe médian discret, base Voronoi (algorithme de Dey &
  Zhao 2004), complété par des règles (appendice du papier)
- **TopMaker** : axe médian + règles (Cambridge Flow Solutions)
- **Cartesian fitting** : blocs alignés sur le repère cartésien — le
  maillage ne suit pas l'écoulement, et le resserrage de la couche-limite
  s'étale dans le passage principal
- **Manuel** : topologies façonnées par des praticiens (référence de
  comparaison)

## Résultats — partie 1 : la comparaison

- Deux cas : **prise d'air moteur** (secteur 90°, Mach 0.42, Re ≈ 7×10⁵,
  Spalart-Allmaras, y⁺ ≈ 1) et **rim seal** avec aube.
- Fonction objectif : **perte de pression totale** ; erreur mesurée
  contre un maillage fin (raffinement uniforme).
- Deux schémas testés (**Roe**, **AUSM**) : le classement des topologies
  ne change pas avec le schéma — c'est la topologie qui gouverne
  l'erreur, pas le solveur.
- Erreur normalisée : d-MAT = 1.0, TopMaker ≈ 1.0, Cartesian fitting =
  1.5. Le **manuel gagne parfois, perd parfois** — l'expérience du
  praticien compte autant que la méthode.

## Résultats — partie 2 : l'adaptation de topologie

- L'adjoint localise les zones d'erreur ; on déplace **les nœuds de bloc**
  (pas le maillage), puis on **regénère** le maillage sur la topologie
  adaptée.
- Leçon clé : adapter le maillage entier produit des cellules biaisées
  qui pénalisent les simulations LES/RANS-LES ; extraire la topologie
  et regénérer préserve la qualité.
- Gain mesuré : **−10 %** d'erreur adjointe (rim seal), **−6 %**
  (labyrinthe).

## Ce que ça donne pour Hex

- Le pipeline CAO → champ de distance → MAT → blocs → blockMesh est
  **validé par la littérature** : le MAT est le blocking optimal pour
  les écoulements internes.
- La qualité du blocking peut se juger par adjoint (lourd) ou par
  orthogonalité géométrique près des parois — le MAT la fournit
  naturellement.
- Limites assumées du papier : le MAT suppose un angle d'entrée stable ;
  le manuel bat l'automatique sur certains cas. D'où le chemin de Hex :
  **commencer en 2D**, où l'axe médian est robuste et bien maîtrisé.
- L'adjoint comme *juge* de topologie est un outillage trop lourd pour
  un premier pas — à garder pour la validation finale.

## Pages de référence (numéros PDF)

- p. 3 : état de l'art du blocking (axe médian, paving/plastering,
  champs croisés)
- pp. 3-6 : méthodes et métrique de Riemann (estimation d'erreur par
  arête)
- pp. 7-9 : cas de la prise d'air, tableau des quatre topologies
- pp. 13-15 : adaptation de topologie (rim seal, labyrinthe)
- p. 16 : conclusion

## Questions ouvertes

- L'adjoint est-il nécessaire, ou la qualité géométrique suffit-elle
  pour un usage hobby puis freelance ?
- Quel algorithme exact pour le MAT 2D de Hex (Voronoi discret ?
  Q-MAT — déjà forké — produit-il des blocs exploitables par blockMesh
  ou seulement des maillages médians ?)
- Comment injecter les couches couche-limite (offsets) *dans* le
  blocking MAT sans casser son orthogonalité ?
