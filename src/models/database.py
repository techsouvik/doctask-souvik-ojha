"""SQLAlchemy Database Layer with Session Persistence & Checkpointing."""

import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import settings

Base = declarative_base()


class CheckpointModel(Base):
    """Database model for graph node state checkpoints."""
    __tablename__ = "checkpoints"

    seq_id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(128), index=True)
    project_id = Column(String(64), index=True)
    node_name = Column(String(64))
    state_json = Column(Text)
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


def save_checkpoint(project_id: str, node_name: str, state_data: Dict[str, Any]) -> str:
    """Save graph node checkpoint to database."""
    get_db_engine()
    if _SESSION_FACTORY is None:
        return ""

    session = _SESSION_FACTORY()
    try:
        cp_id = f"chk_{project_id}_{node_name}_{uuid.uuid4().hex[:8]}"
        cp = CheckpointModel(
            id=cp_id,
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


def load_latest_checkpoint(project_id: str) -> Optional[Dict[str, Any]]:
    """Load latest checkpoint state for a project ordered by true sequence ID."""
    get_db_engine()
    if _SESSION_FACTORY is None:
        return None

    session = _SESSION_FACTORY()
    try:
        cp = session.query(CheckpointModel).filter(CheckpointModel.project_id == project_id).order_by(CheckpointModel.seq_id.desc()).first()
        if cp is not None and cp.state_json is not None:
            return json.loads(str(cp.state_json))
        return None
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
        return None
    finally:
        session.close()
