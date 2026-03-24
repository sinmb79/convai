from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.api import (
    auth, projects, tasks, daily_reports, reports, inspections,
    weather, rag, kakao, permits, quality, settings as settings_router,
    agents, evms, vision, geofence, completion, documents, portal,
)
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="CONAI API",
        description="소형 건설업체를 위한 AI 기반 토목공사 통합관리 플랫폼",
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routers
    api_prefix = "/api/v1"
    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(projects.router, prefix=api_prefix)
    app.include_router(tasks.router, prefix=api_prefix)
    app.include_router(daily_reports.router, prefix=api_prefix)
    app.include_router(reports.router, prefix=api_prefix)
    app.include_router(inspections.router, prefix=api_prefix)
    app.include_router(weather.router, prefix=api_prefix)
    app.include_router(rag.router, prefix=api_prefix)
    app.include_router(kakao.router, prefix=api_prefix)
    app.include_router(permits.router, prefix=api_prefix)
    app.include_router(quality.router, prefix=api_prefix)
    app.include_router(agents.router, prefix=api_prefix)
    app.include_router(evms.router, prefix=api_prefix)
    app.include_router(vision.router, prefix=api_prefix)
    app.include_router(geofence.router, prefix=api_prefix)
    app.include_router(completion.router, prefix=api_prefix)
    app.include_router(documents.router, prefix=api_prefix)
    app.include_router(portal.router, prefix=api_prefix)
    app.include_router(settings_router.router, prefix=api_prefix)

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()
