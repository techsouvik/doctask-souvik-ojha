"""Modular API Route Package for DocuMesh Engine."""

from src.api.routes.health import router as health_router
from src.api.routes.projects import router as projects_router
from src.api.routes.documents import router as documents_router
from src.api.routes.findings import router as findings_router
from src.api.routes.sessions import router as sessions_router
from src.api.routes.search import router as search_router
from src.api.routes.artifacts import router as artifacts_router
from src.api.routes.skills import router as skills_router
from src.api.routes.evals import router as evals_router
from src.api.routes.settings import router as settings_router

all_routers = [
    health_router,
    projects_router,
    documents_router,
    findings_router,
    sessions_router,
    search_router,
    artifacts_router,
    skills_router,
    evals_router,
    settings_router,
]
