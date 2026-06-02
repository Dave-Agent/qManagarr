from fastapi import APIRouter, HTTPException
from .. import db, qbt

router = APIRouter(prefix="/api/torrents", tags=["torrents"])


@router.get("")
def get_torrents():
    session, host = qbt.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Not connected to qBittorrent — check connection settings")

    res = session.get(f"{host}/api/v2/torrents/info", params={"filter": "all"}, timeout=10)
    all_torrents = res.json()

    managed = {c.lower() for c in db.get_categories()}
    return [t for t in all_torrents if (t.get("category") or "").lower() in managed]
