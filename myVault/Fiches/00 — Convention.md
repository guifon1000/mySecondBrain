# La convention des fiches (v3)

## L'objet unique

Tout est **fiche** : markdown + frontmatter + wikilinks. Le vault est la
seule source de vérité ; les bases SQLite (pipeline, index) sont des
index dérivés — jetables, reconstruisibles, jamais autorité.

## Les types

- `idee` — une affirmation défendable ; **le titre EST le claim**
  (« La plate-forme est une grammaire », jamais « Note sur… »).
- `note` — fragment, brouillon, coin de table ; naît sans claim et peut
  devenir `idee` quand elle trouve son affirmation.
- `source` — fiche de lecture d'un document ; dérivée et régénérable,
  structurée pour être étoffée ou scindée en fiches `idee`.
- `capture` — screenshot ou PDF capturé (produit par l'app).

Une fiche naît pauvre de droit ; elle ne survit qu'en se reliant.

## L'auteur

`author: user` pour tout. Le vault est en **lecture seule pour l'agent** :
il lit, cherche, juxtapose, propose — il ne crée ni ne modifie jamais une
fiche de lui-même, sauf rédaction sur demande explicite (la fiche naît
alors `user` : c'est celle de l'humain, l'agent n'a fait que la tapper).

## Les liens

- **Confirmés** : écrits par l'humain (à la souris dans l'Archipel,
  ou à la main). Le lien vit dans le corps (`[[wikilink]]`) ou en
  frontmatter typé : `relève:`, `outillé_par:`, `sert:`, `pdf:`.
- **Suggérés** : champ `suggere:` — proposés par l'agent, affichés en
  pointillés, validés ou supprimés par l'humain. L'agent ne crée jamais
  de lien confirmé de lui-même.

## L'espace

`Fiches/{idees,notes,sources,captures}` — le dossier est un confort de
rangement, l'état se lit dans le frontmatter. `Casquettes/` et `Projets/`
gardent leur statut propre ; les casquettes portent `domaines` (leur
pouvoir d'éclairage) et une seule est `active` à la fois.

## La carte

`tools/galaxie.py` → PNG + `Archipel.html`. Une casquette active éclaire
ses fiches ; l'Archipel sert la carte navigable avec recherche et
édition. La carte sert à retrouver, pas à admirer.

## L'agent au quotidien

- **Consultation** : fiches → FTS5 (`querir.py`, `pdf_cherche.py`) →
  PDF direct. Tokens minimaux.
- **Débridage** : OCR des scans muets (E: et vault) pour rendre
  reliables des pages sans texte.
- **Préparation** : rédaction de fiches `source` sur demande, fiches à
  étoffé/scinder.
- **Juxtaposition** : propositions de liens (`suggere:`), jamais des
  pensées.
- **Incarnation** : assistance dans les projets, comme toujours.
