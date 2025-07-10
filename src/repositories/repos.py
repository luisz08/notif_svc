from .deduplication_repository import DeduplicationRepository
from .event_repository import EventRepository
from .notification_repository import NotificationRepository
from sqlalchemy.orm import Session
from typing import Optional, Generator
from .database import get_db_session


class Repositories:
    def __init__(self, db: Optional[Session] = None):
        if db is None:
            db = get_db_session()
            self._should_close = True
        else:
            self._should_close = False
        
        self.db = db
        self._events: Optional[EventRepository] = None
        self._notifications: Optional[NotificationRepository] = None
        self._deduplication: Optional[DeduplicationRepository] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close and self.db:
            self.db.close()

    @property
    def events(self) -> EventRepository:
        if self._events is None:
            self._events = EventRepository(self.db)
        return self._events

    @property
    def notifications(self) -> NotificationRepository:
        if self._notifications is None:
            self._notifications = NotificationRepository(self.db)
        return self._notifications

    @property
    def deduplication(self) -> DeduplicationRepository:
        if self._deduplication is None:
            self._deduplication = DeduplicationRepository(self.db)
        return self._deduplication


def get_repositories() -> Generator[Repositories, None, None]:
    """Get the singleton instance of Repositories."""
    db = get_db_session()  # Assuming get_db_session is defined elsewhere
    repos = Repositories(db)
    yield repos
    # Cleanup if needed, e.g., closing database connections
    if repos._should_close and repos.db:
        repos.db.close()
