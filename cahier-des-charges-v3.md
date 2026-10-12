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

- Le mécanisme de génération d'idées (couvées, qu'elles soient rigoureuses
  ou sauvages).
- Les 44 atomiques `author: agent` : **archivées** (dossier archive/,
  retrouvables) plutôt que supprimées — à confirmer.

## Ce qui reste

- Les 5 idées promues (`author: guill`) — intouchables, comme toujours.
- Les 2 satellites (kigumi, kiwari) : riches de chemin d'incarnation —
  à trancher : conservées comme fiches `pensee` du vault, ou archivées.
- Les casquettes (éclairage de la carte, une active), les projets et leur
  suivi, l'index de consultation, `pdf_cherche`, l'Archipel (édition,
  recherche, liens PDF) qui devient l'atelier des fiches.

## Questions ouvertes (en discussion)

1. Sort des 44 atomiques (archivées ?) et des 2 satellites (conservées ?).
2. La distinction `author: agent|guill` a-t-elle encore un sens pour les
   nouvelles fiches — toutes de l'humain désormais ?
3. Vocabulaire des types : `pensee / note / source / capture` — suffisant ?
4. L'app : réécrire la capture (screenshots, watcher) pour produire des
   fiches dans le vault, ou la geler telle quelle en attendant ?
5. Critère de réussite : comment saura-t-on que l'environnement créatif
   « marche » ? (proposition : une note de coin de table reliée et
   retrouvée en moins de deux minutes ; une consultation résolue sans
   ouvrir de PDF ; une idée promue incarnée dans un projet)

## Critère de réussite (proposition)

Dans un mois d'usage réel : au moins une question de consultation résolue
aux étages 1-2 sans lecture de PDF ; au moins une note de coin de table
devenue pensee puis incarnée ; la carte utilisée pour retrouver, pas pour
admirer. Sinon : simplifier, pas ajouter.
