---
author: agent
domaines: [assemblages, paramétrique, durabilité]
croise: ["[[Générer un joint d'angle computationnellement]]",
         "[[Le joint sans métal est réversible]]",
         "[[La plate-forme est une grammaire]]"]
couvée: 2026-09-27
approfondi: 2026-09-27
incarnation: renardiere temps 2 (opération "ossature" sur le pivot timberframes) + rincewind/geometry/TimberFrame.py (cut_by_plane)
enfants: ["[[Un joint est une recette de plans de coupe]]", "[[Le connecteur disparaît du devis]]"]
ressort: "[[L'offset du contour est la trajectoire CNC]] (couvée archivée, réalisée par cette idée)"
---
# L'ossature à joints générés (kigumi plate-forme)

L'ossature plate-forme assemble ses pièces par clouage et plaques
métalliques : solide, mais irréversible et pont thermique à chaque
connexion. Le kigumi montre qu'un catalogue de joints géométriques suffit
à tenir une structure entière. Croiser : **chaque rencontre de pièces de
l'ossature (lisse/montant, chevron/panne, solive/lisse basse) reçoit un
joint généré paramétriquement** — soustraction de solides sur les deux
pièces, usiné au CNC — au lieu d'un connecteur acheté.

Résultat : une ossature **démontable, sans métal**, directement usinable
depuis sa géométrie — et chaque joint reste dans le vocabulaire tsugite/
shiguchi plutôt que réinventé par pièce.

## Approfondissement (2026-09-27)

### Confrontation au code — la brique clé est déjà là

- **`rincewind/geometry/TimberFrame.py` : `bar.cut_by_plane()` et
  `add_cutting_plane()`** — les barres sont des solides coupables par des
  plans, et `barres_peripheriques()` applique DÉJÀ des coupes d'extrémité
  par les plans de flanc des barres adjacentes (les « coupes façon zomes »).
  Autrement dit : **le système actuel fabrique déjà des joints
  élémentaires** (coupes droites d'emboîtement) sans les nommer ainsi.
- Un joint kigumi dans ce modèle = une **recette paramétrée de plans de
  coupe** appliqués aux deux pièces qui se rencontrent. Tenon-mortaise
  simple = une poignée de plans. Pas de nouvelle géométrie à inventer :
  un catalogue à écrire.
- **Côté renardiere** : l'opération temps 2 `coupes(layers, types, polys)`
  produit barres + axes utiles ; le générateur de joints serait une
  opération sœur (`joints(...)`) sur le même pivot `timberframes.py`.
- **Argument thermique réel** : les plaques métalliques en façade sont des
  ponts thermiques documentés ; le joint bois-bois les supprime — croisement
  avec « L'étanchéité à l'air est une continuité » (continuité matériau =
  continuité isolant).

### Chemin d'incarnation (3 étapes, pas codé)

- **Étape A — un seul joint, le plus simple** : l'angle bridle
  (enfourchement) de la thèse Kigumi = 2-3 plans de coupe par pièce.
  Prototype : recette + application à une rencontre lisse/montant du pivot.
- **Étape B — l'ossature** : parcourir les croisements des layers
  (lisses × montants, chevrons × pannes) et appliquer les recettes ; les
  décompte s'obtient comme dans `_coupes_objets` (longueurs utiles).
- **Étape C — validation** : protocole de la thèse Kigumi (modélisation,
  EF, flèches + von Mises) appliqué au joint généré, comparé à un
  assemblage pointé EC5 via Kser (« Kser, l'assemblage est un ressort
  paramétrable »).

### Conséquences en cascade

- **Devis** : les lignes « connecteurs » (pointes, plaques Simpson) se
  réduisent, une ligne « usinage » apparaît — voir l'enfant
  « Le connecteur disparaît du devis ».
- **Fabrication** : chaque joint = des coupes = trajectoires — la couvée
  archivée « Trajectoires CNC des joints kigumi » est réalisée par cette
  idée, pas à côté.
- **Durabilité** : démontable/réparable par construction (« Le joint sans
  métal est réversible »).

### Angles morts (ce qui n'a pas été vérifié)

- **La poche aveugle** : `cut_by_plane` retire un demi-espace ; une
  mortaise non traversante exige une soustraction bornée. Vérifier si le
  noyau a une primitive de poche (séquence de 4 plans + fond, ou booléen
  boîte) — c'est LE point technique qui décide de la facilité.
- **Rigidité des joints générés** : aucune valeur Kser joint-généré vs
  pointeau — à mesurer (protocole EF de SB-0054) ou à sourcer (littérature
  citée par la thèse : Moradei 2018, Fang 2018 sur les joints traditionnels
  moment-résistants).
- **Perte de section** : chaque recette entame la pièce — les vérifications
  EC5 (cisaillement, traction perpendiculaire, rupture de bloc) restent à
  refaire sur section entamée.
- **Tolérances d'usinage** : le kigumi traditionnel exige la précision du
  outil ; les tolérances CNC domestiques vs chantier n'ont pas été
  évaluées.