"""SQLAlchemy Database Schema for DocuMesh."""

import json
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class DBProject(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
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
    normalized_value = Column(Text, nullable=True)  # JSON serialized
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


def init_db(db_path: str = "documesh.db"):
    """Initialize database tables synchronously."""
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()
