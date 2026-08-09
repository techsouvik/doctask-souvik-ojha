"""FastAPI Main Server Application for DocuMesh."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from src.api.router import router as api_router
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

# Include API Router
app.include_router(api_router)

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
