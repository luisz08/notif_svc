from ..models import Event
from .base_policy import BasePolicy
from ..repositories import DeduplicationLog, Notification, Repositories
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TimeWindowPolicy(BasePolicy):
    """Deduplication policy that prevents sending notifications within a time window."""

    def __init__(self, repos: Repositories, window_seconds: int = 60):
        super().__init__("time_window")
        self.repos = repos
        self.window_seconds = window_seconds

    def should_send(self, notification: Notification) -> bool:
        """Check if notification should be sent based on deduplication policy."""
        hash = notification.content_hash
        result = not self.repos.notifications.any(
            notification.id, hash, self.window_seconds
        )
        logger.debug(f"Checking deduplication for hash {hash}: {result}")
        return result

    def record_duplication(self, notification: Notification):
        """Record that notification was sent."""
        hash = notification.content_hash
        self.repos.deduplication.log_deduplication(hash)
