---
id: 8
description: RAG de prospectiviste — méthodes de construction résilientes pour le bâtiment 2050. Croise savoir-faire traditionnels (bois, paille, terre) et scénarios GIEC. Projet actif, agent dédié « Prospectiviste » (CLAUDE.md).
created: 2026-09-27
---
# Test corpus

**RAG prospectif — construction résiliente.** `C:\Users\guill\test_corpus`. Projet actif.

- **Mission** (cf. `CLAUDE.md`, rôle "Agent Prospectiviste") : construire des
  hypothèses crédibles sur les méthodes de construction 2050 en croisant
  savoir-faire pré-industriels (charpente, bois/paille/terre, traités comme
  Roubo) et scénarios GIEC (AR6, SSP). Rigueur avant récit, traçabilité des
  sources, degrés de confiance explicites (établi / plausible / spéculatif).
- **Corpus** (`corpus/`) : organisé par domaine (`bois`, `paille`, `terre`,
  `giec`) et type (`norme`, `these`, `traite`, `rapport`), avec un registre
  de classification (`registry/classifications.jsonl`) et des manifestes
  vérifiés par agents (manifest_*_verified.jsonl). Qualité du corpus avant
  volume.
- **Outil** (`rag.py`) : chunking + embeddings + retrieve/search, génération
  via OpenRouter ou Ollama. Rudimentaire mais actif.
- **Liens écosystème** : famille métier charpente (renardiere,
  sapientpearwood) — les captures de détails DTU/normes bois sont
  susceptibles de l'intéresser.
- **Leçon réutilisable pour le second cerveau** : la discipline
  manifeste/registre (chaque document classé, tracé, vérifié avant usage)
  est exactement l'esprit "l'humain valide" du cahier des charges.