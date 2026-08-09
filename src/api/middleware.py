"""FastAPI Middleware for Multi-Tenancy & Request Context Ingestion."""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from src.logging_config import get_logger

logger = get_logger("documesh.api.middleware")


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce tenant_id & project_id context scoping on API requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4())[:8])
        tenant_id = request.headers.get("X-Tenant-ID", "tenant_default")
        project_id = request.headers.get("X-Project-ID", "proj_greenfield_tech_park")

        request.state.tenant_id = tenant_id
        request.state.project_id = project_id
        request.state.correlation_id = correlation_id

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000.0
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Tenant-ID"] = tenant_id

        logger.info(
            "api_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            tenant_id=tenant_id,
            project_id=project_id,
            correlation_id=correlation_id
        )

        return response
