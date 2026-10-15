---
type: idee
author: user
domaines: [assemblages, paramétrique, durabilité]
incarnation: renardiere temps 2 (opération "ossature" sur le pivot timberframes) + rincewind/geometry/TimberFrame.py (cut_by_plane)
travaux: 2026-09-27
suggere: ["[[La maison à ossature version kiwari]]"]
lie: ["[[SB-0054 — Kigumi assemblages japonais]]"]
---
L'ossature plate-forme se cloue et se visse à des plaques métalliques : solide, mais irréversible, et pont thermique à chaque connexion. Le kigumi montre qu'un catalogue de joints géométriques suffit à tenir une structure entière.

Croisement : **chaque rencontre de pièces (lisse/montant, chevron/panne, solive/lisse basse) reçoit un joint généré paramétriquement**, soustraction de solides sur les deux pièces, usinage CNC, au lieu d'un connecteur acheté.

Résultat : une ossature **démontable, sans métal**, usinée directement depuis sa géométrie. Chaque joint reste dans le vocabulaire tsugite-shiguchi.

## Approfondissement (2026-09-27)

### Le code a déjà la brique clé

- `rincewind/geometry/TimberFrame.py` : `bar.cut_by_plane()` et `add_cutting_plane()`. Les barres se coupent par des plans, et `barres_peripheriques()` applique déjà des coupes d'extrémité par les plans de flanc des barres voisines. Le système fabrique donc des joints élémentaires (coupes droites d'emboîtement) sans les nommer.
- Un joint kigumi est une recette de plans de coupe appliquée aux deux pièces. Un tenon-mortaise simple se réduit à quelques plans. Rien de géométriquement nouveau : il reste à écrire le catalogue.
- Côté renardiere : l'opération temps 2 `coupes(layers, types, polys)` produit barres et axes ; le générateur serait une opération sœur `joints(...)` sur le même pivot `timberframes.py`.
- Argument thermique : les plaques métalliques en façade créent des ponts thermiques documentés ; le joint bois-bois les supprime. Lien avec « L'étanchéité à l'air est une continuité ».

### Chemin d'incarnation (non codé)

- **A, un joint, le plus simple** : l'enfourchement (bridle joint) de la thèse Kigumi, 2 à 3 plans de coupe par pièce. Prototype : une recette appliquée à une rencontre lisse/montant du pivot.
- **B, l'ossature** : parcourir les croisements des layers (lisses × montants, chevrons × pannes) et appliquer les recettes. Le décompte suit `_coupes_objets` (longueurs utiles).
- **C, validation** : protocole de la thèse Kigumi (modélisation, EF, flèche et von Mises) sur le joint généré, comparé à un assemblage pointé selon EC5 via Kser (« Kser, l'assemblage est un ressort paramétrable »).

### Conséquences

- **Devis** : les lignes connecteurs (pointes, plaques) se réduisent ; une ligne usinage apparaît (« Le connecteur disparaît du devis »).
- **Fabrication** : chaque joint est un jeu de coupes, donc de trajectoires. La couvée « Trajectoires CNC des joints kigumi », archivée, est réalisée par cette idée.
- **Durabilité** : démontable et réparable par construction (« Le joint sans métal est réversible »).

### Angles morts

- **La poche aveugle** : `cut_by_plane` retire un demi-espace ; une mortaise non traversante exige une soustraction bornée. Vérifier si le noyau dispose d'une primitive de poche (quatre plans et un fond, ou booléen de boîte). C'est le point technique qui décide de la facilité.
- **Rigidité** : aucune valeur de Kser pour les joints générés. À mesurer (protocole EF de SB-0054) ou à sourcer (Moradei 2018, Fang 2018 sur les assemblages traditionnels à moment).
- **Section entamée** : chaque recette retire de la matière. Cisaillement, traction perpendiculaire et rupture de bloc sont à revérifier sur section réduite.
- **Tolérances** : le kigumi traditionnel exige la précision de l'outil. Les tolérances d'une CNC domestique face aux exigences de chantier restent à évaluer.
