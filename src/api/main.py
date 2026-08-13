"""FastAPI Main Server Application for DocuMesh."""

import os
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.api.routes import all_routers
from src.api.middleware import TenantContextMiddleware
from src.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="DocuMesh Agentic Reconciliation Engine API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multi-Tenancy Middleware
app.add_middleware(TenantContextMiddleware)

# Group All Domain Routers under /api/v1
v1_router = APIRouter(prefix="/api/v1")
for r in all_routers:
    v1_router.include_router(r)

app.include_router(v1_router)

# UI Directory
UI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ui")


@app.get("/", response_class=HTMLResponse)
def root():
    index_file = os.path.join(UI_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>DocuMesh Engine API Running</h1><p>Visit /docs for Swagger UI</p>"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
