import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.routes import router
from config import APP_PORT
import os

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


@app.get("/", tags=["UI"])
def root():
    return FileResponse(os.path.join(static_dir, "index.html"))


if __name__ == "__main__":
    # HF Spaces sets PORT=7860; locally fall back to APP_PORT
    port = int(os.getenv("PORT", APP_PORT))
    reload_flag = os.getenv("ENV", "dev") == "dev"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload_flag)
