from fastapi import APIRouter
from pydantic import BaseModel

from .. import db, qbt

router = APIRouter(prefix="/api/settings", tags=["settings"])


class QBittorrentSettings(BaseModel):
    host: str
    username: str
    password: str


class CategoriesPayload(BaseModel):
    categories: list[str]


@router.get("/qbittorrent")
def get_qbt_settings():
    return {
        "host": db.get_setting("qbt_host"),
        "username": db.get_setting("qbt_username"),
        "password": db.get_setting("qbt_password"),
    }


@router.post("/qbittorrent")
def save_qbt_settings(settings: QBittorrentSettings):
    db.set_setting("qbt_host", settings.host.rstrip("/"))
    db.set_setting("qbt_username", settings.username)
    db.set_setting("qbt_password", settings.password)
    return {"status": "saved"}


@router.post("/qbittorrent/test")
def test_qbt_connection():
    host = db.get_setting("qbt_host")
    if not host:
        return {"success": False, "message": "No host configured — save settings first"}

    session, _ = qbt.get_session()
    if session:
        return {"success": True, "message": "Connected successfully"}

    return {"success": False, "message": f"Could not authenticate with {host} — check credentials and host URL"}


@router.get("/categories")
def get_categories():
    return {"categories": db.get_categories()}


@router.post("/categories")
def save_categories(payload: CategoriesPayload):
    # Strip whitespace, drop blanks, preserve order, deduplicate
    cats = list(dict.fromkeys(c.strip() for c in payload.categories if c.strip()))
    db.set_categories(cats)
    return {"categories": cats}
