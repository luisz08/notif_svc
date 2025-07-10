"""
Core data models for the notification service.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel
from datetime import datetime


class NotificationStatus(str, Enum):
    """Notification status enumeration."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class EventType(str, Enum):
    """Event type enumeration."""

    REALTIME = "realtime"
    SCHEDULED = "scheduled"


@dataclass
class Event:
    """Event data structure."""

    id: str
    type: EventType
    data: Dict[str, Any]
    timestamp: Optional[str] = None


# @dataclass
# class UserSignUpEventData:
#     """Data structure for user sign-up events."""

#     source: str
#     user_name: str
#     email: str
#     service_name: str
#     join_date: datetime
#     channel: list[str]
#     recipient: list[str] = []
#     slack_channel: Optional[str] = None


@dataclass
class DailyStatEventData:
    """Data structure for daily statistics events."""

    source: str
    query: str


@dataclass
class NotificationResult:
    """Result of a notification attempt."""

    success: bool
    message: str
    status: NotificationStatus
    channel: str
    event_id: str


class NotificationRequest(BaseModel):
    """Pydantic model for notification API requests."""

    notification_id: str
    event_data: Dict[str, Any]
    override_channels: Optional[List[str]] = None


class NotificationResponse(BaseModel):
    """Pydantic model for notification API responses."""

    request_id: str
    results: List[Dict[str, Any]]
    success: bool
    message: str


class NotificationRegistryEntry(BaseModel):
    """Registry entry for a configured notification."""

    id: str
    name: str
    description: str
    channels: List[str]
    template_id: str
    event_source: str
    deduplication_policy: Optional[str] = None
    enabled: bool = True


class TemplateData(BaseModel):
    """Template data model."""

    id: str
    name: str
    subject: Optional[str] = None
    body: str
    variables: List[str] = []
