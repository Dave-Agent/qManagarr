from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .. import db

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

router = APIRouter(prefix="/api/modules", tags=["modules"])


class ModuleUpdate(BaseModel):
    enabled: bool


def _check(module_id: str):
    if module_id not in db.MODULE_IDS:
        raise HTTPException(status_code=404, detail=f"Unknown module: {module_id}")


@router.get("")
def get_modules():
    return [
        {"id": mid, "enabled": db.get_module_enabled(mid), "config": db.get_module_config(mid)}
        for mid in db.MODULE_IDS
    ]


@router.post("/{module_id}")
def update_module(module_id: str, payload: ModuleUpdate):
    _check(module_id)
    db.set_module_enabled(module_id, payload.enabled)
    return {"id": module_id, "enabled": payload.enabled}


@router.get("/{module_id}/description")
def get_module_description(module_id: str):
    _check(module_id)
    path = CONTENT_DIR / f"{module_id}.md"
    return {"content": path.read_text() if path.exists() else ""}


@router.get("/{module_id}/config")
def get_module_config(module_id: str):
    _check(module_id)
    return db.get_module_config(module_id)


@router.post("/{module_id}/config")
def save_module_config(module_id: str, payload: dict[str, Any]):
    _check(module_id)
    db.set_module_config(module_id, payload)
    return db.get_module_config(module_id)
