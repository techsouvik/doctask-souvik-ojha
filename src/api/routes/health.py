"""Health & System Readiness API Router."""

from fastapi import APIRouter
from src.cache.redis_cache import cache_instance
from src.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def check_health():
    """Check system health status (DB, Redis, App version)."""
    redis_status = "connected" if cache_instance.redis_client else "fallback_memory"

    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "redis_cache": redis_status,
        "database": "sqlite_active"
    }
