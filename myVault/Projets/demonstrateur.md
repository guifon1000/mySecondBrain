---
id: 7
description: SaaS local (FastAPI, port 8000) qui intègre les trois dépôts métier — rincewind, renardiere, sapientpearwood installés en editable. Auth par cookie, workspace utilisateurs, bug-reports.
created: 2026-09-27
---
# Demonstrateur

**SaaS de démonstration**, 100 % local. `C:\Users\guill\demonstrateur`.

- **Rôle** : frontend/serveur FastAPI qui embarque les trois dépôts métier
  (rincewind, renardiere, sapientpearwood) en installations **editable**
  (`pip list` pointe vers `C:\Users\guill\...`).
- **Lancer** : `python -m uvicorn app:app --reload --port 8000` →
  http://127.0.0.1:8000
- **Config** : `.env` (dev local — `COOKIE_SECURE=0` obligatoire en http
  local), `.admin.env`.
- **Structure** : `app.py`, `auth.py`, `cli_invite.py`, `static/`,
  `workspace/`, `users.db`, `bug-reports/`, `scripts/`.
- **Docs clés** : `DEV-LOCAL.md`.