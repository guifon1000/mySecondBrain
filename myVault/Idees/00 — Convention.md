# La pouponnière — convention

## Principes evergreen (d'après Andy Matuschak, adaptés)

1. **Le titre EST le claim** : une idée atomique est titrée comme une
   affirmation défendable ("La rupture de bloc est un phénomène de groupe"),
   jamais comme un sujet ("Note sur les assemblages").
2. **Émancipée de sa source** : l'idée doit se comprendre sans ouvrir le
   document qui l'a fait naître. Le lien de provenance est un bonus, pas un
   soutien.
3. **Orientée concept, pas orientée auteur** : on écrit "La plate-forme est
   une grammaire", pas "L'EC5 dit que la plate-forme est une grammaire".
4. **Densité minimale de liens** : chaque idée doit pouvoir se rattacher à
   au moins un autre concept — une orpheline signale une pensée inachevée.
5. **Création itérative par vagues** : jamais tout d'un coup ; les idées
   s'écrivent par passes motivées (couvées, lectures, projets).

## L'auteur et la promotion (d'après Simback)

- `author: agent` — l'idée est une **proposition**, modifiable, archivable,
  jetable. Rien n'est garanti.
- `author: guill` — l'idée a été **promue** par l'humain : elle capture sa
  pensée. L'agent peut la LIRE, la citer, la croiser, mais **jamais la
  modifier ni la supprimer**. Une idée promue est irrécupérable si on
  l'écrase : l'agent peut re-rechercher un sujet, il ne peut pas re-penser
  une pensée.
- **Rituel de ratification** : par paquets de 5-8, l'agent soumet des idées
  ; pour chaque idée l'humain tranche : **promouvoir / jeter / amender**.
- **Satellites** (couvées validées) : créées `author: agent` avec `croise:`
  rempli ; promues par l'humain selon le même rituel.

## Les autres règles

- **Frontmatter** : `domaines` (vocabulaire libre mais réutilisé, pas de
  synonymes) + `source` (fiche de `_sources/`) + `author` + `croise` /
  `parent` pour les satellites.
- **Frontmatter des casquettes** : `domaines` — c'est leur pouvoir
  d'attraction sur la carte.
- **États** : `atomiques/` → `satellites/` → (`archive/`). Dossier = état.
- **La carte** (`tools/galaxie.py` → PNG + Archipel.html) : phares =
  casquettes, îlots-idées colorés par climat (premier domaine), diamètre =
  outillage disponible dans les dépôts. Calculée au rendu, jamais stockée.

## Ontologie complète

`Notes/Architecture du second cerveau.md` + cahier v2 du dépôt.