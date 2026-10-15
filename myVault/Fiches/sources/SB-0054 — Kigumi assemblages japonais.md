---
type: source
author: user
domaines: [assemblages, géométrie, mécanique, numérique]
source: SB-0054
pdf: "bois-101.pdf"
lie: ["[[Renardiere]]", "[[Rincewind]]", "[[L'ossature à joints générés (kigumi plate-forme)]]"]
---
# Kigumi — l'art des assemblages japonais sans métal

Thèse sur le Kigumi (assemblage bois sans clous ni vis) : histoire, principes,
étude mécanique par éléments finis, prototypage (bois + impression 3D),
intégration dans l'architecture durable.

## Idées principales

- **Kiwari** : le système de proportions japonais qui précalcule la taille
  des pièces à partir du module — une « grammar of construction » pré-
  paramétrique, très proche d'un modèle géométrique paramétrique moderne.
- **Typologie des joints** : tsugite (jonctions longitudinales) et shiguchi
  (assemblages d'angle) — familles complètes, réutilisables comme catalogue.
- **Outil logiciel Tsugite** (UIST'20) : conception interactive de joints
  d'angle générés computationnellement — preuve que la génération de joints
  est un problème de géométrie solvable par algo.
- **Étude mécanique** : modélisation Catia V5 + EF sur assemblages réels
  (chêne), comparaison flèches/contraintes von Mises avec calculs
  théoriques — méthodologie de validation d'assemblages semi-rigides.
- **Prototypage comparé** : chêne usiné vs impression 3D — le geste de
  l'artisan reste décisif ; l'interview menuisier porte sur la conception.
- **Lien durabilité** : modularité, métabolisme architectural (démontabilité,
  réemploi) — le joint sans métal = réparable et démontable, argument de
  résilience.

## Rattachements

- **Test corpus** : exactement le type de source que le corpus « savoir-faire
  traditionnels × durabilité » recherche (référencé UNESCO ; bibliographie
  riche en fin de thèse — mine de sources).
- **Renardiere** : les assemblages tenon-mortaise/embrèvements calculés
  dans l'Eurocode 5 (cf. note EC5) pourraient être *générés* — le joint est
  une géométrie paramétrable.
- **Rincewind** : la génération de joints d'angle est un problème de CSG/
  soustraction de solides paramétrique — dans les cordes du noyau.
