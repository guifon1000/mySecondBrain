# Architecture du second cerveau

> Ontologie figée le 2026-09-27 (phase 0). Détail complet et roadmap dans
> `cahier-des-charges-v2.md` du dépôt `mySecondBrain`.

## Les 4 briques

| Brique | Rôle | Source de vérité | Où |
|---|---|---|---|
| **Items** | la matière capturée (PDF, code, notes, captures) | DB (`secondbrain.db`) | app + notes de tri dans le vault |
| **Fiches + idées** | la pensée : fiches de lecture, idées atomiques, satellites | vault | `_sources/`, `Idees/` |
| **Casquettes** | les domaines d'application — *qui* sert | DB + vault | `Casquettes/`, phares de la carte |
| **Projets** | l'incarnation — *avec quoi* on sert | DB + vault | `Projets/`, dépôts scannés |

## Les 4 relations

1. Une idée **relève de** → casquette(s) : cette idée concerne ce rôle.
2. Une idée **est outillée par** → projet(s) : cette idée peut être incarnée avec les briques de ce dépôt.
3. Une idée **croise** → d'autres idées : les couvées (recettes).
4. Un projet **sert** → casquette(s) : le pont entre l'outillage et le métier.

Toute relation est **proposée par l'agent, validée par l'humain** — jamais automatique.

## Le cycle de vie d'une idée

```
atomique ──couvée──> satellite ──approfondir──> mûre ──code──> INCARNÉE
    │
    └── archive/ (retirée)
```

- **atomique** (`Idees/atomiques/`) : un ingrédient, une phrase, des domaines.
- **satellite** (`Idees/satellites/`) : une recette — croise ≥ 2 idées de base.
- **mûre** : approfondie (confrontation au code + aux docs, enfants, chemin
  d'incarnation, angles morts).
- **incarnée** : le code existe — l'idée devient savoir accumulé du projet
  (état à tracer, phase 3 de la roadmap).
- **archive** (`Idees/archive/`) : retirée, jamais supprimée.

## Les règles de robustesse

1. **Une brique, une source de vérité** : le vault possède la pensée, la DB
   possède le pipeline. L'agent est le moteur sémantique — il n'est jamais
   stocké, il est reconstituable de n'importe quelle machine avec le vault
   + la DB.
2. **Proposé par l'agent, validé par l'humain** — jamais de croisement,
   d'ancrage ou d'incarnation automatiques.
3. **La bibliothèque est organisée, les idées circulent nues** : les fiches
   restent cachées (`_sources/`), les idées portent leur climat, pas leur
   document.
4. **Fécondité avant volume** : le stock d'idées n'est pas un devoir ; les
   orphelines sont signalées, pas noyées.
5. **Doctrine de lecture** : lecture profonde à la demande (pas de mining
   systématique) ; un index de consultation (RAG) peut la porter — outil de
   l'agent, artefact dérivé jetable, jamais fonctionnalité de l'app.
   Voir cahier v2, section dédiée.