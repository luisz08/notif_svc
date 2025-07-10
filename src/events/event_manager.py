from ..repositories import Repositories, Notification, Event
from typing import List, Dict, Any
from ..models import EventType
from .base_event import BaseEvent
from .daily_stat_event import DailyStatEvent
from .signup_event import SignupEvent


class EventManager:
    EVENT_TYPE_MAP = {
        "daily_stat": DailyStatEvent,
        "user_signup": SignupEvent,
    }

    def __init__(self, repos: Repositories):
        self.repos = repos

    def create_event_source(self, event: Event) -> BaseEvent:
        """Create a unique event source identifier."""
        # This could be a UUID or any other unique identifier
        if not isinstance(event.data, dict):
            raise ValueError("Event data must be a dictionary")

        if "source" not in event.data:
            raise ValueError("Event data must contain a 'source' field")

        event_cls = self.EVENT_TYPE_MAP.get(event.data["source"])
        if not event_cls:
            raise ValueError(f"Unknown event source: {event.data['source']}")
        return event_cls(event)

    def process_realtime_event(self, event_data: Dict[str, Any]) -> List[Notification]:
        """Process a real-time event."""
        # Here you would implement the logic to handle real-time events
        # For example, you might create a notification based on the event data
        event = self.repos.events.create_event(EventType.REALTIME.value, event_data)
        event_source = self.create_event_source(event)
        return event_source.create_notifications()

    def process_scheduled_event(self, event_data: dict):
        event = self.repos.events.create_event(EventType.SCHEDULED.value, event_data)
        event_source = self.create_event_source(event)
        return event_source.create_notifications()

    def get_event_source(self) -> List[str]:
        """Get a list of available event sources."""
        return list(self.EVENT_TYPE_MAP.keys())
