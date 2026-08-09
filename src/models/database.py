"""SQLAlchemy Database Layer with Session Persistence & Checkpointing."""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()


class DBProject(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, default="tenant_default")
    name = Column(String, nullable=False)
    document_root = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DBDocument(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    format = Column(String, nullable=False)
    checksum = Column(String, nullable=False, index=True)
    doc_type = Column(String, nullable=False)
    quarantined = Column(Boolean, default=False)
    quarantine_reason = Column(Text, nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    extracted_text = Column(Text, nullable=True)


class DBFact(Base):
    __tablename__ = "facts"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    doc_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    entity_key = Column(String, nullable=False, index=True)
    attribute = Column(String, nullable=False)
    raw_value = Column(String, nullable=False)
    normalized_value = Column(Text, nullable=True)
    unit = Column(String, nullable=True)
    confidence = Column(Float, default=1.0)
    grounded = Column(Boolean, default=True)
    citation_json = Column(Text, nullable=False)
    extracted_at = Column(DateTime, default=datetime.utcnow)


class DBFinding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    finding_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    source_a_json = Column(Text, nullable=False)
    source_b_json = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=False)
    status = Column(String, default="PRESENTED", index=True)
    feedback = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String, nullable=True)


class DBCheckpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    node_name = Column(String, nullable=False)
    state_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


_ENGINE = None
_SESSION_FACTORY = None


def get_db_session(db_path: str = "documesh.db") -> Session:
    """Get database session for SQLite."""
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is None:
        _ENGINE = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(_ENGINE)
        _SESSION_FACTORY = sessionmaker(bind=_ENGINE)
    assert _SESSION_FACTORY is not None
    return _SESSION_FACTORY()


def save_checkpoint(project_id: str, node_name: str, state_data: Dict[str, Any], db_path: str = "documesh.db"):
    """Persist pipeline checkpoint state to database."""
    session = get_db_session(db_path)
    try:
        cp_id = f"chk_{project_id}_{node_name}_{int(datetime.utcnow().timestamp())}"
        cp = DBCheckpoint(
            id=cp_id,
            project_id=project_id,
            node_name=node_name,
            state_json=json.dumps(state_data, default=str),
            created_at=datetime.utcnow()
        )
        session.add(cp)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error saving checkpoint: {e}")
    finally:
        session.close()


def load_latest_checkpoint(project_id: str, db_path: str = "documesh.db") -> Optional[Dict[str, Any]]:
    """Load latest checkpoint state for a project."""
    session = get_db_session(db_path)
    try:
        cp = session.query(DBCheckpoint).filter_by(project_id=project_id).order_by(DBCheckpoint.created_at.desc()).first()
        if cp is not None:
            raw_json = getattr(cp, "state_json", None)
            if raw_json:
                return json.loads(str(raw_json))
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
    finally:
        session.close()
    return None
