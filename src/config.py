"""
Configuration management with dotenv support.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ServiceConfig(BaseModel):
    """Service configuration."""

    name: str = Field(default="Notification Service")
    version: str = Field(default="1.0.0")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)


class EmailConfig(BaseModel):
    """Email configuration."""

    from_email: str = Field(default="noreply@example.com")
    from_name: str = Field(default="Notification Service")


class SlackConfig(BaseModel):
    """Slack configuration."""

    default_channel: str = Field(default="#notifications")


class DatabaseConfig(BaseModel):
    """Database configuration."""

    url: str = Field(default="sqlite:///./notifications.db")
    echo: bool = Field(default=False)

class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    format: str = Field(default="detailed")  # detailed, simple, json
    console_enabled: bool = Field(default=True)
    file_enabled: bool = Field(default=False)
    file_path: Optional[str] = Field(default=None)


class NotificationConfig(BaseModel):
    """Notification service configuration."""

    service: ServiceConfig = Field(default_factory=ServiceConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def get_config() -> NotificationConfig:
    """Get configuration from environment variables."""

    # Service configuration
    service_config = ServiceConfig(
        name=os.getenv("SERVICE_NAME", "Notification Service"),
        version=os.getenv("SERVICE_VERSION", "1.0.0"),
        host=os.getenv("SERVICE_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVICE_PORT", "8000")),
        debug=os.getenv("DEBUG", "False").lower() == "true",
    )

    # Email configuration
    email_config = EmailConfig(
        from_email=os.getenv("FROM_EMAIL", "noreply@example.com"),
        from_name=os.getenv("FROM_NAME", "Notification Service"),
    )

    # Slack configuration
    slack_config = SlackConfig(
        default_channel=os.getenv("SLACK_DEFAULT_CHANNEL", "#notifications")
    )

    database_config = DatabaseConfig(
        url=os.getenv("DATABASE_URL", "sqlite:///./notifications.db"),
        echo=os.getenv("DATABASE_ECHO", "False").lower() == "true",
    )

    # Logging configuration
    logging_config = LoggingConfig(
        level=os.getenv("LOG_LEVEL", "DEBUG" if service_config.debug else "INFO"),
        format=os.getenv("LOG_FORMAT", "detailed"),
        console_enabled=os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true",
        file_enabled=os.getenv("LOG_FILE_ENABLED", "false").lower() == "true",
        file_path=os.getenv("LOG_FILE_PATH"),
    )

    return NotificationConfig(
        service=service_config,
        email=email_config,
        slack=slack_config,
        database=database_config,
        logging=logging_config,
    )


# Global configuration instance
config = get_config()
