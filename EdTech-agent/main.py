import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routes import router
from config import APP_PORT
from db import is_configured as db_is_configured, get_pool
import logging
import os

log = logging.getLogger(__name__)

app = FastAPI(
    title="EdTech AI Tutor",
    description="An intelligent tutoring agent that personalizes learning for every student.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def _startup() -> None:
    if not db_is_configured():
        log.warning(
            "Supabase env vars are missing (DATABASE_URL, SUPABASE_URL, "
            "SUPABASE_SERVICE_ROLE_KEY). DB-backed endpoints will fail."
        )
        return
    try:
        # Eagerly open the pool so the first request isn't slow.
        get_pool()
        log.info("Postgres connection pool ready.")
    except Exception as e:
        log.error("Failed to initialize DB pool: %s", e)


@app.get("/", tags=["UI"])
def root():
    return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", APP_PORT))
    reload_flag = os.getenv("ENV", "dev") == "dev"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload_flag)
