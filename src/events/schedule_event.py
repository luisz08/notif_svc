"""
Base class for scheduled events.
"""
from .base_event import BaseEvent
from typing import Dict, Any
from ..repositories import Event

class ScheduleEvent(BaseEvent):
    """Base class for scheduled events."""
    
    def __init__(self, event: Event):
        """Initialize scheduled event with validation."""
        # Initialize with event data
        super().__init__(source=event.type, data=event.data)
        self.event_id = event.id
        
        # Validate required cron field
        if "cron" not in event.data:
            raise ValueError("Missing 'cron' field in scheduled event data")
        
        self.cron = event.data["cron"]
    
    @property
    def cron_expression(self) -> str:
        """Return cron expression for scheduling."""
        return self.cron
