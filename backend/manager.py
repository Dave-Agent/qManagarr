import time

from . import db, qbt

IGNORE_STATES = ['queuedDL', 'checkingDL', 'allocating']


def run_manager():
    db.purge_old_logs()
    db.set_setting("last_run_at", str(int(time.time())))

    _buffer: list[tuple[str, str]] = []

    def log(message: str, level: str = "INFO"):
        _buffer.append((level, message))

    def flush():
        for level, msg in _buffer:
            db.write_log(msg, level)

    session, host = qbt.get_session()
    if not session:
        log("Cannot connect to qBittorrent — check connection settings", "ERROR")
        flush()
        return

    target_categories = {c.lower() for c in db.get_categories()}
    excluded_hashes   = db.get_excluded_hashes()
    enabled = {mid: db.get_module_enabled(mid) for mid in db.MODULE_IDS}
    cfg     = {mid: db.get_module_config(mid)  for mid in db.MODULE_IDS}

    completed_purge_delay = cfg['completed-purge']['purge_delay']
    exe_bad_extensions    = tuple(cfg['exe-killer']['bad_extensions'])
    error_states          = cfg['error-killer']['error_states']
    eta_max_secs          = cfg['eta-monitor']['max_eta_secs']
    eta_threshold_secs    = cfg['eta-monitor']['eta_threshold_secs']
    eta_grace_secs        = cfg['eta-monitor']['eta_grace_secs']
    eta_min_speed         = cfg['eta-monitor']['min_active_speed']
    eta_ignore_progress   = cfg['eta-monitor']['eta_ignore_progress']
    stall_check_secs      = cfg['stall-monitor']['stall_check_secs']
    stall_threshold_bytes = cfg['stall-monitor']['progress_threshold_bytes']

    conn = db.get_conn()
    cursor = conn.cursor()
    actions_taken = 0
    stalled_count = 0

    try:
        res = session.get(f"{host}/api/v2/torrents/info", params={"filter": "all"}, timeout=10)
        torrents = res.json()

        if not torrents:
            log("Nothing to do: Queue is empty.")
            return

        # Clean stale DB entries and reset watch flags for this run
        current_hashes = [t["hash"] for t in torrents]
        placeholders = ",".join("?" * len(current_hashes))
        cursor.execute(f"DELETE FROM stalls WHERE hash NOT IN ({placeholders})", current_hashes)
        cursor.execute(f"DELETE FROM exclusions WHERE hash NOT IN ({placeholders})", current_hashes)
        cursor.execute("UPDATE stalls SET on_stall_watch=0, on_eta_watch=0")

        for t in torrents:
            cat = (t.get("category") or "").lower()
            if cat not in target_categories:
                continue
            if t["hash"] in excluded_hashes:
                continue

            t_hash     = t["hash"]
            t_name     = t["name"]
            t_state    = t.get("state")
            t_progress = t.get("progress", 0)
            t_dl_bytes = t.get("downloaded", 0)
            t_done_at  = t.get("completion_on", 0)
            t_eta      = t.get("eta", 0)
            t_added_on = t.get("added_on", int(time.time()))
            t_dl_speed = t.get("dlspeed", 0)
            now        = int(time.time())

            cursor.execute(
                "INSERT OR IGNORE INTO stalls (hash, downloaded_at_start, first_stalled_at, bad_eta_since) VALUES (?, ?, ?, NULL)",
                (t_hash, t_dl_bytes, now),
            )
            cursor.execute(
                "INSERT OR IGNORE INTO seen_torrents (hash, first_seen) VALUES (?, ?)",
                (t_hash, now),
            )

            # 1. COMPLETED PURGE
            if enabled['completed-purge'] and t_progress >= 1.0 and t_done_at > 0:
                if (now - t_done_at) > completed_purge_delay:
                    log(f"CLEANUP: '{t_name}' completed. Removing.", "WARNING")
                    _delete(session, host, t_hash, t_name, cat, 'completed-purge', cursor, now)
                    actions_taken += 1
                    continue

            # 2. EXE KILLER
            if enabled['exe-killer'] and t_state != "metaDL":
                files = session.get(
                    f"{host}/api/v2/torrents/files", params={"hash": t_hash}, timeout=10
                ).json()
                if any(f.get("name", "").lower().endswith(exe_bad_extensions) for f in files):
                    log(f"SECURITY: executable found in '{t_name}'. Purging.", "ERROR")
                    _delete(session, host, t_hash, t_name, cat, 'exe-killer', cursor, now)
                    actions_taken += 1
                    continue

            # 3. ERROR KILLER
            if enabled['error-killer'] and t_state in error_states:
                log(f"ERROR: '{t_name}' is in state '{t_state}'. Purging.", "WARNING")
                _delete(session, host, t_hash, t_name, cat, 'error-killer', cursor, now)
                actions_taken += 1
                continue

            # 4. HYBRID ETA MONITOR
            if enabled['eta-monitor'] and t_state not in IGNORE_STATES:
                age = now - t_added_on
                is_bad_eta = (
                    age > eta_threshold_secs
                    and 0 < t_eta > eta_max_secs
                    and t_progress < eta_ignore_progress
                )

                if t_progress > 0.95:
                    grace = 999_999_999
                elif t_progress > 0.85:
                    grace = 4 * 3600
                else:
                    grace = eta_grace_secs

                cursor.execute("SELECT bad_eta_since FROM stalls WHERE hash=?", (t_hash,))
                row = cursor.fetchone()
                bad_eta_since = row["bad_eta_since"] if row else None

                if is_bad_eta:
                    cursor.execute("UPDATE stalls SET on_eta_watch=1 WHERE hash=?", (t_hash,))
                    if bad_eta_since:
                        duration = now - bad_eta_since
                        if duration > grace and t_dl_speed < eta_min_speed:
                            log(
                                f"SLOW: '{t_name}' bad ETA for {duration // 60}m "
                                f"({t_progress * 100:.1f}%, {t_dl_speed // 1024} KB/s). Purging.",
                                "WARNING",
                            )
                            _delete(session, host, t_hash, t_name, cat, 'eta-monitor', cursor, now)
                            actions_taken += 1
                            continue
                        else:
                            mins_left = (grace - duration) // 60
                            log(f"WATCHING ETA: '{t_name[:40]}' ({mins_left}m left)", "WATCH")
                    else:
                        cursor.execute("UPDATE stalls SET bad_eta_since=? WHERE hash=?", (now, t_hash))
                        log(f"BAD ETA DETECTED: '{t_name[:40]}' — starting grace timer.", "WATCH")
                else:
                    cursor.execute("UPDATE stalls SET bad_eta_since=NULL WHERE hash=?", (t_hash,))

            # 5. STALL MONITOR
            if not enabled['stall-monitor']:
                continue

            if t_state in IGNORE_STATES or t_progress >= 1.0:
                cursor.execute("UPDATE stalls SET first_stalled_at=? WHERE hash=?", (now, t_hash))
                continue

            cursor.execute(
                "SELECT downloaded_at_start, first_stalled_at FROM stalls WHERE hash=?", (t_hash,)
            )
            row = cursor.fetchone()
            if row:
                bytes_gained = t_dl_bytes - row["downloaded_at_start"]
                secs_stalled = now - row["first_stalled_at"]

                if bytes_gained < stall_threshold_bytes:
                    if secs_stalled >= stall_check_secs:
                        log(f"STALL: '{t_name}' insufficient progress. Purging.", "WARNING")
                        _delete(session, host, t_hash, t_name, cat, 'stall-monitor', cursor, now)
                        actions_taken += 1
                    else:
                        stalled_count += 1
                        cursor.execute("UPDATE stalls SET on_stall_watch=1 WHERE hash=?", (t_hash,))
                        mins_left = (stall_check_secs - secs_stalled) // 60
                        log(f"WATCHING STALL: '{t_name[:40]}' ({mins_left}m left)", "WATCH")
                else:
                    cursor.execute(
                        "UPDATE stalls SET downloaded_at_start=?, first_stalled_at=? WHERE hash=?",
                        (t_dl_bytes, now, t_hash),
                    )

        conn.commit()

        if actions_taken == 0:
            log(f"All downloads healthy. ({stalled_count} on watch list)")

    except Exception as e:
        log(f"Runtime error: {e}", "ERROR")
    finally:
        conn.close()
        flush()


def _delete(session, host: str, t_hash: str, t_name: str, cat: str,
            module_id: str, cursor, now: int):
    session.post(
        f"{host}/api/v2/torrents/delete",
        data={"hashes": t_hash, "deleteFiles": "true"},
    )
    cursor.execute("DELETE FROM stalls WHERE hash=?", (t_hash,))
    cursor.execute(
        "INSERT INTO purge_events (timestamp, hash, name, module_id, category) VALUES (?, ?, ?, ?, ?)",
        (now, t_hash, t_name, module_id, cat),
    )
