"""
Sovereign AI Workbench Database Schema (SQLAlchemy + SQLite/PostgreSQL).
SIH26117 - MRPL Sovereign AI Workbench.

Defines all 16 core relational models required by the SIH26117 specification:
1. users
2. roles
3. permissions
4. sessions
5. devices
6. documents
7. document_versions
8. document_chunks
9. knowledge_bases
10. knowledge_base_documents
11. agent_runs
12. agent_steps
13. chat_sessions
14. chat_messages
15. audit_logs
16. model_configs
"""

import os
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, Text,
    DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from app.config import settings

Base = declarative_base()


# ==============================================================================
# 1. Identity, Access, & Roles
# ==============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(128), nullable=True)
    role = Column(String(32), nullable=False, default="Analyst")  # Admin, Engineer, Analyst, Viewer
    department = Column(String(64), nullable=False, default="Refinery Operations")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="owner")


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(String(32), primary_key=True)
    role_name = Column(String(64), unique=True, nullable=False)
    description = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(String(32), ForeignKey("roles.role_id"), nullable=False)
    permission_name = Column(String(64), nullable=False)
    allowed = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("role_id", "permission_name", name="uq_role_perm"),)


# ==============================================================================
# 2. Endpoint Device & Session Management (Laptop Theft Scenario)
# ==============================================================================

class Device(Base):
    __tablename__ = "devices"

    device_id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    device_name = Column(String(128), nullable=False)
    device_type = Column(String(64), default="Laptop / Workstation")
    ip_address = Column(String(64), default="127.0.0.1")
    user_agent = Column(String(256), nullable=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_trusted = Column(Boolean, default=True)
    is_revoked = Column(Boolean, default=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(64), nullable=True)

    user = relationship("User", back_populates="devices")
    sessions = relationship("Session", back_populates="device")


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), nullable=True, index=True)
    token_hash = Column(String(128), nullable=False, index=True)
    ip_address = Column(String(64), default="127.0.0.1")
    user_agent = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    last_active = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_revoked = Column(Boolean, default=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(64), nullable=True)

    user = relationship("User", back_populates="sessions")
    device = relationship("Device", back_populates="sessions")


# ==============================================================================
# 3. Document Repository & Encrypted Chunks
# ==============================================================================

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True)
    filename = Column(String(256), nullable=False)
    original_filename = Column(String(256), nullable=False)
    encrypted_path = Column(String(512), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    mime_type = Column(String(64), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    page_count = Column(Integer, default=1)
    owner_id = Column(String(64), ForeignKey("users.id"), nullable=True)
    department = Column(String(64), default="Refinery Operations")
    classification = Column(String(32), default="Confidential")  # Confidential, Restricted, Internal
    access_permissions = Column(Text, default='["Admin", "Engineer", "Analyst"]')  # JSON roles
    ocr_status = Column(String(32), default="NOT_REQUIRED")  # NOT_REQUIRED, PENDING, COMPLETED, FAILED
    processing_status = Column(String(32), default="UPLOADED")  # UPLOADED, OCR, EMBEDDING, INDEXED, FAILED
    extracted_text_preview = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    version_id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    version_num = Column(Integer, default=1)
    encrypted_path = Column(String(512), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    change_summary = Column(String(256), default="Initial confidential upload")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(64), nullable=True)

    document = relationship("Document", back_populates="versions")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, default=1)
    section_header = Column(String(256), nullable=True)
    chunk_text = Column(Text, nullable=False)
    embedding_id = Column(String(64), nullable=True)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="chunks")


# ==============================================================================
# 4. Knowledge Bases & Mappings
# ==============================================================================

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    kb_id = Column(String(64), primary_key=True)
    name = Column(String(128), unique=True, nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    department = Column(String(64), default="Refinery Operations")
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class KnowledgeBaseDocument(Base):
    __tablename__ = "knowledge_base_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kb_id = Column(String(64), ForeignKey("knowledge_bases.kb_id"), nullable=False, index=True)
    document_id = Column(String(64), ForeignKey("documents.id"), nullable=False, index=True)
    indexed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    chunk_count = Column(Integer, default=0)
    status = Column(String(32), default="INDEXED")  # PENDING, INDEXED, FAILED

    __table_args__ = (UniqueConstraint("kb_id", "document_id", name="uq_kb_doc"),)


# ==============================================================================
# 5. Agent Orchestrator Runs & Step Traces
# ==============================================================================

class AgentRun(Base):
    __tablename__ = "agent_runs"

    run_id = Column(String(64), primary_key=True)
    task_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=True)
    query = Column(Text, nullable=False)
    coordinator_plan = Column(Text, nullable=True)  # JSON list of agents and steps
    status = Column(String(32), default="PLANNING")  # PLANNING, EXECUTING, VERIFYING, COMPLETED, FAILED
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    final_verdict = Column(String(32), default="PENDING")
    human_verification_required = Column(Boolean, default=False)
    confidence = Column(Float, default=0.0)
    deliverable_path = Column(String(512), nullable=True)
    error = Column(Text, nullable=True)


class AgentStep(Base):
    __tablename__ = "agent_steps"

    step_id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("agent_runs.run_id"), nullable=False, index=True)
    step_index = Column(Integer, nullable=False)
    agent_name = Column(String(64), nullable=False)  # Coordinator, Retrieval, DocumentAnalyst, DataAnalysis, RiskAnomaly, MultimodalInspection, ReportGeneration
    action = Column(String(128), nullable=False)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    status = Column(String(32), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    execution_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ==============================================================================
# 6. Conversational Chat & Citations
# ==============================================================================

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String(64), primary_key=True)
    user_id = Column(String(64), nullable=True)
    title = Column(String(128), default="Confidential Industrial Consultation")
    kb_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(String(64), primary_key=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.session_id"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    citations = Column(Text, nullable=True)  # JSON array of source citations
    evidence = Column(Text, nullable=True)   # Grounding evidence chunks
    agent_trace = Column(Text, nullable=True) # Execution steps summary
    human_verification_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ==============================================================================
# 7. Tamper-Evident Audit Micro-Ledger
# ==============================================================================

class AuditLogEntry(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    event_type = Column(String(64), nullable=False, index=True)  # LOGIN, LOGOUT, FAILED_LOGIN, DOCUMENT_UPLOAD, DOCUMENT_VIEW, etc.
    user_id = Column(String(64), nullable=True, index=True)
    username = Column(String(64), nullable=True)
    ip_address = Column(String(64), default="127.0.0.1")
    action = Column(String(128), nullable=False)
    severity = Column(String(16), default="INFO")  # INFO, WARNING, ERROR, CRITICAL
    details = Column(Text, nullable=True)
    previous_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)


# ==============================================================================
# 8. Local Model Runtime Configuration
# ==============================================================================

class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(32), default="Ollama (Local)")
    model_name = Column(String(64), default="llama3.1")
    embedding_model = Column(String(64), default="nomic-embed-text")
    vision_model = Column(String(64), default="llava")
    temperature = Column(Float, default=0.1)
    context_length = Column(Integer, default=8192)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ==============================================================================
# Engine Initialization & Seed Management
# ==============================================================================

_engine = None
_SessionFactory = None
_db_lock = threading.Lock()


def get_db_engine():
    """Initializes and returns the SQLAlchemy engine."""
    global _engine, _SessionFactory
    if _engine is None:
        db_url = os.getenv("DATABASE_URL", "").strip()
        if not db_url:
            db_path = Path(settings.TASK_DB_PATH).resolve()
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{db_path}"

        is_sqlite = db_url.startswith("sqlite")
        connect_args = {"check_same_thread": False, "timeout": 15.0} if is_sqlite else {}
        _engine = create_engine(db_url, connect_args=connect_args, echo=False)
        _SessionFactory = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return _engine


def get_db_session():
    """Provides a thread-safe SQLAlchemy database session context."""
    get_db_engine()
    return _SessionFactory()


def init_all_schemas():
    """Creates all 16 database tables if they do not exist and seeds initial reference data."""
    with _db_lock:
        engine = get_db_engine()
        Base.metadata.create_all(bind=engine)
        
        session = get_db_session()
        try:
            # 1. Seed Roles
            existing_roles = {r.role_id for r in session.query(Role).all()}
            default_roles = [
                ("Admin", "Full operational authority, user management, and security revocation"),
                ("Engineer", "Upload technical documentation, query knowledge bases, trigger agents"),
                ("Analyst", "Search knowledge, synthesize cross-document insights, export reports"),
                ("Viewer", "Read authorized executive summaries and query allowed knowledge bases")
            ]
            for r_id, desc in default_roles:
                if r_id not in existing_roles:
                    session.add(Role(role_id=r_id, role_name=r_id, description=desc))

            # 2. Seed Default Knowledge Bases (5 industrial categories from specification)
            existing_kbs = {kb.slug for kb in session.query(KnowledgeBase).all()}
            default_kbs = [
                ("Refinery Maintenance", "refinery-maintenance", "Centrifugal pumps, compressors, valve telemetry, and scheduled maintenance procedures."),
                ("Safety SOPs", "safety-sops", "Standard operating procedures, emergency shutdown sequences, and hazardous chemical protocols."),
                ("Equipment Manuals", "equipment-manuals", "Original manufacturer technical manuals, pump curves, specifications, and tolerances."),
                ("Inspection Reports", "inspection-reports", "Periodic NDT inspection logs, vibration spectrum analyses, and ultrasonic thickness surveys."),
                ("Engineering Documents", "engineering-docs", "Process flow diagrams, piping specifications, instrumentation diagrams (P&IDs), and metallurgy.")
            ]
            for name, slug, desc in default_kbs:
                if slug not in existing_kbs:
                    session.add(KnowledgeBase(
                        kb_id=f"kb_{slug.replace('-', '_')}",
                        name=name,
                        slug=slug,
                        description=desc,
                        is_system=True
                    ))

            # 3. Seed Default Model Configuration
            if not session.query(ModelConfig).first():
                session.add(ModelConfig(
                    provider="Ollama (Local)",
                    model_name="llama3.1",
                    embedding_model="nomic-embed-text",
                    vision_model="llava",
                    temperature=0.1,
                    context_length=8192,
                    is_active=True
                ))

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"[DB SCHEMA INIT WARNING]: {e}")
        finally:
            session.close()
