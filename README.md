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
   automatique par le registre) → copie vers `data/archives/`, dédup, OCR +
   embedding en fond. Elle apparaît dans l'inbox en quelques secondes.
   (Dossier surchargeable via `SB_WATCH_DIRS` dans `.env`.)
2. **Bookmarks & texte** : colle l'URL dans le champ en haut de la page de
   tri (Entrée ou bouton "Capturer"), ou colle du code / du texte via le
   bouton "＋ Texte/code". Titre récupéré via oEmbed quand possible
   (YouTube oui, X non).
3. **Le rituel quotidien** : ouvrir l'interface, trier 5-10 min :
   - `A` archiver · `1-9` lier à un projet · `C` créer un projet et y lier
     l'item · `→` passer · `S` rejeter une suggestion (une fois le seuil activé).
4. **Fichiers du passé (PDF, code, notes)** : dépose-les dans le dossier
   surveillé (ou un dossier dédié via `SB_WATCH_DIRS`) — ils sont ingérés au
   démarrage (rattrapage) : texte extrait (pypdf pour les PDF), embedding,
   inbox. Extension blanchie (pdf, py, md, txt, ts...).
5. **Vault Obsidian** (`myVault/`) : chaque projet créé pendant le tri génère
   un stub dans `myVault/Projets/`. Écris librement dedans ; seule la ligne
   `description:` du frontmatter est relue (embedding du projet tant qu'il
   n'a pas d'items liés). L'app ne réécrit jamais tes fichiers — renomme,
   déplace, lie des notes comme tu veux.
6. **Projet de code lié** : sur la page d'un projet, colle le chemin d'un
   dossier de code (`C:\code\mon-depot`) → l'app scanne ses fichiers `.md`
   (README, docs) et son historique git récent pour enrichir l'embedding du
   projet. Tes captures de bugs et bookmarks de libs se rapprocheront du bon
   dépôt. Jamais le code lui-même, jamais d'upload, tout en local.
7. Les sessions sont journalisées : le critère de succès de v0
   (≥ 10 sessions / 14 jours, médiane ≤ 10 min, inbox stable) est mesuré dans
   la table `sessions`, affiché sur l'écran d'accueil.

## Config (optionnelle)

Copier `.env.example` vers `.env` si besoin. Par défaut :
- auth de l'endpoint désactivée (tout est en local),
- OCR désactivé si Tesseract n'est pas installé (les items restent triables),
- embeddings désactivés si Ollama ne tourne pas (idem),
- vision photo désactivée (`SB_VISION_MODEL` vide).

Aucun de ces services ne bloque la capture ni le tri.

## Calibration des suggestions (après ~1 semaine d'usage)

Les scores item×projet sont journalisés dans `suggestion_log` (action `shown`)
dès qu'un projet existe. Regarder leur distribution :

```sql
SELECT MIN(score), AVG(score), MAX(score) FROM suggestion_log WHERE score IS NOT NULL;
```

Puis fixer `SB_SUGGEST_THRESHOLD` (les suggestions n'apparaissent qu'au-dessus).

## Sauvegarde

`data/` contient tout l'état (SQLite en WAL + archives images). Une copie
simple suffit : `robocopy data D:\backup\secondbrain /MIR` ou équivalent.

## Ce qui n'est PAS dans v0

- Carte/archipel, tempête, coffre, mode jeu → `cahier-des-charges-v1.md`.
- Capture mobile (Syncthing, HTTP Shortcuts, Tailscale) : reportée, le noyau
  est prêt à la réactiver sans refonte le jour où l'usage local est en place.