"""
Database service layer for notification system operations.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Generator
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .database import Event, get_db_session


class EventRepository:
    """Repository class for event operations."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db or get_db_session()
        self._should_close = db is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.db.close()

    def create_event(self, event_type: str, data: Dict[str, Any]) -> Event:
        """Create a new event."""
        event = Event(
            id=uuid.uuid4(),
            type=event_type,
            data=data,
            created_at=datetime.utcnow(),
            processed=False,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_event(self, event_id: uuid.UUID) -> Optional[Event]:
        """Get event by ID."""
        return self.db.query(Event).filter(Event.id == event_id).first()

    def get_unprocessed_events(self) -> List[Event]:
        """Get all unprocessed events."""
        return self.db.query(Event).filter(Event.processed == False).all()

    def mark_event_processed(self, event_id: uuid.UUID) -> bool:
        """Mark an event as processed."""
        event = self.get_event(event_id)
        if event:
            event.processed = True
            event.processed_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

    def get_scheduled_events(self) -> List[Event]:
        """Get all scheduled type events."""
        return self.db.query(Event).filter(Event.type == "scheduled").all()

    def get_scheduled_event_by_id(self, event_id: uuid.UUID) -> Optional[Event]:
        """Get scheduled event by ID."""
        return self.db.query(Event).filter(
            and_(Event.id == event_id, Event.type == "scheduled")
        ).first()


def get_event_repository(
    db: Optional[Session] = None,
) -> Generator[EventRepository, None, None]:
    """Get an instance of EventRepository."""
    repo = EventRepository(db)
    try:
        yield repo
    finally:
        if db is None:
            repo.db.close()
