# Second cerveau — noyau v0

Implémentation du cahier des charges `cahier-des-charges-v0.md` : rituel quotidien
de tri des captures du téléphone, sur un seul process Python (API + watcher +
enrichissement + UI).

## Démarrage rapide (dev)

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Linux/mac : .venv/bin/pip
.venv/Scripts/python run.py
```

Interface : http://localhost:8420 — endpoint bookmarks : `POST /ingest/bookmark`.

## Config

Copier `.env.example` vers `.env` et adapter (token d'ingestion notamment).

## Le rituel

1. Le téléphone pousse ses captures via Syncthing dans `data/watched/` (configuré
   côté Android vers ce dossier).
2. Le watcher copie chaque fichier vers `data/archives/` (survit aux suppressions
   téléphone), déduplique par hash, puis un worker fait OCR + embedding en fond.
3. Partage d'une URL X/YouTube → HTTP Shortcuts → `POST /ingest/bookmark`
   (header `X-Ingest-Token`).
4. Chaque jour, ouvrir l'interface, trier 5-10 min :
   - `A` archiver · `1-9` lier à un projet · `C` créer un projet et y lier l'item
     · `→` passer · `S` rejeter une suggestion (une fois le seuil activé).
5. Les sessions sont journalisées : le critère de succès de v0
   (≥ 10 sessions / 14 jours, médiane ≤ 10 min, inbox stable) est mesurable dans
   la table `sessions`, affiché sur l'écran d'accueil.

## Dégradation gracieuse

- Tesseract absent → pas d'OCR, les items restent triables.
- Ollama absent → pas d'embeddings ni de suggestions ; le tri manuel fonctionne.
- Vision désactivé par défaut (`SB_VISION_MODEL` vide).

Aucun de ces services ne bloque la capture ni le tri.

## Calibration des suggestions (après ~1 semaine d'usage)

Les scores item×projet sont journalisés dans `suggestion_log` (action `shown`)
dès qu'un projet existe. Regarder leur distribution :

```sql
SELECT MIN(score), AVG(score), MAX(score) FROM suggestion_log WHERE score IS NOT NULL;
```

Puis fixer `SB_SUGGEST_THRESHOLD` (les suggestions n'apparaissent qu'au-dessus).

## Déploiement serveur (Tailscale)

- Installer le repo sur le serveur, `python run.py` sous systemd (ou tmux pour tester).
- L'app écoute sur `SB_HOST:SB_PORT`, accessible uniquement via l'IP Tailscale.
- Côté Android : Syncthing → dossier `watched` ; HTTP Shortcuts → POST vers
  `http://<ip-tailscale>:8420/ingest/bookmark` avec header `X-Ingest-Token`.

## Sauvegarde

`data/` contient tout l'état (SQLite en WAL + archives images). Copie quotidienne
simple : `rsync -a data/ /backup/secondbrain/` en cron.

## Ce qui n'est PAS dans v0

Carte/archipel, tempête, coffre, mode jeu → `cahier-des-charges-v1.md`, qui ne
démarre qu'après validation du critère de succès de v0 (mesuré, pas ressenti).
