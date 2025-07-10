from abc import ABC, abstractmethod
from ..models import Event
from ..repositories import Notification


class BasePolicy(ABC):
    """Abstract base class for deduplication policies."""

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        """Get the name of the deduplication policy."""
        return self._name

    @abstractmethod
    def should_send(self, notification: Notification) -> bool:
        """Check if notification should be sent based on deduplication policy."""
        pass

    @abstractmethod
    def record_duplication(self, notification: Notification):
        """Record that notification was sent."""
        pass
