# qManagarr

An automated torrent management tool for qBittorrent, designed for use alongside the *arr stack (Sonarr, Radarr). Runs as a background daemon with a web UI for configuration.

## Features

- **Dashboard** — connection status, metrics (active, all-time, watch list, purges), purge breakdown by module, and live torrent list
- **Completed Purge** — removes finished torrents after a configurable delay
- **EXE Killer** — deletes torrents containing executable files (security)
- **Error Killer** — purges torrents stuck in error or missing-file states
- **ETA Monitor** — kills torrents with a sustained bad ETA and low download speed
- **Stall Monitor** — removes torrents that haven't made meaningful progress
- Each module can be individually enabled/disabled and configured via non-linear sliders
- **Torrent exclusions** — toggle per-torrent on the dashboard; excluded torrents are ignored by all modules and auto-cleared when the torrent leaves qBittorrent
- **Managed categories** — configurable list of qBittorrent categories in scope (default: radarr, tv-sonarr)
- **Configurable scheduler** — set evaluation interval (5m–24h); trigger an immediate evaluation from the dashboard
- **Activity log** — filterable by level (All / Watch+ / Warning+)

---

## Deployment (Docker — recommended)

### Standalone

Create a `docker-compose.yml` — no source code required:

```yaml
services:
  qmanagarr:
    image: ghcr.io/dave-agent/qmanagarr:latest
    container_name: qmanagarr
    ports:
      - "7487:7487"
    volumes:
      - ./data:/app/data
    environment:
      - PUID=1000
      - PGID=1000
    restart: unless-stopped
```

```bash
docker compose up -d
```

The UI is available at `http://<server-ip>:7487`.

### Integrating into an existing media stack

Add qManagarr as a service in your existing `docker-compose.yml`:

```yaml
services:
  qmanagarr:
    image: ghcr.io/dave-agent/qmanagarr:latest
    container_name: qmanagarr
    ports:
      - "7487:7487"
    volumes:
      - ./qmanagarr/data:/app/data
    environment:
      - PUID=1000   # match your stack's user ID
      - PGID=1000   # match your stack's group ID
    restart: unless-stopped
    networks:
      - your_media_network
```

When qBittorrent is on the same Docker network, set the host URL in the qManagarr UI to `http://<qbittorrent-container-name>:<port>` rather than `localhost`.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PUID` | `1000` | User ID the process runs as |
| `PGID` | `1000` | Group ID the process runs as |

### Volumes

| Path | Description |
|------|-------------|
| `/app/data` | SQLite database — all settings and history. **Mount this to persist data across container restarts.** |
| `/app/backend/content` | Module description markdown files. Mount this if you want to edit the in-app module descriptions without rebuilding the image. |

---

## Development Setup

### Requirements

- Python 3.11+
- Node.js 18+
- [UV](https://github.com/astral-sh/uv)

### Backend

```bash
uv venv
uv pip install -r requirements.txt
.venv/bin/uvicorn backend.main:app --port 7487 --reload
```

API available at `http://localhost:7487`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at `http://localhost:5173`

The Vite dev server proxies `/api` requests to the backend automatically.

### Production build (without Docker)

```bash
cd frontend && npm run build
.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 7487
```

---

## Configuration

All settings are configured through the web UI and persisted to `data/qmanagarr.db`. No config files to edit.

---

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Skeleton, qBittorrent connection settings | ✅ Complete |
| 2 | Live torrent list | ✅ Complete |
| 3 | Core manager daemon + log viewer | ✅ Complete |
| 4 | Module enable/disable toggles | ✅ Complete |
| 5 | Per-module settings (non-linear sliders) | ✅ Complete |
| 6 | Dashboard with metrics + torrent list | ✅ Complete |
| 7 | Torrent exclusions | ✅ Complete |
| 8 | Configurable scheduler interval + Evaluate Now | ✅ Complete |
| 9 | Docker container (multi-stage, PUID/PGID) | ✅ Complete |
