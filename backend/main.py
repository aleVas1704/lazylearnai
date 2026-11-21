from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.modules.demo.routes import router as demo_router
from backend.modules.health.routes import router as health_router

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

app = FastAPI(title="Base de hackathon", version="0.1.0")
app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")
app.state.templates = Jinja2Templates(directory=FRONTEND / "templates")
app.include_router(health_router)
app.include_router(demo_router)
