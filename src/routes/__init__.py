"""
Route modules for the notification service.
"""

from .system import router as system_router
from .events import router as events_router
from .registry import router as registry_router

__all__ = [
    "system_router",
    "events_router",
    "registry_router",
]
