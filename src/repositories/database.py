"""
Database configuration and models for the notification service.
Using SQLAlchemy 2.0 style with proper type annotations.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Generator, List
from sqlalchemy import (
    create_engine,
    String,
    Text,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy.types as types
from ..config import config
from contextlib import contextmanager

# Create database engine and session
engine = create_engine(config.database.url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base class."""
    pass

# Custom UUID type for SQLite compatibility
class GUID(types.TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as string.
    """

    impl = types.CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(types.CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value

class Event(Base):
    """Event table model with SQLAlchemy 2.0 type annotations."""

    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationship with proper type annotation
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="event", cascade="all, delete-orphan"
    )

class Template(Base):
    """Template table model with SQLAlchemy 2.0 type annotations."""

    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)  # path to templates folder
    variables: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

class Notification(Base):
    """Notification table model with SQLAlchemy 2.0 type annotations."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    recipient: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship with proper type annotation
    event: Mapped["Event"] = relationship("Event", back_populates="notifications")

class DeduplicationLog(Base):
    """Deduplication log table model with SQLAlchemy 2.0 type annotations."""

    __tablename__ = "deduplication_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    content_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

# Database utility functions
def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_db_session() -> Session:
    """Get database session for direct use."""
    return SessionLocal()

def get_db() -> Generator[Session, None, None]:
    """Get database session for depends."""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database session."""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()
