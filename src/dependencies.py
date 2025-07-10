"""
Dependency injection functions for FastAPI.
"""

from functools import lru_cache
from typing import Generator, Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from .config import NotificationConfig, get_config
from .repositories.database import get_db
from .repositories import Repositories
from .services import NotificationService
from .scheduler import NotificationScheduler
from .templates import TemplateManager, get_template_manager
from .channels import ChannelManager
from .deduplications import DeduplicationManager
from .events import EventManager

# Configuration dependency
@lru_cache()
def get_app_config() -> NotificationConfig:
    """Get application configuration with caching."""
    return get_config()

# Core dependencies
def get_repositories(db: Session = Depends(get_db)) -> Repositories:
    """Create a Repositories instance with proper database session management."""
    return Repositories(db)

def get_template_manager_dep() -> TemplateManager:
    """Get template manager instance."""
    return get_template_manager()

def get_channel_manager() -> ChannelManager:
    """Get channel manager instance."""
    return ChannelManager()

def get_deduplication_manager(repos: Repositories = Depends(get_repositories)) -> DeduplicationManager:
    """Get deduplication manager instance."""
    return DeduplicationManager(repos)

def get_event_manager(repos: Repositories = Depends(get_repositories)) -> EventManager:
    """Get event manager instance."""
    return EventManager(repos)

def get_notification_service(
    repos: Repositories = Depends(get_repositories),
    template_manager: TemplateManager = Depends(get_template_manager_dep),
    channel_manager: ChannelManager = Depends(get_channel_manager),
    deduplication_manager: DeduplicationManager = Depends(get_deduplication_manager),
    event_manager: EventManager = Depends(get_event_manager),
) -> NotificationService:
    """Create a NotificationService instance with all dependencies injected."""
    return NotificationService(
        repos=repos,
        template_manager=template_manager,
        channel_manager=channel_manager,
        deduplication_manager=deduplication_manager,
        event_manager=event_manager,
    )

# Scheduler dependency - managed as singleton
_scheduler_instance: Optional[NotificationScheduler] = None

def get_scheduler() -> NotificationScheduler:
    """Get the singleton scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = NotificationScheduler()
    return _scheduler_instance

def get_scheduler_for_startup() -> Generator[NotificationScheduler, None, None]:
    """Get scheduler for application startup/shutdown management."""
    scheduler = get_scheduler()
    try:
        yield scheduler
    finally:
        # Cleanup handled in lifespan
        pass
