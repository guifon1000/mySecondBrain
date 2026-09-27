# Second cerveau — Cahier des charges v0 (noyau)

## Problème à résoudre

Capture continue de photos, captures d'écran et bookmarks, jamais réorganisés ensuite : ça tombe dans l'oubli.

**Objectif v0** : un rituel quotidien de 5 à 10 minutes, sur ordinateur, qui vide le stock de captures sans effort et sans y repenser le reste de la journée.

**Choix de périmètre (pivot)** : v0 tourne 100 % en local sur le PC. La capture mobile (Syncthing, HTTP Shortcuts, Tailscale) est reportée — voir "Parcours de capture" — pour que le rituel démarre avec la friction minimale possible. Le critère de succès ne change pas.

## Critère de succès de v0 (avant tout le reste)

v0 est considéré comme validé si **tous** les critères suivants sont mesurés vrais sur une fenêtre de 14 jours glissants, via la table `sessions` :

- **≥ 10 sessions de tri** sur les 14 jours (≈ 5/semaine, tolérance à la vraie vie) ;
- **durée médiane de session ≤ 10 minutes** ;
- **taille de l'inbox stable ou décroissante** sur la période (pas d'accumulation plus vite qu'on ne trie).

Tant que ce n'est pas vrai, rien d'autre ne doit être construit — voir `cahier-des-charges-v1.md`, qui ne démarre qu'après validation de v0. Chaque session est enregistrée en base (début, fin, nombre d'items triés/archivés/liés) : le critère doit pouvoir être tranché objectivement au jour 14, pas ressenti.

## Hors scope (explicitement exclu de v0 et v1 proche)

- Carte/archipel visuel, îles, simulation de forces → v1 seulement.
- Mode jeu (pirates, combats, ressources) → non spécifié, à ne considérer que si v0 et v1 tournent et que l'envie persiste. Ne doit jamais bloquer ou compliquer v0/v1.
- RAG sur corpus lourds (PDF scientifiques, schémas DTU, code) → hors périmètre, expérience passée négative sur ce type de projet (Palais des Connaissances, RAGDungeon, RAGWizard).
- Détection automatique de liens sans validation humaine → jamais. Le système ne fait que scorer et suggérer, l'utilisateur décide toujours.

## Parcours de capture (local)

Tout tourne sur le PC. Deux canaux de capture :

- **Images (captures d'écran, photos)** : le watcher surveille le dossier de captures d'écran du PC, **détecté automatiquement via le registre Windows** (gère Windows FR — `OneDrive\Pictures\Captures d'écran` — et EN), surchargeable via `SB_WATCH_DIRS`. Le dossier est ciblé précisément pour ne pas ingérer la pellicule OneDrive (photos du téléphone synchronisées). Prendre une capture d'écran suffit : elle arrive dans l'inbox en quelques secondes.
- **Bookmarks** : champ URL directement dans l'interface de tri (coller,
  Entrée ou bouton Capturer). Un endpoint HTTP `POST /ingest/bookmark`
  subsiste pour un usage avancé (bookmarklet, HTTP Shortcuts), authentifié
  par token si `SB_INGEST_TOKEN` est défini.

La capture mobile (Syncthing, HTTP Shortcuts, Tailscale) est **reportée** :
le noyau est conçu pour la réactiver plus tard sans refonte, mais elle ne
doit pas compliquer le démarrage.

## Types d'items

| type | comment ça arrive | contenu extrait |
|---|---|---|
| `screenshot` / `photo` | capture d'écran ou image déposée dans un dossier surveillé | OCR (+ vision optionnel) |
| `bookmark` | champ URL dans l'UI, ou endpoint HTTP | titre oEmbed si dispo + URL |
| `note` | bouton "＋ Texte/code" dans l'UI (coller un snippet, une pensée) | le texte lui-même |
| `file` | PDF, code, markdown... déposé dans un dossier surveillé | texte extrait (pypdf pour les PDF, lecture directe pour le texte) — extension blanchie | items déjà présents au premier lancement (dossiers existants), y compris le stock d'archives passées, sont ingérés au démarrage (rattrapage). C'est le canal pour backfiller "les tas de choses qui m'ont intéressé par le passé".

## Vault Obsidian (pont unidirectionnel, option A)

`myVault/` est l'espace d'écriture ; la DB reste la source de vérité du pipeline.

- À la création d'un projet (touche `C` pendant le tri), l'app crée un stub
  `myVault/Projets/<slug>.md` avec frontmatter `id`, `description`, `created`.
- L'app ne réécrit **jamais** un fichier existant. Renommer ou déplacer le
  fichier dans Obsidian ne casse rien (lien par `id:` frontmatter).
- L'app ne relit que le frontmatter : `description` sert de descriptif du
  projet (que l'agent Pi lit) ; la relecture est déclenchée au chargement de
  la page de tri (détection mtime).
- Le contenu libre du fichier projet (tes notes, tes connexions) n'est jamais
  parsé — c'est ton espace.

## Traitement à l'ingestion

1. Un watcher (Python, `watchdog`) détecte les nouveaux fichiers dans les dossiers surveillés, et le champ URL / bouton texte / endpoint reçoivent les bookmarks et notes.
2. **Le watcher COPIE le fichier hors du dossier source** vers un dossier d'archives interne (`data/archives/`). Jamais de référence directe vers un fichier du dossier source : si l'utilisateur supprime une capture, l'archive doit survivre.
3. **Déduplication** par hash SHA-256 du fichier (ou de l'URL pour les bookmarks) : un doublon est ignoré silencieusement.
4. OCR sur les images (`pytesseract` / Tesseract, langue `fra+eng`). Si le texte extrait est trop court (< ~20 caractères), l'item est marqué "photo sans texte" et passe au modèle vision s'il est activé.
5. Description optionnelle des photos non textuelles : pas de vision embarquée — l'agent Pi peut décrire une photo à la demande (il lit l'archive).
6. Pour les bookmarks : récupération du titre via oEmbed quand disponible (YouTube : oui ; X : pas d'oEmbed public fiable → on affiche l'URL brute, pas de promesse de preview au-delà). Pas de scraping lourd en v0.
7. **Aucun embedding, aucun appel IA** : l'enrichissement est purement local (oEmbed, extraction de texte, OCR optionnel). La sémantique est déléguée à l'agent Pi dédié au projet.

**Choix IA** : pas de modèle local, pas de clé API dans l'app. L'agent Pi (session dédiée à ce projet) fait le travail sémantique à la demande, en lisant la base. Un humain valide toujours tout lien.
8. **Burst initial toléré** : le traitement (OCR, extraction) se fait dans une file d'arrière-plan, pas dans le chemin de capture. Un afflux massif au premier lancement (rattrapage des dossiers existants) ralentit l'enrichissement, jamais la capture ni le tri.

## Projets

- Table `projects` : `id`, `title`, `description` (courte, optionnelle), `created_at`, `vault_path`, `code_path`.
- Création de projet possible à tout moment : à l'ingestion (pas nécessaire), et pendant le tri (action "Créer un projet", avec lien immédiat de l'item courant).
- Le scoring porte sur la liste des projets existants **au moment de l'affichage** — la création d'un nouveau projet est toujours permise et n'est pas une "découverte ouverte".

- **Ancrage à un dépôt de code** : sur la page projet, un champ permet de
  lier un dossier local (ex. `C:\code\mon-projet`). L'app y scanne — jamais
  le code lui-même — les fichiers `*.md` (README, docs) et l'historique
  git récent (`git log --oneline -40`), tout plafonné (30 fichiers,
  600 car/fichier). Le texte scanné est stocké en base (`code_scan_text`) :
  c'est la matière que l'agent Pi lit pour suggérer des liens. Rescan auto
  24 h au chargement du tri.

## IA : aucune embarquée — l'agent Pi fait le sémantique

L'app n'appelle **aucun modèle** (ni local, ni API). Le travail sémantique est
confié à l'**agent Pi dédié au projet**, à la demande :

- il lit directement la base SQLite (`data/secondbrain.db`) : items en inbox,
  OCR/titres, descriptions de projets, textes de scan des dépôts ;
- il propose des liens item ↔ projet en langage naturel ;
- la validation reste humaine : dans l'UI (touches 1-9) ou via lui ;
- les colonnes `embedding` restent NULL (schéma préservé pour un usage futur).

Conséquences :
- zéro clé API, zéro service IA à maintenir dans le code ;
- la section "Suggestions de lien" (seuil, calibrage, suggestion_log) devient
  **hors scope v0** : les suggestions viennent d'une conversation avec
  l'agent, pas d'un calcul embarqué.

## Tri quotidien

- Interface liste simple (pas de carte en v0), **un item affiché à la fois**, **conçue keyboard-first** :
  - `A` = archiver (un geste, zéro décision supplémentaire, l'item sort de l'inbox — conservé, pas supprimé)
  - `1`–`9` = lier au projet n de la liste affichée à l'écran
  - `C` = créer un nouveau projet et y lier l'item courant
  - navigation `→` ou `Espace` pour passer sans décider (l'item reste en inbox)
  - `S` = rejeter la suggestion affichée (quand les suggestions sont activées)
- Session **plafonnée à 15 items** par défaut (configurable) pour respecter la fenêtre 5-10 min.
- Une entrée est créée dans `sessions` à l'ouverture du tri (si de nouveaux items existent) et clôturée automatiquement.

## Boucle de récompense (page projet minimale)

Le tri ne doit pas être qu'une corvée de soustraction. Dès v0 :

- Page **Mes projets** : liste des projets avec nombre d'items liés.
- Page **projet** : titre, description, liste chronologique des items liés (miniatures pour les images, liens cliquables pour les bookmarks).
- La page projet affiche le compteur "grandi de N items cette semaine" — la satisfaction minimale avant la carte de v1.

## Stack technique

- **Langage** : Python partout côté serveur (aucune UI riche en v0, donc pas de sujet JS).
- **API + UI** : FastAPI (endpoint de réception des bookmarks) avec NiceGUI monté dessus — **un seul processus** : API, watcher, enrichissement, tri. Moins de services, moins de choses qui cassent.
- **Watcher** : `watchdog`, thread dans le même processus.
- **OCR** : `pytesseract` (dégradation gracieuse si Tesseract absent).
- **Vision (option)** : supprimée — l'agent peut décrire une photo si on lui demande.
- **Embeddings** : supprimés — colonnes conservées (NULL) pour un usage futur.
- **Métadonnées** : **SQLite unique**, pas de service séparé, pas de ChromaDB.
- **Conteneurisation** : hors scope. Un process local suffit.
- **Réseau** : tout en local (`127.0.0.1` par défaut). Pas de Tailscale, pas d'exposition, pas de certificats.
- **Sauvegarde** : le dossier `data/` (SQLite + archives) est le seul état du système ; copie simple documentée dans le README.

## Schéma de données (SQLite)

Table **items** :

| champ | description |
|---|---|
| `id` | identifiant unique |
| `type` | screenshot / photo / bookmark / note / file |
| `source_path` | chemin de la copie archivée dans `data/archives/` |
| `url` | URL pour les bookmarks |
| `title` | titre oEmbed si disponible |
| `ocr_text` | texte extrait |
| `vision_description` | description du modèle vision si activé |
| `embedding` | BLOB du vecteur (NULL si enrichissement incomplet) |
| `sha256` | hash de déduplication (unique) |
| `created_at` | date de capture |
| `status` | inbox / archived / linked |
| `linked_project_id` | projet associé si lié |
| `ingest_done` | 0 = en attente d'enrichissement, 1 = traité |

Table **projects** : `id`, `title`, `description`, `created_at`, `vault_path`, `vault_mtime` (pont vault, option A), `code_path`, `code_scan_at`, `code_scan_text` (dépôt de code lié). La colonne `embedding` reste (NULL, usage futur).

Table **sessions** : `id`, `started_at`, `ended_at`, `items_reviewed`, `archived`, `linked`, `projects_created`.

Table **suggestion_log** : conservée (historique des liens proposés par l'agent et acceptés/rejetés), sans calcul de score embarqué.