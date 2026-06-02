from fastapi import APIRouter
from pydantic import BaseModel

from .. import db

router = APIRouter(prefix="/api/exclusions", tags=["exclusions"])


class ExclusionPayload(BaseModel):
    hash: str
    name: str
    note: str = ""


@router.get("")
def get_exclusions():
    return db.get_exclusions()


@router.post("")
def add_exclusion(payload: ExclusionPayload):
    db.add_exclusion(payload.hash, payload.name, payload.note)
    return db.get_exclusions()


@router.delete("/{torrent_hash}")
def remove_exclusion(torrent_hash: str):
    db.remove_exclusion(torrent_hash)
    return db.get_exclusions()
