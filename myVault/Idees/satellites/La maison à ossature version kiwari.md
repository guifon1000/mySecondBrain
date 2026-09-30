---
author: agent
domaines: [paramétrique, bois]
croise: ["[[Kiwari, les proportions précalculées]]", "[[La plate-forme est une grammaire]]"]
couvée: 2026-09-27
approfondi: 2026-09-27
incarnation: rincewind/modelers/maison.py + rincewind/document/timberframes.py (temps 2)
enfants: ["[[Le module comme contrat, la géométrie comme dérivation]]", "[[L'entraxe existe déjà, le module non]]"]
---
# La maison à ossature version kiwari

L'ossature plate-forme est déjà une grammaire répétitive (montants, lisses,
plancher d'étage) ; kiwari montre qu'un module unique précalcule toutes les
pièces par règle de proportion. Croiser les deux : **une maison à ossature
générée entièrement depuis un module proportionnel** — entraxe, section et
longueurs dérivés de la proportion, pas calculés au cas par cas.

Candidat direct pour les modélisateurs `maison` et `comble` de rincewind :
le paramètre d'entrée devient le module, et la grammaire plate-forme
devient l'expansion automatique de ce module.

## Approfondissement (2026-09-27)

### Confrontation au code — ce qui existe déjà

- `rincewind.modelers.maison.creer_maison(poly_sol, hauteur_mur, pente,
  pentes_par_arete)` produit l'**enveloppe** (mesh fermé sol+murs+toiture,
  avec traçabilité `mesh.corrections`). Pas d'ossature : c'est la coque.
- `rincewind.document.timberframes.py` est le **pivot** annoncé : enveloppe →
  liste de TimberFrames (layers mur_0, versant_*, sol...), puis opérations
  temps 2 (coupes, ossature, ep).
- **renardiere `api.solivage(L, W, tilt, entraxe, ...)`** : l'entraxe est
  DÉJÀ un paramètre de modeleur — mais c'est un entraxe de solivage isolé,
  pas un **module kiwari** qui dériverait aussi sections et longueurs.
- L'opération "ossature : remplissage (pannes, montants, chevrons, lisses)"
  est **annoncée** dans la docstring du pivot mais pas implémentée comme
  telle (côté renardiere : `charpente(layers, types, polys, template,
  section)` remplit une charpente périphérique par template).

### Ce que « version kiwari » veut dire concrètement

1. **Un module m** (ex. entraxe montant = 60 cm ou 40,5 cm tatami) est
   l'ENTRÉE ; en dérivent par règles fixes : entraxe des chevrons (m ou
   m/2), sections (règles forfaitaires par portée/proportion), longueurs
   de pièces (trame du poly_sol), ouvertures (multiples de m).
2. **La grammaire plate-forme** est l'expandeur : chaque face mur du mesh
   → cadres (lisses + montants à l'entraxe m) ; chaque versant → chevrons
   à l'entraxe dérivé ; chaque plancher → solivage à l'entraxe dérivé.
3. **La dérivation est une fonction pure** : module + enveloppe → liste de
   pièces avec dimensions. Vérifiable par tableau (fiches constructives
   SB-0053, annexes du livre ossature).

### Chemin d'incarnation (prochain pas, pas codé)

- Étape A : dans renardiere, écrire `ossature_plateforme(entries, module)`
  qui lit le pivot timberframes (types mur/versant/sol) et génère montants/
  chevrons/solives aux entraxes dérivés du module — réutiliser la mécanique
  `_charpente_objets` comme gabarit.
- Étape B : dans rincewind, brancher `creer_maison()` → `mesh_vers_tfs()`
  (existe) pour que la chaîne maison→ossature soit automatisable.
- Étape C : test de vérité = une maison carrée 3×3 modules doit produire
  un décompte de pièces exact (montants = périmètre/entraxe, etc.) et
  correspondre à une fiche constructive du livre SB-0053.

### Angles morts (ce qui n'a pas été vérifié)

- Les règles forfaitaires sections-par-module : je sais qu'elles existent
  dans la pratique DTU 31.2 mais je n'ai pas les valeurs — à sourcer
  (test_corpus ou DTU 31.2 de la bibliothèque).
- La question des ouvertures (multiples de module vs réalisme) : décision
  de conception restante.
- `house/House.py` n'a pas été fouillé (13 lignes, probablement wrapper).