"""Interface de tri (NiceGUI) — keyboard-first, un item à la fois.

Raccourcis (cahier des charges v0) :
  A        archiver
  1..9     lier au projet n de la liste affichée
  C        créer un projet et y lier l'item courant
  -> / E   passer sans décider (l'item reste en inbox)
  S        rejeter la suggestion (si les suggestions sont activées)
"""
import logging
from datetime import datetime
from pathlib import Path

from nicegui import app, ui

from . import config, db, enrich
from . import codeproject, vault
from .api import ingest_text, ingest_url

log = logging.getLogger("ui")


# --- Utilitaires ------------------------------------------------------------

def _archive_url(item) -> str | None:
    if not item["source_path"]:
        return None
    return f"/archives/{Path(item['source_path']).name}"


def _stats() -> dict:
    with db.db() as conn:
        rows = conn.execute(
            "SELECT started_at, ended_at FROM sessions "
            "WHERE started_at >= datetime('now', '-14 days') AND ended_at IS NOT NULL"
        ).fetchall()
    durations = sorted(
        (datetime.fromisoformat(r["ended_at"]) - datetime.fromisoformat(r["started_at"])
         ).total_seconds() / 60
        for r in rows
    )
    with db.db() as conn:
        inbox = db.inbox_count(conn)
    return {
        "sessions_14d": len(rows),
        "median_min": round(durations[len(durations) // 2], 1) if durations else 0.0,
        "inbox": inbox,
    }


# --- Actions de tri ----------------------------------------------------------

def _link_item(item_id: int, project_id: int, session_id: int) -> None:
    with db.db() as conn:
        conn.execute(
            "UPDATE items SET status = 'linked', linked_project_id = ? WHERE id = ?",
            (project_id, item_id),
        )
        conn.execute(
            "UPDATE sessions SET items_reviewed = items_reviewed + 1, "
            "linked = linked + 1 WHERE id = ?",
            (session_id,),
        )
        conn.execute(
            "UPDATE suggestion_log SET action = 'accepted' WHERE item_id = ? "
            "AND project_id = ? AND action = 'shown'",
            (item_id, project_id),
        )


def _archive_item(item_id: int, session_id: int) -> None:
    with db.db() as conn:
        conn.execute("UPDATE items SET status = 'archived' WHERE id = ?", (item_id,))
        conn.execute(
            "UPDATE sessions SET items_reviewed = items_reviewed + 1, "
            "archived = archived + 1 WHERE id = ?",
            (session_id,),
        )


def _create_project_with_item(title: str, description: str, item_id: int,
                              session_id: int) -> int:
    with db.db() as conn:
        cur = conn.execute(
            "INSERT INTO projects (title, description) VALUES (?, ?)", (title, description)
        )
        project_id = cur.lastrowid
        conn.execute(
            "UPDATE items SET status = 'linked', linked_project_id = ? WHERE id = ?",
            (project_id, item_id),
        )
        conn.execute(
            "UPDATE sessions SET items_reviewed = items_reviewed + 1, "
            "linked = linked + 1, projects_created = projects_created + 1 WHERE id = ?",
            (session_id,),
        )
        try:
            stub = vault.create_project_stub(project_id, title, description)
            if stub:
                conn.execute(
                    "UPDATE projects SET vault_path = ? WHERE id = ?",
                    (str(stub), project_id),
                )
        except Exception:
            log.exception("stub vault non créé (erreur)")
    return project_id


def _close_stale_sessions() -> None:
    with db.db() as conn:
        conn.execute(
            "UPDATE sessions SET ended_at = datetime('now') "
            "WHERE ended_at IS NULL AND started_at < datetime('now', '-1 hour')"
        )


# --- Page de tri -------------------------------------------------------------

@ui.page("/")
def tri_page():
    ui.dark_mode(True)
    _close_stale_sessions()

    with db.db() as conn:
        items = db.inbox_items(conn, config.SESSION_MAX_ITEMS)
        projects = db.all_projects(conn)

    state = {"index": 0, "dialog_open": False, "session_id": None, "done": False}

    # Pont vault (option A) + rafraîchissement des dépôts de code liés
    try:
        with db.db() as conn:
            vault.sync_projects(conn)
    except Exception:
        log.exception("sync vault ignorée (erreur)")
    try:
        with db.db() as conn:
            codeproject.rescan_stale(conn)
    except Exception:
        log.exception("rescan des dépôts de code ignoré")

    if items:
        with db.db() as conn:
            state["session_id"] = conn.execute("INSERT INTO sessions DEFAULT VALUES").lastrowid

    header_label = ui.label().classes("text-lg opacity-70")
    card = ui.column().classes("w-full")

    # Capture locale : champ URL (bookmark) + bouton texte/code (note)
    with ui.row().classes("w-full max-w-3xl mx-auto items-center gap-2"):
        url_input = ui.input(placeholder="Coller une URL à capturer…").classes("grow")

        async def capture_url():
            value = url_input.value
            try:
                _item_id, status = ingest_url(value)
            except Exception:
                ui.notify("URL invalide", type="negative")
                return
            url_input.set_value(None)
            ui.notify(
                "Capture ajoutée à l'inbox" if status == "ok" else "Déjà en inbox (doublon)",
                type="positive" if status == "ok" else "info",
            )

        ui.button("Capturer", on_click=capture_url).props("outline")
        url_input.on("keydown.enter", capture_url)

        async def open_note_dialog():
            state["dialog_open"] = True
            with ui.dialog() as note_dlg, ui.card().classes("w-full max-w-2xl"):
                ui.label("Coller du texte ou du code").classes("text-lg")
                ta = ui.textarea(placeholder="Colle ici…").classes("w-full")
                ta.props("autogrow outlined")
                with ui.row():
                    ui.button(
                        "Capturer",
                        on_click=lambda: (
                            note_dlg.close(),
                            ingest_text_and_notify(ta.value),
                        ),
                    )
                    ui.button("Annuler", on_click=note_dlg.close).props("flat")
            note_dlg.on("hide", lambda: state.update(dialog_open=False))
            note_dlg.open()
            ui.run_javascript(
                "setTimeout(() => document.querySelector('.q-textarea textarea')?.focus(), 100)"
            )

        ui.button("＋ Texte/code", on_click=open_note_dialog).props("outline flat")

    def ingest_text_and_notify(text: str):
        try:
            _item_id, status = ingest_text(text)
        except Exception:
            ui.notify("Texte vide", type="negative")
            return
        ui.notify(
            "Capture ajoutée à l'inbox" if status == "ok" else "Déjà en inbox (doublon)",
            type="positive" if status == "ok" else "info",
        )

    with ui.column().classes("w-full max-w-3xl mx-auto p-2 opacity-70 text-sm"):
        ui.markdown(
            "**A** archiver · **1-9** lier · **C** créer projet · "
            "**→** passer · **S** rejeter suggestion"
        )

    def update_header():
        with db.db() as conn:
            remaining = db.inbox_count(conn)
        header_label.set_text(
            f"Tri du jour — item {state['index'] + 1}/{len(items)} · {remaining} en inbox"
        )

    def summary_view():
        card.clear()
        stats = _stats()
        with card:
            ui.label("Session terminée 🎉").classes("text-2xl")
            ui.label(
                f"{len(items)} items traités. Le reste attendra — la session est "
                f"plafonnée pour tenir en 5-10 min."
            ).classes("opacity-70")
            with ui.row().classes("mt-4 gap-6 items-center"):
                with ui.column():
                    ui.label(f"{stats['sessions_14d']}").classes("text-3xl font-bold")
                    ui.label("sessions / 14 j").classes("text-sm opacity-60")
                with ui.column():
                    ui.label(f"{stats['median_min']} min").classes("text-3xl font-bold")
                    ui.label("durée médiane").classes("text-sm opacity-60")
                with ui.column():
                    ui.label(f"{stats['inbox']}").classes("text-3xl font-bold")
                    ui.label("en inbox").classes("text-sm opacity-60")
            with ui.row().classes("mt-4"):
                ui.link("Voir mes projets →", "/projects").classes("text-blue-400")
                ui.button("Recharger", on_click=lambda: ui.navigate.to("/")).props("flat")

    def show_item():
        if state["index"] >= len(items):
            if state["session_id"]:
                with db.db() as conn:
                    conn.execute(
                        "UPDATE sessions SET ended_at = datetime('now') WHERE id = ?",
                        (state["session_id"],),
                    )
            state["done"] = True
            summary_view()
            return
        item = items[state["index"]]
        update_header()
        card.clear()
        with card, ui.card().classes("w-full"):
            url = _archive_url(item)
            if url and item["type"] in ("photo", "screenshot"):
                ui.image(url).classes("max-h-96 w-auto")
            if item["type"] == "file" and url:
                with ui.row().classes("items-center gap-2"):
                    ui.badge(Path(item["source_path"]).suffix).color("purple")
                    ui.link("Ouvrir le fichier", url).classes("text-blue-400")
            if item["title"]:
                ui.label(item["title"]).classes("text-lg font-semibold")
            if item["url"]:
                ui.link(item["url"], item["url"]).classes("text-blue-400 break-all")
            if item["ocr_text"]:
                with ui.scroll_area().classes("max-h-40 w-full"):
                    ui.label(item["ocr_text"]).classes("whitespace-pre-wrap text-sm")
            if not (url or item["url"] or item["ocr_text"] or item["title"]):
                ui.label("(item sans contenu exploitable)").classes("opacity-50")
            # Suggestions : pas d'IA embarquée dans l'app — elles viennent de
            # l'agent Pi dédié au projet, à la demande (lecture de la base,
            # proposition, validation humaine ici via touches 1-9).

    def advance():
        state["index"] += 1
        show_item()

    def do_archive():
        if state["done"]:
            return
        _archive_item(items[state["index"]]["id"], state["session_id"])
        advance()

    def do_link(idx: int):
        if state["done"] or idx >= len(projects):
            return
        _link_item(items[state["index"]]["id"], projects[idx]["id"], state["session_id"])
        advance()

    def do_create_project(title: str):
        if state["done"] or not title.strip():
            return
        _create_project_with_item(
            title.strip(), "", items[state["index"]]["id"], state["session_id"]
        )
        ui.notify(f"Projet « {title.strip()} » créé", type="positive")
        advance()

    def do_reject_suggestion():
        if state["done"]:
            return
        item_id = items[state["index"]]["id"]
        with db.db() as conn:
            conn.execute(
                "UPDATE suggestion_log SET action = 'rejected' WHERE item_id = ? "
                "AND action = 'shown'",
                (item_id,),
            )
        ui.notify("Suggestion rejetée")
        advance()

    def open_create_dialog():
        state["dialog_open"] = True
        with ui.dialog() as dlg, ui.card():
            ui.label("Nouveau projet").classes("text-lg")
            inp = ui.input("Titre").classes("w-full")
            with ui.row():
                ui.button(
                    "Créer et lier",
                    on_click=lambda: (dlg.close(), do_create_project(inp.value)),
                )
                ui.button("Annuler", on_click=dlg.close).props("flat")
        dlg.on("hide", lambda: state.update(dialog_open=False))
        inp.on("keydown.enter", lambda: (dlg.close(), do_create_project(inp.value)))
        dlg.open()
        ui.run_javascript(
            "setTimeout(() => document.querySelector('.q-field input')?.focus(), 100)"
        )

    async def on_key(e):
        # KeyEventArguments : e.action.keydown / e.action.repeat, e.key.name /
        # e.key.number. Les inputs (champ URL, dialog) sont déjà exclus par le
        # paramètre `ignore` par défaut de ui.keyboard.
        if not e.action.keydown or e.action.repeat or state["done"]:
            return
        if state["dialog_open"]:
            return
        num = e.key.number
        if num is not None and 1 <= num <= 9:
            do_link(num - 1)
        elif e.key.name.lower() == "a":
            do_archive()
        elif e.key.name.lower() == "c":
            open_create_dialog()
        elif e.key.name.lower() == "s":
            do_reject_suggestion()
        elif e.key.space or e.key.name == "ArrowRight":
            advance()

    ui.keyboard(on_key=on_key)

    if items:
        show_item()
    else:
        with card, ui.card().classes("w-full"):
            _empty_state()

    if projects and not state["done"]:
        with ui.column().classes("w-full max-w-3xl mx-auto p-2"):
            ui.label("Projets (touches 1-9)").classes("text-sm opacity-60")
            for i, p in enumerate(projects[:9]):
                with ui.row().classes("items-center gap-2 no-wrap"):
                    ui.badge(str(i + 1)).props("dense")
                    ui.label(p["title"])
                    ui.label(f"({p['item_count']})").classes("opacity-50 text-sm")


def _empty_state():
    stats = _stats()
    ui.label("Inbox vide ✨").classes("text-2xl")
    ui.label(
        "Le rituel reprendra quand Syncthing aura synchronisé de nouvelles captures."
    ).classes("opacity-70")
    with ui.row().classes("mt-4 gap-6 items-center"):
        with ui.column():
            ui.label(f"{stats['sessions_14d']}").classes("text-3xl font-bold")
            ui.label("sessions / 14 j").classes("text-sm opacity-60")
        with ui.column():
            ui.label(f"{stats['median_min']} min").classes("text-3xl font-bold")
            ui.label("durée médiane").classes("text-sm opacity-60")
        with ui.column():
            ui.label(f"{stats['inbox']}").classes("text-3xl font-bold")
            ui.label("en inbox").classes("text-sm opacity-60")
    if stats["sessions_14d"] >= 10:
        ui.badge("Critère v0 en bonne voie — continue", color="green")
    ui.link("Mes projets →", "/projects").classes("text-blue-400 mt-2")


# --- Pages projets (boucle de récompense minimale) ----------------------------

@ui.page("/projects")
def projects_page():
    ui.dark_mode(True)
    with db.db() as conn:
        projects = db.all_projects(conn)
    with ui.column().classes("w-full max-w-3xl mx-auto gap-2 p-4"):
        ui.label("Mes projets").classes("text-2xl")
        if not projects:
            ui.label(
                "Aucun projet pour l'instant. Les projets naissent pendant le tri "
                "(touche C) quand une capture ne correspond à rien."
            ).classes("opacity-70")
        for p in projects:
            with ui.card().classes("w-full") as proj_card:
                with ui.row().classes("w-full items-center justify-between"):
                    with ui.row().classes("items-center gap-2"):
                        ui.label(p["title"]).classes("text-lg font-semibold")
                        if p["items_this_week"]:
                            ui.badge(f"+{p['items_this_week']} cette semaine").color("green")
                    ui.label(f"{p['item_count']} items").classes("opacity-60")
                proj_card.on("click", lambda _, pid=p["id"]: ui.navigate.to(f"/project/{pid}"))
        ui.link("← Retour au tri", "/").classes("text-blue-400 mt-4")


@ui.page("/project/{project_id}")
def project_page(project_id: int):
    ui.dark_mode(True)
    with db.db() as conn:
        p = db.project(conn, project_id)
        items = db.linked_items(conn, project_id)
    if p is None:
        ui.label("Projet introuvable")
        return
    with ui.column().classes("w-full max-w-3xl mx-auto gap-3 p-4"):
        ui.label(p["title"]).classes("text-2xl")
        if p["description"]:
            ui.label(p["description"]).classes("opacity-70")

        # Dépôt de code lié (scan md + git pour l'embedding du projet)
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center gap-2 no-wrap"):
                code_input = ui.input("Dossier du projet de code (optionnel)",
                                      value=p["code_path"] or "").classes("grow")

                def link_code():
                    path = code_input.value.strip()
                    if path and not Path(path).is_dir():
                        ui.notify("Dossier introuvable", type="negative")
                        return
                    with db.db() as conn:
                        conn.execute(
                            "UPDATE projects SET code_path = ? WHERE id = ?",
                            (path or None, project_id),
                        )
                        n = codeproject.link_and_scan(conn, project_id, path) if path else -1
                    if path and n >= 0:
                        ui.notify(f"Dépôt lié — {n} fichiers md scannés", type="positive")
                    elif path:
                        ui.notify("Dépôt lié mais rien d'exploitable (pas de md)", type="warning")
                    else:
                        ui.notify("Dépôt délié")
                    ui.navigate.to(f"/project/{project_id}")

                ui.button("Lier & scanner", on_click=link_code).props("outline")
            if p["code_path"]:
                scanned = p["code_scan_at"] or "jamais"
                ui.label(
                    f"Dépôt lié : {p['code_path']} — dernier scan : {scanned} "
                    f"(rescan auto toutes les 24 h au chargement du tri)"
                ).classes("text-xs opacity-60")

        ui.label(f"{len(items)} items liés").classes("opacity-60")
        ui.separator()
        if not items:
            ui.label("Aucun item lié pour l'instant.").classes("opacity-70")
        for item in items:
            with ui.card().classes("w-full"):
                with ui.row().classes("w-full items-start gap-3 no-wrap"):
                    url = _archive_url(item)
                    if url:
                        ui.image(url).classes("w-24 h-24 rounded object-cover")
                    with ui.column().classes("grow"):
                        if item["title"]:
                            ui.label(item["title"]).classes("font-semibold")
                        if item["url"]:
                            ui.link(item["url"], item["url"]).classes(
                                "text-blue-400 break-all text-sm")
                        if item["ocr_text"]:
                            preview = item["ocr_text"][:200]
                            suffix = "…" if len(item["ocr_text"]) > 200 else ""
                            ui.label(preview + suffix).classes("text-sm opacity-70")
                        ui.label(item["created_at"]).classes("text-xs opacity-40")
        ui.link("← Mes projets", "/projects").classes("text-blue-400 mt-4")
