import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Generator
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .database import Notification, get_db_session
from ..models import NotificationStatus


class NotificationRepository:
    """Repository class for notification operations."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db or get_db_session()
        self._should_close = db is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close:
            self.db.close()

    def create_from_instance(self, notification: Notification) -> Notification:
        """Create a new notification."""
        notification.subject = notification.subject or "No Subject"
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    # Notification operations
    def create(
        self,
        event_id: uuid.UUID,
        template_id: uuid.UUID,
        channel: str,
        subject: str,
        recipient: Optional[str],
        content: str,
        content_hash: str,
        status: str,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            id=uuid.uuid4(),
            event_id=event_id,
            template_id=template_id,
            channel=channel,
            subject=subject,
            recipient=recipient,
            content=content,
            content_hash=content_hash,
            status=status,
            created_at=datetime.utcnow(),
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get(self, notification_id: uuid.UUID) -> Optional[Notification]:
        """Get notification by ID."""
        return (
            self.db.query(Notification)
            .filter(Notification.id == notification_id)
            .first()
        )

    def any(self, id: uuid.UUID, hash: str, seconds: int = 3600) -> bool:
        """Check if a notification with the given hash exists within the last 'seconds'."""
        threshold = datetime.utcnow() - timedelta(seconds=seconds)
        return (
            self.db.query(Notification)
            .filter(
                and_(
                    Notification.content_hash == hash,
                    Notification.created_at >= threshold,
                    Notification.id != id,
                )
            )
            .count()
            > 0
        )

    def get_by_event(self, event_id: uuid.UUID) -> List[Notification]:
        """Get all notifications for an event."""
        return (
            self.db.query(Notification).filter(Notification.event_id == event_id).all()
        )

    def get_by_channel(self, channel: str) -> List[Notification]:
        """Get all notifications for a channel."""
        return self.db.query(Notification).filter(Notification.channel == channel).all()

    def update_status(
        self,
        notification_id: uuid.UUID,
        status: str,
        sent_at: Optional[datetime] = None,
    ) -> Optional[Notification]:
        """Update notification status."""
        notification = self.get(notification_id)
        if notification:
            notification.status = status
            if sent_at:
                notification.sent_at = sent_at
            elif status == NotificationStatus.SENT:
                notification.sent_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(notification)
        return notification

    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        total = self.db.query(Notification).count()
        sent = (
            self.db.query(Notification)
            .filter(Notification.status == NotificationStatus.SENT)
            .count()
        )
        failed = (
            self.db.query(Notification)
            .filter(Notification.status == NotificationStatus.FAILED)
            .count()
        )
        pending = (
            self.db.query(Notification)
            .filter(Notification.status == NotificationStatus.PENDING)
            .count()
        )
        duplicates = (
            self.db.query(Notification)
            .filter(Notification.status == NotificationStatus.DUPLICATE)
            .count()
        )

        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "pending": pending,
            "duplicates": duplicates,
        }


def get_notification_repository(
    db: Optional[Session] = None,
) -> Generator[NotificationRepository, None, None]:
    """Get an instance of NotificationRepository."""
    repo = NotificationRepository(db)
    try:
        yield repo
    finally:
        if db is None:
            repo.db.close()
