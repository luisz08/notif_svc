"""
Core notification service implementation.
"""

from typing import Dict, Any, List, Optional, Generator
from datetime import datetime
import uuid
import asyncio

from ..models import (
    Event,
    EventType,
    NotificationResult,
    NotificationStatus,
    NotificationRegistryEntry,
)
from ..templates import TemplateManager, get_template_manager
from ..deduplications import DeduplicationManager
from ..config import config
from ..channels import ChannelManager
from ..repositories import Repositories, Notification, Event as DbEvent, GUID
from ..events import EventManager
from ..logging_config import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Main notification service class."""

    def __init__(
        self,
        repos: Repositories,
        template_manager: Optional[TemplateManager] = None,
        channel_manager: Optional[ChannelManager] = None,
        deduplication_manager: Optional[DeduplicationManager] = None,
        event_manager: Optional[EventManager] = None,
    ):
        self.repos = repos
        
        # Use injected dependencies or create defaults
        self.template_manager = template_manager or get_template_manager()
        self.channel_manager = channel_manager or ChannelManager()
        self.deduplication_manager = deduplication_manager or DeduplicationManager(repos)
        self.event_manager = event_manager or EventManager(repos)

        logger.info("NotificationService initialized")
        logger.debug(f"Template manager: {type(self.template_manager).__name__}")
        logger.debug(f"Channel manager: {type(self.channel_manager).__name__}")

    def send_notification(self, notification: Notification) -> bool:
        """Send a notification through the appropriate channel."""
        id = uuid.UUID(str(notification.id))

        logger.info(f"Processing notification {id} via {notification.channel}")
        logger.debug(
            f"Notification details - recipient: {notification.recipient}, template: {getattr(notification, 'template', 'N/A')}"
        )

        try:
            notification = self.repos.notifications.create_from_instance(notification)
            logger.debug(f"Notification {id} stored in database")

            should_send = self.deduplication_manager.handle(notification)
            logger.debug(notification.content)
            if not should_send:
                logger.info(f"Duplicate notification detected for {id}, skipping send")
                self.repos.notifications.update_status(
                    id, NotificationStatus.DUPLICATE, datetime.utcnow()
                )
                return False

            logger.debug(
                f"Sending notification {id} through {notification.channel} channel"
            )
            self.channel_manager.send(notification)

            self.repos.notifications.update_status(
                id, NotificationStatus.SENT, datetime.utcnow()
            )
            logger.info(f"Notification {id} sent successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to send notification {id}: {e}", exc_info=True)
            self.repos.notifications.update_status(id, NotificationStatus.FAILED)
            return False


def get_notification_service(
    repos: Optional[Repositories] = None,
) -> NotificationService:
    """Get the singleton instance of NotificationService."""
    if repos is None:
        repos = Repositories()  # Initialize with default repositories
    return NotificationService(repos)


def get_notification_service_gen(
    repos: Optional[Repositories] = None,
) -> Generator[NotificationService, None, None]:
    """Generator to yield NotificationService instance."""
    if repos is None:
        repos = Repositories()  # Initialize with default repositories
    service = get_notification_service(repos)
    yield service
    # Cleanup if needed, e.g., closing database connections
    # repos.close() if repos else None
