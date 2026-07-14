# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dev commands

**Backend**
```bash
uv venv
uv pip install -r requirements.txt
uv run uvicorn backend.main:app --port 7487 --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev       # dev server on :5173, proxies /api/* to :7487
npm run build     # outputs to frontend/dist/
```

There are no tests.

## Architecture

Single-process FastAPI app that serves both the API and the built Vue SPA. In dev, Vite runs separately and proxies `/api` to the backend. In production (and Docker), `backend/main.py` mounts `frontend/dist/` as static files on the same port (7487).

### Backend

**`backend/manager.py` — the core engine.**
`run_manager()` is a plain synchronous function that runs at startup and on a configurable APScheduler interval. It fetches all torrents from the qBittorrent API, filters to managed categories, and applies each module's logic in sequence (completed-purge → exe-killer → error-killer → eta-monitor → stall-monitor). Each torrent is evaluated top-to-bottom; `continue` after any purge skips remaining modules for that torrent.

**`backend/db.py` — all persistence.**
SQLite via raw `sqlite3`, no ORM. `init_db()` creates tables on startup and is safe to re-run (uses `CREATE TABLE IF NOT EXISTS` and `ALTER TABLE ... ADD COLUMN` with OperationalError catch for migrations). Module configs are stored as JSON blobs in the `settings` table under keys like `module_<id>_config`; they are merged with `DEFAULT_MODULE_CONFIGS` on read so new default keys appear automatically after upgrades.

**`backend/routers/`** — one file per resource (`dashboard`, `torrents`, `exclusions`, `modules`, `settings`, `logs`, `scheduler`). Each is a thin FastAPI router that delegates to `db.py` and `qbt.py`.

**`backend/qbt.py`** — wraps `requests.Session` for qBittorrent's WebUI API v2. Handles the auth-bypass case (HTTP 204 response).

**`backend/scheduler.py`** — thin APScheduler wrapper. The scheduler interval is re-read from the DB and applied live via `POST /api/scheduler/interval`.

### Frontend

Vue 3 SPA with Vite + Tailwind CSS. No component library — all components are hand-written Tailwind using a Dracula-inspired dark theme defined as CSS custom properties in `src/style.css` and mapped into Tailwind in `tailwind.config.js`. Icons are from `lucide-vue-next`.

**Navigation structure (Sidebar.vue):**
- Dashboard
- MODULES section: one nav item per module with an inline enable/disable toggle
- SYSTEM section (pinned bottom): Logs, Settings

**Panel routing** is handled in `App.vue` by a single `activePanel` ref. Panel components live in `src/components/panels/`. `SettingsPanel.vue` covers qBittorrent connection, scheduler interval, and managed categories (it was renamed from `QBittorrentPanel.vue`).

**`StepSlider.vue`** is a non-linear range slider used throughout module settings. It takes a `steps` array of `{label, value}` pairs from `src/sliderSteps.js` and emits the stepped value, not the raw index.

### Adding a new module

Four places must be updated in sync:
1. `backend/db.py` — add the module ID to `MODULE_IDS` and its default config to `DEFAULT_MODULE_CONFIGS`
2. `backend/manager.py` — add logic inside `run_manager()`
3. `frontend/src/components/Sidebar.vue` — add an entry to `MODULES` with a lucide icon
4. `frontend/src/components/panels/ModulePanel.vue` — add a `<template v-else-if>` branch for the module's settings UI
5. `frontend/src/App.vue` — add the ID to `MODULE_IDS`

### Data directory

`data/qmanagarr.db` — SQLite database holding all settings, logs, purge history, stall state, and exclusions. Always mount this in Docker; without it all config is lost on container restart.
