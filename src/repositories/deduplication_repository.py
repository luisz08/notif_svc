import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Generator
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .database import DeduplicationLog, get_db_session


class DeduplicationRepository:
    """Repository class for deduplication operations."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db or get_db_session()
        self._should_close = db is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.db.close()

    def check_duplicate(self, content_hash: str) -> bool:
        """Check if content hash exists in deduplication log."""
        return (
            self.db.query(DeduplicationLog)
            .filter(DeduplicationLog.content_hash == content_hash)
            .first()
            is not None
        )

    def log_deduplication(self, content_hash: str) -> DeduplicationLog:
        """Log a content hash for deduplication."""
        log_entry = DeduplicationLog(
            id=uuid.uuid4(), content_hash=content_hash, created_at=datetime.utcnow()
        )
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry

    def cleanup_old_logs(self, days: int = 30) -> int:
        """Clean up old deduplication logs."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = (
            self.db.query(DeduplicationLog)
            .filter(DeduplicationLog.created_at < cutoff_date)
            .delete()
        )
        self.db.commit()
        return deleted


def get_deduplication_repository(
    db: Optional[Session] = None,
) -> Generator[DeduplicationRepository, None, None]:
    """Get a deduplication repository instance."""
    repo = DeduplicationRepository(db)
    try:
        yield repo
    finally:
        if db is None:
            repo.db.close()
