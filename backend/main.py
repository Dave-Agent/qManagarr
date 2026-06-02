import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import init_db, get_setting
from .manager import run_manager
from .scheduler import scheduler
from .routers import dashboard, exclusions, logs, modules, settings, scheduler as scheduler_router, torrents


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    interval_secs = int(get_setting("scheduler_interval_secs") or 900)
    scheduler.add_job(run_manager, "interval", seconds=interval_secs, id="manager")
    scheduler.start()
    threading.Thread(target=run_manager, daemon=True).start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="qManagarr", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(exclusions.router)
app.include_router(settings.router)
app.include_router(modules.router)
app.include_router(scheduler_router.router)
app.include_router(torrents.router)
app.include_router(logs.router)

frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
