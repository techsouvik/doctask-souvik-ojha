"""Redis Cache & Distributed Lock Layer with graceful In-Memory Fallback."""

import json
import time
from typing import Optional, Any, Dict
from src.logging_config import get_logger

logger = get_logger("documesh.cache")

try:
    import redis as redis_lib
    _HAS_REDIS = True
except ImportError:
    redis_lib = None
    _HAS_REDIS = False


class DocuMeshCache:
    """Hybrid Redis / In-Memory Cache with TTL and Lock support."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = None
        self._memory_cache: Dict[str, Any] = {}
        self._memory_cache_expiry: Dict[str, float] = {}
        self._memory_locks: Dict[str, float] = {}

        if _HAS_REDIS and redis_lib is not None:
            try:
                client = redis_lib.Redis.from_url(redis_url, socket_connect_timeout=1.0, decode_responses=True)
                client.ping()
                self.redis_client = client
                logger.info("redis_connected", redis_url=redis_url)
            except Exception as e:
                logger.warning("redis_connection_failed_using_memory_fallback", error=str(e))
                self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis or Memory cache."""
        if self.redis_client:
            try:
                val = self.redis_client.get(key)
                return json.loads(val) if val else None
            except Exception as e:
                logger.warning("redis_get_error_fallback_memory", key=key, error=str(e))

        # Memory fallback
        if key in self._memory_cache:
            if time.time() < self._memory_cache_expiry.get(key, float("inf")):
                return self._memory_cache[key]
            else:
                del self._memory_cache[key]
                del self._memory_cache_expiry[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Set value in Redis or Memory cache."""
        if self.redis_client:
            try:
                self.redis_client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
                return
            except Exception as e:
                logger.warning("redis_set_error_fallback_memory", key=key, error=str(e))

        # Memory fallback
        self._memory_cache[key] = value
        self._memory_cache_expiry[key] = time.time() + ttl_seconds

    def get_cached_fact(self, checksum: str) -> Optional[Any]:
        """Get cached facts by document checksum."""
        return self.get(f"fact:{checksum}")

    def set_cached_fact(self, checksum: str, facts: Any, ttl_seconds: int = 86400):
        """Cache facts by document checksum."""
        self.set(f"fact:{checksum}", facts, ttl_seconds)

    def acquire_lock(self, lock_key: str, ttl_seconds: int = 30) -> bool:
        """Acquire a distributed lock."""
        full_key = f"lock:{lock_key}"
        if self.redis_client:
            try:
                acquired = self.redis_client.set(full_key, "LOCKED", nx=True, ex=ttl_seconds)
                return bool(acquired)
            except Exception as e:
                logger.warning("redis_lock_error_fallback_memory", lock_key=lock_key, error=str(e))

        # Memory fallback
        now = time.time()
        if full_key in self._memory_locks:
            if now < self._memory_locks[full_key]:
                return False  # Lock held

        self._memory_locks[full_key] = now + ttl_seconds
        return True

    def release_lock(self, lock_key: str):
        """Release a distributed lock."""
        full_key = f"lock:{lock_key}"
        if self.redis_client:
            try:
                self.redis_client.delete(full_key)
                return
            except Exception as e:
                logger.warning("redis_unlock_error", lock_key=lock_key, error=str(e))

        if full_key in self._memory_locks:
            del self._memory_locks[full_key]


# Global singleton instance
cache_instance = DocuMeshCache()
