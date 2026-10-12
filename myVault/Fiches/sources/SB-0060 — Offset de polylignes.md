---
type: source
author: user
domaines: [données, géométrie, maths, numérique, usinage]
source: SB-0060
ouvrage: "Liu X.-Z., Yong J.-H., Zheng G.-Q., Sun J.-G., « An offset algorithm for polyline curves », Computers in Industry 58, 2007 (16 p., HAL inria-00518005)"
lie: ["[[Rincewind]]", "[[Renardiere]]"]
---
# Algorithme d'offset pour courbes polylignes (segments + arcs)

Article INRIA/Tsinghua : construire les courbes offset (à distance d) de
polylignes composées de segments de droite et d'arcs, y compris cas
pathologiques : courbes fermées, auto-intersectées, arc de rayon < offset,
segments superposés. Prouvé complet théoriquement.

## Idées principales

- **Structure SEG {point, bulge}** : une polyligne = liste de segments, un
  bulge nul = droite, tan(θ/4) sinon — représentation compacte et universelle
  des géométries 2D "menuiseries" (droites + arcs), très proche des formats
  DXF/usinage.
- **Recette en trois temps** : (1) offsets naïfs de chaque segment → (2)
  assemblage par règles trim/joint selon le type de coins (droite-droite,
  droite-arc, arc-arc) → courbe « untrimmed » → (3) clipping (dual clipping
  + closest-point-pair) → offsets finaux. La preuve (théorème 10) garantit
  qu'on ne perd rien et ne coupe pas trop.
- **Taxonomie des cas difficiles** : faux/points d'intersection vrais
  (TIP/FIP), auto-intersections locales, arcs plus petits que l'offset
  (aucun offset intérieur), superpositions successives — chaque cas a son
  traitement explicite. AutoCAD 2002/2004 échoue sur plusieurs de ces cas ;
  l'algorithme réussit.
- **Application canonique** : génération de **trajectoires d'outil CNC** —
  les offsets du contour = passes d'usinage.
- **Principe généralisable** : beaucoup d'algorithmes d'offset de courbes
  complexes passent par la réduction préalable en polylignes — cet article
  est la brique de base.

## Rattachements

- **Rincewind** : les fonctions d'offset du noyau peuvent être vérifiées
  contre ces cas pathologiques (les figures de l'article = jeux de tests
  tout prêts).
- **Renardiere / casquette Menuisier** : les coupes et débits de bois, les
  trajectoires de défonceuse/CNC sont des offsets de contours 2D —
  applicabilité directe.
- **Casquette Développeur** : exemple remarquable de paper algorithmique
  avec preuves — le genre de référence à garder sous la main avant de
  coder n'importe quel traitement de contours.
