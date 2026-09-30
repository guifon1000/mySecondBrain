# Vestiges RAG — leçons et idées à garder

> Note de fouille des trois projets RAG abandonnés (`RAGCarto`,
> `RAGDungeon`/Palais des Connaissances, `RAGWizard`). Le cahier des charges
> exclut le RAG lourd sur corpus — mais il y a des idées concrètes à
> récupérer. Tenue par l'agent du second cerveau.

## Ce qui a échoué (pour ne pas recommencer)

- **Palais des Connaissances / RAGDungeon** : moteur de donjon roguelike
  généré depuis un corpus PDF (embeddings → ChromaDB → UMAP → layout du
  donjon), quiz LLM dans les salles. Bel objet, corvée d'entretien : la
  pipeline RAG (ingestion, chunking, index) écrasait le jeu sous la
  maintenance. Leçon : ne jamais laisser un pipeline RAG au cœur d'un objet
  de plaisir.
- **RAGWizard** : boucle génération → auto-critique → réécriture. Deux
  fichiers. Leçon : l'auto-critique de LLM améliore la forme, pas la
  véracité — peu utile sans corpus de vérification (que test_corpus,
  lui, construit méthodiquement).

## Idées récupérables pour le second cerveau

1. **Extraction de figures depuis les PDF** (RAGCarto, `smart_chunk.py` +
   `book_navigator.py`) — détection de la police dominante pour repérer les
   légendes, extraction des zones de figure en images (`extract_visual` via
   PyMuPDF). **Le plus concret** : les items `file` (PDF, DTU, traités)
   pourraient livrer leurs figures en pièces jointes — une note d'inbox
   Obsidian montrerait alors la planche du DTU, pas seulement un extrait de
   texte. Coût : dépendance PyMuPDF. À faire si les PDF deviennent
   fréquents dans l'inbox.
2. **Layout 2D par réduction de dimension** (RAGDungeon, `dungeon_gen.py`) :
   UMAP sur les embeddings pour positionner les éléments. Pour la v1
   (carte/archipel), les positions initiales des débris pourraient venir
   d'une réduction de dimension plutôt que d'un spawn aléatoire — le
   d3-force ferait ensuite le raffinement. Ajouté comme option au cahier v1.
3. **Fenêtre de contexte autour d'un chunk** (`book_navigator.get_context_window`) :
   présenté un item, montrer son voisinage (items captés au même moment) —
   naturel pour un journal de captures horodatées.
4. **Distillation de chunks** (`RAGDungeon/rag/distill.py`) : condenser un
   long document en résumés par zone. Idée pour un jour : distiller les PDF
   de l'inbox pour l'affichage tri (une ligne de résumé sous le PDF).
5. **La discipline manifeste de test_corpus** (actif, à ne PAS abandonner) :
   registre JSONL de classification, manifestes vérifiés par agents,
   sources re-localisables. Modèle de traçabilité que le second cerveau
   respecte déjà avec `suggestion_log` et les sessions.

## Décisions

- Les dépôts RAG* ne deviennent **pas** des projets du second cerveau
  (abandonnés, hors périmètre du rituel).
- Idée 1 (figures PDF) : candidate la plus sérieuse — attendre que l'usage
  le justifie (cahier des charges : un incrément se justifie par l'usage).
- Idée 2 (UMAP pour v1) : notée dans `cahier-des-charges-v1.md`.
- test_corpus : ajouté comme projet actif (instance Prospectiviste dédiée).