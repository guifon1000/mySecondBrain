---
type: idee
author: user
domaines: [paramétrique, bois]
incarnation: rincewind/modelers/maison.py + rincewind/document/timberframes.py (temps 2)
travaux: 2026-09-27
suggere: ["[[L'ossature à joints générés (kigumi plate-forme)]]"]
---
L'ossature plate-forme est déjà une grammaire répétitive (montants, lisses, plancher d'étage). Kiwari montre qu'un module unique précalcule chaque pièce par règle de proportion.

Croisement : **une maison à ossature générée entièrement depuis un module proportionnel**. Entraxe, section et longueurs se dérivent de la proportion, au lieu d'être calculés au cas par cas.

Candidat direct pour les modeleurs `maison` et `comble` de rincewind : le paramètre d'entrée devient le module, et la grammaire plate-forme devient l'expansion automatique de ce module.

## Approfondissement (2026-09-27)

### Le code existant

- `rincewind.modelers.maison.creer_maison(poly_sol, hauteur_mur, pente, pentes_par_arete)` produit l'enveloppe (maillage fermé sol, murs et toiture, avec traçabilité `mesh.corrections`). Ce n'est pas une ossature : c'est la coque.
- `rincewind.document.timberframes.py` est le pivot : enveloppe → liste de TimberFrames (layers mur_0, versant_*, sol…), puis opérations temps 2 (coupes, ossature, ep).
- `renardiere.api.solivage(L, W, tilt, entraxe, ...)` : l'entraxe est déjà un paramètre de modeleur, mais isolé. Ce n'est pas un module qui dériverait aussi les sections et les longueurs.
- L'opération « ossature : remplissage (pannes, montants, chevrons, lisses) » est annoncée dans la docstring du pivot, sans être implémentée comme telle. Côté renardiere, `charpente(layers, types, polys, template, section)` remplit une charpente périphérique à partir d'un gabarit.

### Ce que « version kiwari » veut dire

1. **Un module m** (ex. entraxe de montant, 60 cm par exemple) est l'entrée. Des règles fixes en dérivent : entraxe des chevrons (m ou m/2), sections (règles forfaitaires selon portée et proportion), longueurs de pièces (trame du poly_sol), ouvertures (multiples de m).
2. **La grammaire plate-forme** est l'expandeur : chaque mur donne des lisses et des montants à l'entraxe m ; chaque versant, des chevrons à l'entraxe dérivé ; chaque plancher, un solivage à l'entraxe dérivé.
3. **La dérivation est une fonction pure** : module + enveloppe → liste de pièces cotées. Elle se vérifie par tableau (fiches constructives SB-0053, annexes du livre ossature).

### Chemin d'incarnation (non codé)

- **A** : dans renardiere, écrire `ossature_plateforme(entries, module)`. Lire le pivot timberframes (types mur, versant, sol) et générer montants, chevrons et solives aux entraxes dérivés. Réutiliser la mécanique de `_charpente_objets` comme gabarit.
- **B** : dans rincewind, brancher `creer_maison()` → `mesh_vers_tfs()` (existant) pour automatiser la chaîne maison → ossature.
- **C** : test de vérité. Une maison carrée de 3×3 modules doit donner un décompte exact (montants = périmètre / entraxe, etc.) et correspondre à une fiche du livre SB-0053.

### Angles morts

- Les règles forfaitaires de section par module existent dans la pratique du DTU 31.2, mais les valeurs ne sont pas sourcées ici. À chercher dans le test_corpus ou dans le DTU 31.2 de la bibliothèque.
- Les ouvertures : multiples du module, ou réalisme ? Décision de conception restante.
- `house/House.py` n'a pas été examiné (13 lignes, probablement un wrapper).
