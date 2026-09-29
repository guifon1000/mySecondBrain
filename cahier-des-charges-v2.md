# Second cerveau — Cahier des charges v2 (pouponnière / archipel)

## Prérequis et honest-check

v0 (le noyau : capture → tri → projets/casquettes) tourne ; le rituel n'a pas
encore passé son critère de 14 jours — mais le système d'idées est né de
l'usage réel (fiches, lectures, première couvée). Ce cahier **formalise ce
qui existe** et trace la roadmap de ce qui manque. Il ne remplace ni v0 ni
v1 : v0 est le pipeline, v1 sera la carte interactive, v2 est la pensée.

## Problème à résoudre

Une base documentaire riche (DTU, thèses, livres, articles) et une base de
code vivante (5 dépôts) produisent des idées qui restent dispersées :
notes de lecture au fond d'un dossier, captures non relues, analogies
non faites. Objectif : une **pouponnière** — les documents génèrent des
idées atomiques, les idées se croisent par ce qu'elles partagent, les
croisements s'incarnent dans les projets, le tout visible comme un
archipel.

## Objet : la chaîne complète

```
documents (biblio/) → fiches (_sources/) → idées atomiques (Idees/atomiques/)
    → couvées (croisements proposés par l'agent, validés par l'humain)
    → satellites (Idees/satellites/) → approfondissement (confrontation code
      + docs, enfants, chemin d'incarnation, angles morts)
    → incarnation dans un projet → savoir accumulé
```

## Ontologie (figée en phase 0, voir `myVault/Notes/Architecture du second cerveau.md`)

### Les 4 briques

| Brique | Rôle | Source de vérité |
|---|---|---|
| **Items** | la matière capturée | DB |
| **Fiches + idées** | la pensée | vault |
| **Casquettes** | les domaines d'application | DB + vault |
| **Projets** | l'incarnation | DB + vault |

### Les 4 relations

1. idée **relève de** → casquette (application)
2. idée **est outillée par** → projet (outillage)
3. idée **croise** → idées (couvées)
4. projet **sert** → casquette (pont outillage/métier) — **absente aujourd'hui**

Toute relation : proposée par l'agent, validée par l'humain. Jamais automatique.

### Le cycle de vie d'une idée

`atomique → (couvée) → satellite → (approfondir) → mûre → (code) → incarnée`,
avec sortie `archive/`. Dossier = état. Incarnation tracée (phase 3) : lien
vers le commit/module qui réalise l'idée.

## Implémenté (l'état v2.0, date de ce cahier)

- Bibliothèque humaine : `myVault/biblio/{pdf,img}/` (noms d'origine,
  indexée Obsidian) ; archive système horodatée en `data/archives/`.
- Fiches de lecture dans `_sources/` (exclues d'Obsidian) — la matière
  détaillée, cachée du flux.
- Pouponnière : `Idees/atomiques/` (45), `Idees/satellites/` (2 approfondies :
  maison kiwari, ossature kigumi), `Idees/archive/`, journal `Couvées.md`,
  convention `00 — Convention.md`.
- Le contrat « approfondir » : raciner → confronter (code + docs) → enfants
  atomiques → chemin d'incarnation → angles morts. Pas de code pendant
  l'approfondissement.
- Archipel `tools/galaxie.py` : phares (casquettes, ancrés en périphérie,
  faisceaux de lignée), îlots-idées (diamètre = outillage lexical disponible
  dans les dépôts ; couleur = climat = grande catégorie), satellites
  (couvées), courants de domaines. Les dépôts pèsent sans paraître.

## Roadmap

### Phase 1 — les relations explicites (prochaine couvée)

Frontmatter des idées : `relève: [casquette]` et `outillé_par: [projet]` —
point de départ = lignée + lexical, affinage par curation de l'agent.
Galaxie v0.5 : faisceaux pleins (relève-de) distincts des pointillés
(outillé-par). Aucun effet automatique : la relation informe le tri, elle ne
l'exécute pas.

### Phase 2 — projet sert des casquettes

Frontmatter des projets (+ DB) : `sert: [casquettes]`. Usage : les instances
Pi de chaque projet reçoivent le contexte (« tu sers le couvreur ») et le
rapport de tirage qui va avec. C'est le pont second cerveau ↔ autres agents.

### Phase 3 — l'incarnation trackée

Quand du code implémente une idée : l'idée passe dans un état incarné, avec
référence (commit/module/fichier). La galaxie montre les idées digérées
(masse stabilisée, halo différent). Les îles grossissent de ce qu'elles ont
absorbé — la « croissance lente » du cahier v1, transposée à la pensée.

### Phase 4 — le rétro-minage

Les projets déposent dans l'inbox du second cerveau leurs propres
découvertes (pattern réutilisable, dette, problème sans solution). Les
instances Pi des projets deviennent des sources d'idées — la boucle
bibliothèque → idées → projets → idées se referme.

## Critères de robustesse (mesurables)

- **Traçabilité** : toute idée mène à sa source (fiche → item → document)
  en ≤ 2 clics ; toute idée satellite liste ses parents.
- **Pas de doublon** : avant création d'une idée atomique, l'agent vérifie
  le stock existant (recherche par domaines + termes).
- **Fécondité** : ratio satellites/atomiques surveillé — un stock de 100
  atomiques sans satellite est un échec de couvée, pas une richesse.
- **Portabilité** : le vault seul (sans DB, sans app) doit rester
  compréhensible et utilisable à la main.

## Hors scope (invariants)

- Aucune IA embarquée dans l'app — le sémantique est fait par l'agent, à la
  demande, avec validation humaine.
- Aucun croisement, ancrage ou incarnation automatiques.
- Pas de RAG lourd sur les corpus — la qualité des idées vient de la
  lecture effective, pas d'un index vectoriel.
- Le mode jeu reste derrière : il ne se discute que si v2 est utilisée avec
  plaisir sans lui.