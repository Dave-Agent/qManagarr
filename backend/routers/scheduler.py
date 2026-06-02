import threading

from fastapi import APIRouter
from pydantic import BaseModel

from .. import db
from ..manager import run_manager
from ..scheduler import scheduler

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])

DEFAULT_INTERVAL_SECS = 900  # 15 minutes


class IntervalPayload(BaseModel):
    interval_secs: int


@router.get("/interval")
def get_interval():
    raw = db.get_setting("scheduler_interval_secs")
    return {"interval_secs": int(raw) if raw else DEFAULT_INTERVAL_SECS}


@router.post("/interval")
def set_interval(payload: IntervalPayload):
    db.set_setting("scheduler_interval_secs", str(payload.interval_secs))
    scheduler.reschedule_job("manager", trigger="interval", seconds=payload.interval_secs)
    return {"interval_secs": payload.interval_secs}


@router.post("/run")
def run_now():
    threading.Thread(target=run_manager, daemon=True).start()
    return {"status": "started"}
