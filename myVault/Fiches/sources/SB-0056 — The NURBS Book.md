---
type: source
author: user
domaines: [géométrie, paramétrique]
source: SB-0056
ouvrage: "Piegl L. & Tiller W., « The NURBS Book », 2e éd., Springer 1997 (649 p.) — la référence NURBS"
lie: ["[[Rincewind]]"]
---
# The NURBS Book

La référence mondiale des NURBS (Non-Uniform Rational B-Splines) : théorie,
centaines d'algorithmes en pseudocode C, bibliothèque Nlib — standard
IGES/STEP/PHIGS pour la représentation géométrique.

## Idées principales

- **NURBS = forme unifiée** : représente à la fois les formes analytiques
  (cercles, coniques, quadriques) et les formes libres (coques de navire,
  carrosseries) avec un seul formalisme — c'est pourquoi le noyau
  géométrique de rincewind est « parlé en NURBS ».
- **La hiérarchie Bézier → B-spline → NURBS** : le livre construit tout à
  partir des polynômes de Bernstein ; comprendre cette généalogie (degrés,
  élévation/réduction) éclaire toutes les opérations.
- **Les algorithmes fondamentaux** : insertion de nœuds (le couteau suisse —
  subdivision, isocourbes, évaluation), raffinement/retrait de nœuds,
  élévation/réduction de degré — et leur stabilité numérique.
- **Constructions de surfaces** : règles, révolution, balayage, skinned
  (lofting), Coons, Gordon — le catalogue des surfaces utiles au modelage
  (coques, ailes).
- **Fitting** : interpolation locale/globale, moindres carrés contraints —
  pour passer de données mesurées (nuages de points) à des surfaces.
- **Modification de forme** : repositionnement de points de contrôle,
  modification de poids, warping/flattening/bending, modification pilotée
  par contraintes — le socle d'une UI de modelage interactive.
- **Standard & échange** : IGES/STEP — le format d'échange est indissociable
  du modèle géométrique.

## Rattachements

- **Rincewind** : lecture de chevet pour le noyau — Bézier/splines/UV
  surfaces y sont implémentés ; les chapitres 5-6 (algorithmes
  géométriques) et 8 (surfaces communes : coque, révolution) nourrissent
  directement les modelers (hull, ailes).
- **Renardiere** : exports 3dm/Rhino = NURBS ; toute interop GH ↔ Python
  passe par ce formalisme.
- **Casquette Développeur** : le pattern « algorithme + test de précision
  + illustration calculée » du livre est un modèle d'ingénierie de
  bibliothèque géométrique.
