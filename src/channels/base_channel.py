from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import os
from pathlib import Path
from ..repositories import Notification


class BaseChannel(ABC):
    """Abstract base class for notification channels."""

    def __init__(self, name: str, description: str = ""):
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        """Get the name of the channel."""
        return self._name

    @property
    def description(self) -> str:
        """Get the description of the channel."""
        return self._description

    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """Send notification through this channel."""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate channel configuration."""
        return True
