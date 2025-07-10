from typing import Dict, Any, Optional
from datetime import datetime
import os
from pathlib import Path
from ..repositories import Notification
from .base_channel import BaseChannel


class EmailChannel(BaseChannel):
    """Email notification channel - mocks by writing to files."""

    def __init__(self):
        super().__init__("email", "Email notification channel")
        self.output_dir = Path("outputs/email")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def send(self, notification: Notification) -> bool:
        """Send email notification by writing to file."""

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{notification.id}_{timestamp}.txt"
            filepath = self.output_dir / filename

            email_content = f"""
To: {notification.recipient }
From: notifications@service.com
Subject: {notification.subject}
Date: {datetime.now().isoformat()}

{notification.content}
"""

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(email_content)

            return True

        except Exception as e:
            return False

    def validate_config(self) -> bool:
        return (
            True  # Email channel does not require additional configuration validation
        )
