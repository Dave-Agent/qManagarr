from fastapi import APIRouter

from .. import db, qbt

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

_MODULE_LABELS = {
    'completed-purge': 'Completed Purge',
    'exe-killer':      'EXE Killer',
    'error-killer':    'Error Killer',
    'eta-monitor':     'ETA Monitor',
    'stall-monitor':   'Stall Monitor',
}


@router.get("")
def get_dashboard():
    session, _ = qbt.get_session()
    connected = session is not None

    last_run_raw = db.get_setting("last_run_at")
    last_run = int(last_run_raw) if last_run_raw else None

    all_time_count        = db.get_seen_count()
    watch_stall, watch_eta = db.get_watch_counts()
    purge_stats           = db.get_purge_stats()

    purged_24h    = sum(v["last_24h"] for v in purge_stats.values())
    purged_all    = sum(v["all_time"] for v in purge_stats.values())

    breakdown = [
        {
            "module_id": mid,
            "label":     _MODULE_LABELS[mid],
            "last_24h":  purge_stats[mid]["last_24h"],
            "all_time":  purge_stats[mid]["all_time"],
        }
        for mid in db.MODULE_IDS
    ]

    return {
        "connection": {"connected": connected},
        "last_run":   last_run,
        "metrics": {
            "all_time_count": all_time_count,
            "watch_stall":    watch_stall,
            "watch_eta":      watch_eta,
            "purged_24h":     purged_24h,
            "purged_all_time": purged_all,
        },
        "purge_breakdown": breakdown,
    }
