# Cahier des charges v5 — l'arbre (brouillon)

*v5 sort des mécanismes bâtis pour la v4 (chantiers, ordonnances, panier)
et repart de la métaphore fondatrice. Ce cahier grave la vision et les
décisions prises en discussion — rien n'y est figé, les ouverts sont
listés à la fin. Issu des échanges d'octobre.*

## La vision

Le truc est un **arbre**.

- **La canopée** — les extrémités (rameaux, feuilles) : ce que l'humain
  voit et manipule. Les feuilles sont des fiches, des documents, des
  notebooks — du markdown lisible, dans le vault.
- **Le bois** — le domaine de l'IA : plus abstrait, plus bas niveau, là
  où les idées se recoupent. L'humain voit la silhouette, jamais les
  fibres.
- **Les petites branches** regroupent les idées similaires ; **le tronc**
  porte les éléments de plus bas niveau — les motifs générateurs qui
  traversent tout.

Un seul arbre, qui **se redessine au gré du travail** : les bourgeons
activés au cours d'une session en changent la silhouette. L'arbre n'est
pas dessiné d'avance — il pousse.

## La scène fondatrice (Arunda)

> J'ouvre l'arbre, je crée une feuille « recréer le Mafell Arunda, un
> gabarit à queue d'aronde pour défonceuse et bague à copier ». Soit
> l'IA fait automatiquement le lien avec les offsets CNC, soit je rentre
> le mot-clé « offsets ». Je peux aussi aller sélectionner une feuille
> sur le block mesh, car je me dis que le solver eikonal fait un offset.
> L'agent m'écrit un markdown éditable, sauvable comme feuille, jetable.
> J'obtiens une nouvelle feuille, placée au bon endroit de la canopée
> par l'agent, et que je pourrais donner à un agent de code.

Ce que la scène définit :

- **La feuille naît d'une tâche** — et mûrit en savoir une fois le
  travail fait. Même feuille, deux âges.
- **Trois façons de greffer** : l'agent suspend automatiquement ; le
  mot-clé pose dans le bois ; la traversée manuelle d'une autre branche.
- **Le brouillon de l'agent** est un objet propre, jetable, adoptable.

## Les trois âges (lignification)

1. **Bourgeon** — écrit par un agent (compagnon, agent de session,
   agent de code), markdown éditable, **jetable**. Il ne devient feuille
   que si l'humain l'adopte en l'éditant.
2. **Feuille** — adoptée par l'humain, durable, dans le vault.
3. **Bois** — le motif qui traverse plusieurs feuilles, **détecté par
   l'IA, nommé par l'humain**. La détection sans le nom ne durcit pas ;
   le nom sans la traversée de feuilles n'existe pas.

Règle absolue : **tout passe par le bourgeon.** Aucun agent n'écrit
jamais dans la canopée — y compris l'agent de code : son travail revient
en bourgeons pendus à la feuille-commande, à adopter. La doctrine des
deux mains devient un cycle de végétation.

## Les greffes

Une feuille pend à **une seule branche** — là où vit la tâche. Les
recoupements transversaux sont des **greffes** : fibres visibles vers
d'autres branches. L'arbre garde sa silhouette hiérarchique ; le graphe
réel (embrouillé, multi-domaine) vit dessous et s'y lit par les greffes.
Le bois est une **lecture** du graphe, recalculable — jamais l'état du
monde.

## Les liens : deux régimes

L'humain choisit : laisser l'agent **chercher et proposer** les liens
(au risque du bruit), ou **forcer** les liens lui-même. Au moment de la
greffe, l'agent peut souffler la traversée : « ce motif existe aussi
là-bas — veux-tu voir ? » C'est le bois qui fait couler la sève :
proposer le croisement au moment où la feuille se greffe, pas après.

## Ce qui reste ouvert

- **Le redessin** : qu'est-ce qui fait bouger la silhouette ? Les
  bourgeons activés, la fréquence de traversée des branches — à préciser.
- **Le rituel du tronc** : comment l'humain nomme un motif détecté,
  combien de feuilles avant que le bois durcisse.
- **La vue du bois** : combien de structure l'humain voit — silhouette
  seulement, ou branches explorables ?
- **La migration** : ce que deviennent les objets v3/v4 (fiches,
  chantiers, ordonnances, panier) dans le vocabulaire feuille/branche/
  bourgeon — délibérément non tranché tant que la vision n'est pas
  stable.

## Le test qui reste valable

Si l'application disparaît, **la canopée reste** : feuilles en markdown
dans le vault. Le bois se regénère — il est dérivé, jetable, recomputé
par l'IA tant qu'il y a des feuilles à lire.