# Cahier des charges v3 — l'environnement créatif (brouillon)

*v3 remplace v2 sur les points de pipeline ; la doctrine (modes de travail,
consultation, promotion) reste. État : brouillon enrichi par la discussion.*

## La vision

Un lieu de travail (Obsidian + Archipel) où des objets de pensée de toutes
natures — idées affirmées, notes de coin de table, références
bibliographiques, fragments de code — cohabitent sous une seule forme,
se relient entre eux et aux projets, et restent visibles d'un coup
d'œil. L'IA y rend **productif** (consultation, OCR, préparation,
juxtaposition) mais ne **pense** plus : la génération d'idées n'est plus
déléguée.

## L'objet fiche

Une seule classe d'objet : **la fiche** — markdown + frontmatter +
wikilinks, comme tout le vault aujourd'hui.

- `type:` distingue la nature : `pensee` (claim affirmé), `note`
  (coin de table, non encore affirmée), `source` (fiche de lecture d'un
  document), `capture` (screenshot, PDF capturé). Projets et casquettes
  gardent leur statut propre.
- Les liens sont **typés** : `source:` (référence biblio), `code:`
  (projet/fichier), `relève:`, `outillé_par:`, `sert:` — visibles dans le
  panneau de la fiche (sections Sources et Code, cliquables : PDF à la
  page, fichier de dépôt) et marquées sur la carte (fiche ancrée vs
  flottante).
- Le cycle de vie se simplifie : une note peut devenir pensee ; l'état se
  lit dans le frontmatter, plus dans le dossier seul (dossiers = confort).

## Le vault comme source unique

Tout vit dans `myVault/`. Les bases SQLite (pipeline, index corpus, index
E:) deviennent des **index dérivés** : jetables, reconstruisibles, jamais
source de vérité. L'app ne capture plus « en base » : elle écrit des
fiches `capture` dans le vault. Doctrine inchangée : l'app ne réécrit
jamais les fiches de l'humain.

## Le rôle de l'IA (redéfini)

- **Le vault est en lecture seule pour l'agent** : tout est `author: user`,
  l'agent ne crée ni ne modifie jamais une fiche. Il lit, cherche,
  juxtapose, propose.
- **Consultation** : les trois étages (fiches → FTS5 → PDF direct).
- **Débridage** : OCR des scans (325 sur E:, 3 dans le vault) pour rendre
  reliables des pages muettes.
- **Préparation** : fiche `source` rédigée par l'agent à la lecture d'un
  document (dérivée, régénérable, non promouvable — ce qu'on promeut,
  ce sont les pensées extraites).
- **Juxtaposition** : l'agent peut **proposer des liens** entre fiches
  (rappel, croisement) — jamais créer des pensées. Toute liaison proposée
  reste une suggestion jusqu'à validation.
- **Assistance d'incarnation** : dans les projets, comme aujourd'hui.

## Ce qui disparaît

- Le mécanisme de génération d'idées (couvées) — et avec lui le rituel de
  ratification, dont c'était la raison d'être.
- Les 44 atomiques `author: agent` : **jetées** (décision de l'humain,
  2026-10-11). Ce qu'on garde, c'est ce qui est approfondi et rattaché au
  réel — une fiche sans matière ni lien n'est pas une richesse.
- Le champ `author: agent` : l'agent n'écrit plus de fiches de pensée.

## Ce qui reste

- Les 5 idées promues (`author: guill`) — intouchables, comme toujours.
- Les 2 satellites (kigumi, kiwari) : riches de chemin d'incarnation —
  à trancher : conservées comme fiches `pensee` du vault, ou archivées.
- Les casquettes (éclairage de la carte, une active), les projets et leur
  suivi, l'index de consultation, `pdf_cherche`, l'Archipel (édition,
  recherche, liens PDF) qui devient l'atelier des fiches.

## Liens : les deux mains (décidé)

- **À la souris** : l'humain relie deux fiches depuis la carte ou le
  panneau ; le lien est confirmé immédiatement.
- **Suggérés** : l'agent marque des liaisons possibles dans une section
  `suggere:` du frontmatter — pointillés sur la carte, dans le panneau
  deux boutons (valider / supprimer). Un seul fichier, deux états de lien.
- L'agent ne crée jamais de lien confirmé de lui-même.

## Structure (décidée)

```
myVault/
  Fiches/
    00 — Convention.md     la doctrine, à côté des fiches
    idees/                 les affirmations (titre = claim)
    notes/                 les fragments de coin de table
    sources/               les fiches de lecture (étoffables, scindables)
    captures/              ce que l'app déposera
  Casquettes/  Projets/  Notes/  biblio/  _sources/  Inbox/
```

Les 2 satellites re-triées vivent dans `Fiches/idees/` avec leurs chemins
d'incarnation conservés. Les fiches `source` de `_sources/` migreront
vers `Fiches/sources/` lors de la refonte de l'app.

## La première fiche de lecture (fait, 2026-10-11)

`Fiches/sources/Ali et al. 2017 — Optimal multi-block mesh generation
for CFD.md` — rédigée par l'agent sur demande explicite, née `author:
user`, structurée pour être étoffée et scindée (méthodes, résultats,
leçons pour Hex, pages de référence, questions ouvertes).

## Travail restant (stack affinée, tri des solutions équivalentes)

1. **lint_fiches.py** (nouveau, première étape) : liens de code périmés
   (détection via git, à la Link), citations vérifiées contre les pages
   PDF (à la Cortex), fiches orphelines. Sécurise les fiches restantes
   pendant la refonte.
2. **Migrer** les fiches de `_sources/` vers `Fiches/sources/` (format v3).
3. **UI de l'Archipel** : relier à la souris, valider/supprimer les liens
   suggérés, créer des fiches, **anti-doublons à la création** (la
   recherche montre les fiches proches avant de créer), afficher les
   liens pdf/code, section « lacunes & contre-arguments » dans les fiches
   source.
4. **Réécrire l'app** : capture → fiches dans le vault, DB = index dérivé.
5. **OCR** des scans muets (325 sur E:, les restants du vault).

### Refusés (tri des équivalents, 2026-10-11)

- Recherche vectorielle (Khoj, qmd) : FTS5 tient ; le jour où une vraie
  question rate, on l'ajoutera.
- Curation automatique du vault, minage transversal de papiers (LENS) :
  de la pensée déléguée — contraire à la v3.
- Backends typés (owletto, Binder) : markdown source + SQLite index, déjà
  notre doctrine.
- Hébergé / multi-agents (Dexio, tracecraft) : tout local, un humain,
  un agent.
- Ranking par usage/récence : mesuré et refusé par Link — néfaste sur des
  fiches durables.
- Capture Telegram : hors plan pour l'instant.

## Critère de réussite (proposition)

Dans un mois d'usage réel : au moins une question de consultation résolue
aux étages 1-2 sans lecture de PDF ; au moins une note de coin de table
devenue pensee puis incarnée ; la carte utilisée pour retrouver, pas pour
admirer. Sinon : simplifier, pas ajouter.
