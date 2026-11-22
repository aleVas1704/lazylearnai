from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.core.timing import TimingMiddleware
from backend.modules.demo.routes import router as demo_router
from backend.modules.guided_math.routes import router as guided_math_router
from backend.modules.health.routes import router as health_router
from backend.modules.student_access.routes import router as student_access_router
from backend.modules.student_dashboard.routes import router as student_dashboard_router
from backend.modules.student_task_chat.routes import router as student_task_chat_router
from backend.modules.teacher_portal.routes import router as teacher_portal_router

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

app = FastAPI(title="Base de hackathon", version="0.1.0")
app.add_middleware(TimingMiddleware)
app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")
app.state.templates = Jinja2Templates(directory=FRONTEND / "templates")
app.include_router(health_router)
app.include_router(demo_router)
app.include_router(student_access_router)
app.include_router(student_dashboard_router)
app.include_router(student_task_chat_router)
app.include_router(teacher_portal_router)
app.include_router(guided_math_router)
