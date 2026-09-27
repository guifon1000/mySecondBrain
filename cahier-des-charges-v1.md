# Second cerveau — Cahier des charges v1 (carte / archipel)

## Prérequis

v1 ne démarre que si les critères de `cahier-des-charges-v0.md` (≥ 10 sessions / 14 jours, durée médiane ≤ 10 min, inbox stable) sont **mesurés dans la table `sessions`**. v1 est une couche de satisfaction ajoutée sur un noyau qui fonctionne déjà — elle ne doit jamais devenir la raison de repousser ou compliquer v0.

## Objectif

Rendre le rituel de tri quotidien agréable ("kiffant") plutôt que corvée, en rendant visible la progression des projets plutôt que le simple acte de tri.

## Principe général de la carte

- Une carte 2D où chaque item non lié ("débris") a une position, et chaque projet validé ("île") a une position fixe.
- La position reflète la proximité sémantique (embeddings déjà calculés en v0), pas une découverte de nouveaux liens — la carte est une couche d'affichage au-dessus de scores déjà calculés en v0, elle ne réintroduit jamais de détection automatique de lien.

## Mécanique

### Îles (projets)
- Position fixe, définie une seule fois à la création (à l'endroit où se trouvait l'amas de débris qui l'a fait naître, pour éviter tout saut visuel).
- Ne bouge plus jamais après création — nœud épinglé (masse infinie) dans la simulation de forces.

### Débris (items non liés)
- Simulation de forces (type `d3-force`) : répulsion mutuelle entre tous les débris, attraction faible entre débris sémantiquement proches, attraction très faible vers les îles pour lesquelles le score est non nul.
- **Position initiale des débris** (idée héritée de RAGDungeon/Palais des Connaissances, fouille du 2026-09-27, voir `myVault/Vestiges RAG — leçons.md`) : dérivée d'une réduction de dimension (UMAP ou PCA) sur les embeddings — les débris naissent groupés par affinité naturelle au lieu d'un spawn aléatoire, et la simulation de forces n'a plus qu'à raffiner. À ne considérer qu'en v1, sur critère d'usage.
- **Deux seuils distincts** (seuils calibrés sur les données réelles de v0, pas posés à l'aveugle) :
  - Seuil bas → dérive visuelle vers une île (signal doux, sans conséquence, visible tôt).
  - Seuil haut → suggestion active de lien dans le flux de tri (l'utilisateur doit trancher).

### La tempête *(v1.1 — pas dans la première livraison)*
- Déclenchée à l'ouverture de la session de tri si de nouveaux items sont arrivés depuis la dernière visite.
- N'affecte que les débris libres (jitter/vitesse aléatoire injectée puis relâchée) ; les îles restent fixes.
- Sert de signal visuel du "nouveau depuis hier", cohérent avec le rituel quotidien.

### Croissance des îles — deux vitesses
- **Immédiate** : chaque lien validé ajoute un repère visuel instantané (accusé de réception).
- **Lente** : un score d'engagement cumulé, compté uniquement quand la fenêtre du projet a le focus ET qu'il y a une frappe active (pas un onglet simplement ouvert). C'est ce score, pas le nombre de liens, qui fait grossir la structure principale de l'île — pour éviter d'optimiser le volume de tri plutôt que le temps investi.
- **Vigilance en usage** : ce mécanisme crée une incitation à garder un projet ouvert. À observer ; si l'effet pervers domine (frappe faite pour frapper), le score est recalibré (par exemple pénalité par session, plafond journalier).

### Éléments archivés (non liés) *(v1.1)*
- Ne disparaissent pas : ils "coulent" visuellement vers un coffre/une zone hors du champ de vision courant, récupérables si besoin.

## Priorité de livraison v1

Le cœur de v1 est **minimal** : carte force + débris + îles + clic sur un débris → aperçu, scores, validation/archivage. La tempête, le coffre et les habillages secondaires sont des incréments *après* que le cœur est utilisé. Chaque incrément doit se justifier par l'usage, pas par l'envie de construire.

## Parcours d'interaction

1. Clic sur un débris → aperçu de l'item + scores top-projets → validation (le nœud rejoint l'île, repère ajouté) ou archivage (le nœud coule).
2. Clic sur une île → page du projet (celle de v0, enrichie) : notes, items liés, mode exploration. C'est là que le temps de frappe alimente la croissance lente.

## Implémentation technique

- Le backend (Python, prolongement de v0) ne fournit que les données : liste des nœuds (débris + îles avec leur `growth_level`), poids de similarité, scores par seuil.
- Toute la simulation physique (positions, animation, tempête) tourne côté client, dans un composant isolé (`d3-force` ou équivalent), embarqué dans l'interface NiceGUI. C'est le seul endroit du projet où du JS est nécessaire — il reste contenu à ce composant.

## Hors scope de v1

- Mode jeu (pirates, combats, ressources, exploration incarnée) : idée mise de côté volontairement, à ne considérer, si jamais, qu'une fois v1 stable et toujours utilisé avec plaisir sans elle.