"""LangGraph Cross-Run Memory Store Integration (LangGraph v1.2+ Store API)."""

from typing import Dict, Any, Optional, List
from langgraph.store.memory import InMemoryStore
from src.logging_config import get_logger

logger = get_logger("documesh.graph.store")


class DocuMeshCrossRunStore:
    """Cross-run persistent store for tenant preferences, entity alias maps, and audit playbooks."""

    def __init__(self):
        self.store = InMemoryStore()

    def put_preference(self, namespace: str, key: str, value: Dict[str, Any]):
        """Save cross-run preference or alias map."""
        self.store.put((namespace,), key, value)
        logger.info("store_preference_saved", namespace=namespace, key=key)

    def get_preference(self, namespace: str, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cross-run preference."""
        item = self.store.get((namespace,), key)
        if item and hasattr(item, "value"):
            return item.value
        return None

    def search_preferences(self, namespace: str, query: str = "") -> List[Dict[str, Any]]:
        """Search items in store namespace."""
        items = self.store.search((namespace,), query=query)
        return [item.value for item in items if hasattr(item, "value")]


global_cross_run_store = DocuMeshCrossRunStore()
