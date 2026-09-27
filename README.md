# Second cerveau — noyau v0 (100% local)

Implémentation du cahier des charges `cahier-des-charges-v0.md` : rituel quotidien
de tri des captures du PC, sur un seul process Python (API + watcher +
enrichissement + UI). Pas de téléphone, pas de VPS, pas de service externe requis.

## Démarrage

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python run.py
```

Interface : http://localhost:8420

## Comment ça marche

1. **Captures d'écran / images** : dès que tu prends une capture Windows
   (`Win+PrtScn`, Snipping Tool, etc.), elle est détectée dans ton dossier de
   captures (`OneDrive\Pictures\Captures d'écran` sur Windows FR, détection
   automatique par le registre) → copie vers `data/archives/`, dédup,
   OCR (si Tesseract installé). Elle apparaît dans l'inbox en quelques
   secondes. (Dossier surchargeable via `SB_WATCH_DIRS` dans `.env`.)
2. **Bookmarks & texte** : colle l'URL dans le champ en haut de la page de
   tri (Entrée ou bouton "Capturer"), ou colle du code / du texte via le
   bouton "＋ Texte/code". Titre récupéré via oEmbed quand possible
   (YouTube oui, X non).
3. **Le rituel quotidien** : ouvrir l'interface, trier 5-10 min :
   - `A` archiver · `1-9` lier à un projet · `C` créer un projet et y lier
     l'item · `→` passer · `S` rejeter une suggestion (proposée par l'agent)
4. **Fichiers du passé (PDF, code, notes)** : dépose-les dans le dossier
   surveillé (ou un dossier dédié via `SB_WATCH_DIRS`) — ils sont ingérés au
   démarrage (rattrapage) : texte extrait (pypdf pour les PDF), inbox. Extension blanchie (pdf, py, md, txt, ts...).
5. **Vault Obsidian** (`myVault/`) : chaque projet créé pendant le tri génère
   un stub dans `myVault/Projets/`. Écris librement dedans ; seule la ligne
   `description:` du frontmatter est relue. L'app ne réécrit jamais tes
   fichiers — renomme, déplace, lie des notes comme tu veux.
6. **Projet de code lié** : sur la page d'un projet, colle le chemin d'un
   dossier de code (`C:\code\mon-depot`) → l'app scanne ses fichiers `.md`
   (README, docs) et son historique git récent, et stocke le texte en base.
   C'est la matière que **l'agent Pi** (session dédiée à ce projet) lit pour
   suggérer des liens : demande-lui par ex. "suggère des liens pour mon inbox".
   Jamais le code lui-même, jamais d'upload, tout en local.
7. Les sessions sont journalisées : le critère de succès de v0
   (≥ 10 sessions / 14 jours, médiane ≤ 10 min, inbox stable) est mesuré dans
   la table `sessions`, affiché sur l'écran d'accueil.

## Config (optionnelle)

Copier `.env.example` vers `.env` si besoin. Par défaut :
- auth de l'endpoint désactivée (tout est en local),
- OCR désactivé si Tesseract n'est pas installé (les items restent triables),
- **IA** : aucune embarquée (pas de clé API, pas de modèle local). Le
  sémantique est fait par **l'agent Pi dédié au projet**, à la demande : il
  lit la base SQLite, propose des liens, tu valides (touches 1-9 dans l'UI,
  ou via lui). Voir le cahier des charges v0, section dédiée.

La capture, le tri et le vault fonctionnent sans aucune clé — l'IA ne fait
qu'enrichir les suggestions.

## Suggestions : par l'agent, pas par un calcul

Pour faire suggérer des liens item ↔ projet, demande-le à l'agent Pi dédié au
projet (ex. "suggère des liens pour mon inbox") : il lit la base (items, OCR,
descriptions, scans de dépôts), te propose des liens en langage naturel, et tu
valides — dans l'UI (touches 1-9) ou en le laissant les appliquer.

## Sauvegarde

`data/` contient tout l'état (SQLite en WAL + archives images). Une copie
simple suffit : `robocopy data D:\backup\secondbrain /MIR` ou équivalent.

## Ce qui n'est PAS dans v0

- Carte/archipel, tempête, coffre, mode jeu → `cahier-des-charges-v1.md`.
- Capture mobile (Syncthing, HTTP Shortcuts, Tailscale) : reportée, le noyau
  est prêt à la réactiver sans refonte le jour où l'usage local est en place.