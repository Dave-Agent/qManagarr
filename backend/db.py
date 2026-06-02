import json
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "qmanagarr.db"

LOG_RETENTION_SECS = 30 * 24 * 3600  # 30 days


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = _connect()
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stalls (
            hash                 TEXT PRIMARY KEY,
            downloaded_at_start  INTEGER,
            first_stalled_at     INTEGER,
            bad_eta_since        INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            level     TEXT    NOT NULL DEFAULT 'INFO',
            message   TEXT    NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seen_torrents (
            hash       TEXT    PRIMARY KEY,
            first_seen INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purge_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            hash      TEXT    NOT NULL,
            name      TEXT    NOT NULL,
            module_id TEXT    NOT NULL,
            category  TEXT    NOT NULL DEFAULT ''
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exclusions (
            hash     TEXT    PRIMARY KEY,
            name     TEXT    NOT NULL,
            added_at INTEGER NOT NULL,
            note     TEXT    NOT NULL DEFAULT ''
        )
    ''')

    # Add watch flag columns to stalls (safe to run on existing DBs)
    for col in ("on_stall_watch INTEGER NOT NULL DEFAULT 0",
                "on_eta_watch   INTEGER NOT NULL DEFAULT 0"):
        try:
            cursor.execute(f"ALTER TABLE stalls ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass  # column already exists

    conn.commit()
    conn.close()


# --- Settings ---

def get_setting(key: str, default: str = "") -> str:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default


def set_setting(key: str, value: str):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()


# --- Logs ---

def write_log(message: str, level: str = "INFO"):
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)",
        (int(time.time()), level, message)
    )
    conn.commit()
    conn.close()


def get_logs(limit: int = 200) -> list[dict]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, timestamp, level, message FROM logs ORDER BY timestamp DESC, id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def purge_old_logs():
    cutoff = int(time.time()) - LOG_RETENTION_SECS
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logs WHERE timestamp < ?", (cutoff,))
    conn.commit()
    conn.close()


# --- Modules ---

MODULE_IDS = ['completed-purge', 'exe-killer', 'error-killer', 'eta-monitor', 'stall-monitor']

DEFAULT_MODULE_CONFIGS: dict[str, dict] = {
    'completed-purge': {
        'purge_delay': 10800,                                       # 3 hours
    },
    'exe-killer': {
        'bad_extensions': ['.exe', '.scr'],
    },
    'error-killer': {
        'error_states': ['error', 'missingFiles', 'unregistered'],
    },
    'eta-monitor': {
        'max_eta_secs':         2592000,    # 30 days
        'eta_threshold_secs':   900,        # 15 mins — age before ETA is checked
        'eta_grace_secs':       1800,       # 30 mins — sustained bad ETA before action
        'min_active_speed':     51200,      # 50 KB/s
        'eta_ignore_progress':  0.90,       # ignore ETA logic above 90%
    },
    'stall-monitor': {
        'stall_check_secs':         3600,   # 1 hour
        'progress_threshold_bytes': 102400, # 100 KB
    },
}


def get_module_enabled(module_id: str) -> bool:
    return get_setting(f"module_{module_id}_enabled", "1") == "1"


def set_module_enabled(module_id: str, enabled: bool):
    set_setting(f"module_{module_id}_enabled", "1" if enabled else "0")


def get_module_config(module_id: str) -> dict:
    raw = get_setting(f"module_{module_id}_config")
    if not raw:
        return DEFAULT_MODULE_CONFIGS.get(module_id, {}).copy()
    # Merge with defaults so new keys added in future updates appear automatically
    defaults = DEFAULT_MODULE_CONFIGS.get(module_id, {})
    saved = json.loads(raw)
    return {**defaults, **saved}


def set_module_config(module_id: str, config: dict):
    set_setting(f"module_{module_id}_config", json.dumps(config))


# --- Categories ---

_DEFAULT_CATEGORIES = ["radarr", "tv-sonarr"]


def get_categories() -> list[str]:
    raw = get_setting("target_categories")
    if not raw:
        return _DEFAULT_CATEGORIES[:]
    return json.loads(raw)


def set_categories(cats: list[str]):
    set_setting("target_categories", json.dumps(cats))


# --- Exclusions ---

def get_exclusions() -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT hash, name, added_at, note FROM exclusions ORDER BY added_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_excluded_hashes() -> set[str]:
    conn = _connect()
    rows = conn.execute("SELECT hash FROM exclusions").fetchall()
    conn.close()
    return {r[0] for r in rows}


def add_exclusion(hash: str, name: str, note: str = ""):
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO exclusions (hash, name, added_at, note) VALUES (?, ?, ?, ?)",
        (hash, name, int(time.time()), note),
    )
    conn.commit()
    conn.close()


def remove_exclusion(hash: str):
    conn = _connect()
    conn.execute("DELETE FROM exclusions WHERE hash = ?", (hash,))
    conn.commit()
    conn.close()


# --- Dashboard metrics ---

def get_seen_count() -> int:
    conn = _connect()
    row = conn.execute("SELECT COUNT(*) FROM seen_torrents").fetchone()
    conn.close()
    return row[0]


def get_watch_counts() -> tuple[int, int]:
    """Returns (stall_watch_count, eta_watch_count)."""
    conn = _connect()
    row = conn.execute(
        "SELECT SUM(on_stall_watch), SUM(on_eta_watch) FROM stalls"
    ).fetchone()
    conn.close()
    return (row[0] or 0, row[1] or 0)


def get_purge_stats() -> dict[str, dict[str, int]]:
    """Returns {module_id: {last_24h, all_time}} for all modules."""
    cutoff_24h = int(time.time()) - 86400
    conn = _connect()

    all_time = dict(conn.execute(
        "SELECT module_id, COUNT(*) FROM purge_events GROUP BY module_id"
    ).fetchall())

    last_24h = dict(conn.execute(
        "SELECT module_id, COUNT(*) FROM purge_events WHERE timestamp >= ? GROUP BY module_id",
        (cutoff_24h,)
    ).fetchall())

    conn.close()
    return {
        mid: {"last_24h": last_24h.get(mid, 0), "all_time": all_time.get(mid, 0)}
        for mid in MODULE_IDS
    }


# --- Stalls (used by manager) ---

def get_conn() -> sqlite3.Connection:
    """Returns a raw connection for the manager to use within a single run."""
    return _connect()
