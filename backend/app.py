from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import settings
from backend.db.database import engine
from backend.db.models import Base

from backend.routes.predict import router as predict_router
from backend.routes.auth import router as auth_router
from backend.routes.simulate import router as simulate_router
from backend.routes.tasks import router as tasks_router
from backend.routes.progress import router as progress_router
from backend.routes.report import router as report_router
from backend.routes.profile import router as profile_router
from backend.routes.devices import router as devices_router
from backend.routes.alerts import router as alerts_router
from backend.routes.goals import router as goals_router
from backend.routes.gamification import router as gamification_router
from backend.routes.behavior import router as behavior_router
from backend.routes.chat import router as chat_router
from backend.routes.health_score import router as health_score_router
from backend.routes.ehr import router as ehr_router
from backend.routes.health_data import router as health_data_router
from backend.routes.ai import router as ai_router
from backend.routes.monitor import router as monitor_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Intelligent Preventive Healthcare Decision Support System",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "https://preventive-health-frontend.onrender.com",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(predict_router)
    app.include_router(simulate_router)
    app.include_router(tasks_router)
    app.include_router(progress_router)
    app.include_router(report_router)
    app.include_router(profile_router)
    app.include_router(devices_router)
    app.include_router(alerts_router)
    app.include_router(goals_router)
    app.include_router(gamification_router)
    app.include_router(behavior_router)
    app.include_router(chat_router)
    app.include_router(health_score_router)
    app.include_router(health_data_router)
    app.include_router(ehr_router)
    app.include_router(ai_router)
    app.include_router(monitor_router)

    @app.get("/health")
    def health():
        return {"ok": True, "service": "backend"}

    @app.on_event("startup")
    def _startup():
        Base.metadata.create_all(bind=engine)

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=True,
    )
