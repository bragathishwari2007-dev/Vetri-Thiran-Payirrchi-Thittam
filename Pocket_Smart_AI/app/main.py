



from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.routes import (
    auth_routes,
    history_routes,
    pages,
    planner_routes,
)


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="AI-powered budget and recommendation assistant.",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static",
)


app.include_router(pages.router)
app.include_router(auth_routes.router)
app.include_router(planner_routes.router)
app.include_router(history_routes.router)


@app.get(
    "/api/health",
    tags=["utility"],
)
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "gemini_configured": bool(
            settings.gemini_api_key
        ),
        "model": settings.gemini_model,
    }