from .schedule_event import ScheduleEvent
from typing import Dict, Any, List
from ..repositories import Notification, Event
import uuid
from datetime import datetime


class DailyStatEvent(ScheduleEvent):
    """Event for daily statistics."""

    def __init__(self, event: Event):
        # If event.data is a column, use getattr or event.__dict__ to get the value
        if not isinstance(event.data, dict):
            raise ValueError("event.data must be a dictionary")

        # ScheduleEvent will validate cron field and set self.cron
        super().__init__(event)

        if (
            "query" not in event.data
            or "recipient" not in event.data
            or "slack_channel" not in event.data
        ):
            raise ValueError("Missing required fields in event data")

        # event_id and cron are already set by ScheduleEvent parent class
        # Remove duplicate assignment: self.event_id and self.corn

    @property
    def channel_template(self):
        return {
            "slack": "daily_statistics_report.j2",
        }

    def query_data(self) -> Dict[str, Any]:
        """Query data for daily statistics."""
        return {
            "date": "2023-10-01",
            "total_users": 100,
            "new_signups": 10,
            "active_users": 80,
            "notifications_sent": 50,
            "avg_response_time": "2s",
            "success_rate": "95%",
            "cpu_usage": "30%",
            "memory_usage": "40%",
            "disk_usage": "20%",
            "alerts": ["1", "2"],
            "report_time": "2023-10-01T12:00:00Z",
        }

    def create_notifications(self) -> List[Notification]:
        """Create notifications for daily statistics."""
        notifications = []

        data = self.query_data()
        slack_content = self.render_content(self.channel_template["slack"], data)
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
