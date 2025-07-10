from .base_event import BaseEvent
from typing import Dict, Any, List
from ..repositories import Notification, Event
import uuid
from datetime import datetime


class SignupEvent(BaseEvent):
    """Event for user signup."""

    def __init__(self, event: Event):
        # If event.data is a column, use getattr or event.__dict__ to get the value
        if not isinstance(event.data, dict):
            raise ValueError("event.data must be a dictionary")

        super().__init__(source="user_signup", data=event.data)
        self.event_id = event.id

        if (
            "user_name" not in event.data
            or "email" not in event.data
            or "service_name" not in event.data
            or "recipient" not in event.data
            or "slack_channel" not in event.data
        ):
            raise ValueError("Missing required fields in event data")

    @property
    def channel_template(self):
        return {
            "email": "user_welcome_email.j2",
            "slack": "user_welcome_slack_message.j2",
        }

    def create_notifications(self) -> List[Notification]:
        """Create notifications for user signup."""
        notifications = []

        email_content = self.render_content(self.channel_template["email"])
        email_content_hash = self.template_manager.get_content_hash(email_content)

        # Email notification
        email_notification = Notification(
            id=uuid.uuid4(),
            event_id=self.event_id,
            template_id=self.channel_template["email"],
            channel="email",
            recipient=self._data["recipient"],
            content=email_content,
            content_hash=email_content_hash,
            status="pending",
            created_at=datetime.utcnow(),
        )
        notifications.append(email_notification)

        slack_content = self.render_content(self.channel_template["slack"])
        slack_content_hash = self.template_manager.get_content_hash(slack_content)

        # Slack notification
        slack_notification = Notification(
            id=uuid.uuid4(),
            event_id=self.event_id,
            template_id=self.channel_template["slack"],
            channel="slack",
            recipient=self._data["slack_channel"],
            content=slack_content,
            content_hash=slack_content_hash,
            status="pending",
            created_at=datetime.utcnow(),
        )
        notifications.append(slack_notification)

        return notifications
