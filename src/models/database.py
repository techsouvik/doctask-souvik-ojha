"""SQLAlchemy Database Layer with Session Persistence & Checkpointing."""

import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import settings

Base = declarative_base()


class CheckpointModel(Base):
    """Database model for graph node state checkpoints."""
    __tablename__ = "checkpoints"

    seq_id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(128), index=True)
    tenant_id = Column(String(64), default="tenant_default", index=True)
    project_id = Column(String(64), index=True)
    node_name = Column(String(64))
    state_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentFactCacheModel(Base):
    """Persistent per-document fact cache for instant resumption without re-extraction."""
    __tablename__ = "document_fact_cache"

    id = Column(String(128), primary_key=True)
    tenant_id = Column(String(64), default="tenant_default", index=True)
    project_id = Column(String(64), index=True)
    doc_id = Column(String(128), index=True)
    checksum = Column(String(128), index=True)
    facts_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


_ENGINE = None
_SESSION_FACTORY = None


def get_db_engine():
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is None:
        db_url = settings.database_url
        if db_url.startswith("sqlite+aiosqlite"):
            db_url = db_url.replace("sqlite+aiosqlite", "sqlite")

        _ENGINE = create_engine(db_url, echo=False)
        Base.metadata.create_all(_ENGINE)
        _SESSION_FACTORY = sessionmaker(bind=_ENGINE)

    return _ENGINE


def save_checkpoint(project_id: str, node_name: str, state_data: Dict[str, Any], tenant_id: str = "tenant_default") -> str:
    """Save graph node checkpoint to database."""
    get_db_engine()
    if _SESSION_FACTORY is None:
        return ""

    session = _SESSION_FACTORY()
    try:
        cp_id = f"chk_{project_id}_{node_name}_{uuid.uuid4().hex[:8]}"
        cp = CheckpointModel(
            id=cp_id,
            tenant_id=tenant_id,
            project_id=project_id,
            node_name=node_name,
            state_json=json.dumps(state_data, default=str),
            created_at=datetime.utcnow()
        )
        session.add(cp)
        session.commit()
        return cp_id
    except Exception as e:
        session.rollback()
        print(f"Error saving checkpoint: {e}")
        return ""
    finally:
        session.close()


def load_latest_checkpoint(project_id: str, tenant_id: str = "tenant_default") -> Optional[Dict[str, Any]]:
    """Load latest checkpoint state for a project ordered by true sequence ID."""
    get_db_engine()
    if _SESSION_FACTORY is None:
        return None

    session = _SESSION_FACTORY()
    try:
        cp = session.query(CheckpointModel).filter(
            CheckpointModel.project_id == project_id,
            CheckpointModel.tenant_id == tenant_id
        ).order_by(CheckpointModel.seq_id.desc()).first()
        
        # Fallback if no tenant-scoped checkpoint
        if cp is None:
            cp = session.query(CheckpointModel).filter(
                CheckpointModel.project_id == project_id
            ).order_by(CheckpointModel.seq_id.desc()).first()

        if cp is not None and cp.state_json is not None:
            return json.loads(str(cp.state_json))
        return None
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
        return None
    finally:
        session.close()


def save_cached_facts_db(project_id: str, doc_id: str, checksum: str, facts: List[Dict[str, Any]], tenant_id: str = "tenant_default"):
    """Persist extracted facts for a document to database cache."""
    get_db_engine()
    if _SESSION_FACTORY is None:
        return

    session = _SESSION_FACTORY()
    try:
        cache_id = f"{tenant_id}_{project_id}_{checksum}"
        existing = session.query(DocumentFactCacheModel).filter(DocumentFactCacheModel.id == cache_id).first()
        if existing:
            existing.facts_json = json.dumps(facts, default=str)
        else:
            item = DocumentFactCacheModel(
                id=cache_id,
                tenant_id=tenant_id,
                project_id=project_id,
                doc_id=doc_id,
                checksum=checksum,
                facts_json=json.dumps(facts, default=str),
                created_at=datetime.utcnow()
            )
            session.add(item)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error saving fact cache: {e}")
    finally:
        session.close()


def load_cached_facts_db(project_id: str, checksum: str, tenant_id: str = "tenant_default") -> Optional[List[Dict[str, Any]]]:
    """Retrieve cached facts for a document from database."""
    get_db_engine()
    if _SESSION_FACTORY is None:
        return None

    session = _SESSION_FACTORY()
    try:
        cache_id = f"{tenant_id}_{project_id}_{checksum}"
        item = session.query(DocumentFactCacheModel).filter(DocumentFactCacheModel.id == cache_id).first()
        if item and item.facts_json:
            return json.loads(str(item.facts_json))
        return None
    except Exception as e:
        print(f"Error loading fact cache: {e}")
        return None
    finally:
        session.close()


def list_saved_projects_db(tenant_id: str = "tenant_default") -> List[str]:
    """List all unique project IDs persistently stored in database checkpoints."""
    get_db_engine()
    if _SESSION_FACTORY is None:
        return []

    session = _SESSION_FACTORY()
    try:
        results = session.query(CheckpointModel.project_id).distinct().all()
        return [r[0] for r in results if r[0]]
    except Exception as e:
        print(f"Error listing saved projects: {e}")
        return []
    finally:
        session.close()

