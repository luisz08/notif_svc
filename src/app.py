"""
FastAPI application for the notification service.
"""

import logging
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session

from .services import NotificationService
from .scheduler import NotificationScheduler
from .config import get_config
from .logging_config import setup_logging
from .middleware import LoggingMiddleware, HealthCheckMiddleware
from .repositories.database import create_tables
from .routes import system_router, events_router, registry_router
from .dependencies import get_scheduler_for_startup, get_app_config
from .exceptions import setup_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Get configuration through dependency injection
    config = get_app_config()
    
    # Initialize logging first
    setup_logging(config.logging)
    logger = logging.getLogger(__name__)

    # Startup
    logger.info(f"Starting {config.service.name} v{config.service.version}")
    logger.info(f"Log level: {config.logging.level}")
    logger.info(f"Debug mode: {config.service.debug}")

    create_tables()  # Initialize database tables
    logger.info("Database tables initialized")

    # Initialize scheduler through dependency injection
    scheduler_gen = get_scheduler_for_startup()
    scheduler = next(scheduler_gen)
    scheduler.start()
    logger.info("NotificationScheduler started")
    logger.info("Application startup completed")

    # Store scheduler in app state for route access
    app.state.notification_scheduler = scheduler

    yield

    # Shutdown
    logger.info("Application shutdown initiated")
    try:
        scheduler.stop()
        logger.info("NotificationScheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
    
    # Cleanup scheduler generator
    try:
        next(scheduler_gen)
    except StopIteration:
        pass
    
    logger.info("Application shutdown completed")


# Get configuration for app initialization
_config = get_app_config()

# Initialize FastAPI app
app = FastAPI(
    title=_config.service.name,
    description="A FastAPI-based notification service with support for multiple channels and templating",
    version=_config.service.version,
    debug=_config.service.debug,
    lifespan=lifespan,
)

# Setup exception handlers
setup_exception_handlers(app)

# Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(HealthCheckMiddleware)

# Register routers
app.include_router(system_router)
app.include_router(events_router)
app.include_router(registry_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=_config.service.host, port=_config.service.port)
