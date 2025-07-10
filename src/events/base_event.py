from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..repositories import Notification
from ..templates import TemplateManager


class BaseEvent(ABC):
    """Abstract base class for events."""

    def __init__(self, source: str, data: Dict[str, Any]):
        self._source = source
        self._data = data
        self.template_manager = TemplateManager()

    @property
    def source(self) -> str:
        """Get the source of the event."""
        return self._source

    @abstractmethod
    def create_notifications(self) -> List[Notification]:
        """Process the event."""
        pass

    def render_content(
        self, template_id: str, data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Render the content of the channel."""
        if data is None:
            data = self._data
        return self.template_manager.render(template_id, data)
