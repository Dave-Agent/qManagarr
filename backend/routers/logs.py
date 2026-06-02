from fastapi import APIRouter, Query
from .. import db

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
def get_logs(limit: int = Query(200, ge=1, le=1000)):
    return db.get_logs(limit)
