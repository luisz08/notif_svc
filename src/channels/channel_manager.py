from .email_channel import EmailChannel
from .slack_channel import SlackChannel
from ..repositories import Notification
import logging

logger = logging.getLogger(__name__)


class ChannelManager:
    def __init__(self):
        self.channels = self._get_channels()

    def _get_channels(self):
        """Initialize available notification channels."""
        email = EmailChannel()
        slack = SlackChannel()
        return {
            email.name: email,
            slack.name: slack,
        }

    def get_all_channel_infos(self):
        """Get all available notification channels."""
        return {key: value.description for key, value in self.channels.items()}

    def send(self, notification: Notification):
        if not notification.channel in self.channels.keys():
            raise ValueError(f"Channel {notification.channel} not found")

        channel = self.channels[notification.channel]
        if not channel.validate_config():
            raise ValueError(f"Channel {notification.channel} configuration is invalid")
        return channel.send(notification)
