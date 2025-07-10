from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime
from typing import Dict, Any, Optional, List
from ..events import EventManager
from ..models import EventType
from ..services import NotificationService
from pydantic import BaseModel, Field, validator
import logging
import re

# Import dependency injection functions
from ..dependencies import get_notification_service, get_repositories

logger = logging.getLogger(__name__)


class ScheduledEventRequest(BaseModel):
    """Request model for creating scheduled events."""

    source: str = Field(
        ..., min_length=1, max_length=100, description="Event source identifier"
    )
    cron: str = Field(
        ..., description="Cron expression (5 parts: minute hour day month day_of_week)"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Event-specific data"
    )
    enabled: Optional[bool] = Field(
        default=True, description="Whether the event is enabled"
    )

    @validator("source")
    def validate_source(cls, v):
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(
                "Source must be a valid identifier (letters, numbers, underscores)"
            )
        return v

    @validator("cron")
    def validate_cron(cls, v):
        cron_parts = v.strip().split()
        if len(cron_parts) != 5:
            raise ValueError(
                "Cron expression must have exactly 5 parts: minute hour day month day_of_week"
            )

        return v


class RealTimeEventRequest(BaseModel):
    """Request model for creating real-time events."""

    source: str = Field(
        ..., min_length=1, max_length=100, description="Event source identifier"
    )
    event_type: str = Field(
        ..., min_length=1, max_length=100, description="Type of the event"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Event-specific data"
    )

    @validator("source", "event_type")
    def validate_identifiers(cls, v):
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(
                "Field must be a valid identifier (letters, numbers, underscores)"
            )
        return v


class EventResponse(BaseModel):
    """Response model for event operations."""

    status: str
    message: str
    event_id: str


class EventListResponse(BaseModel):
    """Response model for listing events."""

    status: str
    events: List[Dict[str, Any]]


router = APIRouter(prefix="/events", tags=["events"])


@router.post("/real-time", response_model=EventResponse)
async def real_time_event(
    request: Request,
    realtime_request: RealTimeEventRequest,
    repos=Depends(get_repositories),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Handle real-time events by sending notifications based on the event data.
    """
    try:
        logger.info("Received request to process a real-time event")

        # Prepare event data
        event_data = {
            "source": realtime_request.source,
            "event_type": realtime_request.event_type,
            **realtime_request.data,
        }

        # Create the real-time event in the database
        event = repos.events.create_event(EventType.REALTIME.value, event_data)

        logger.info(f"Real-time event created with ID: {event.id}")

        # Process the event if immediate processing is requested
        event_manager = EventManager(repos)
        notifications = event_manager.process_realtime_event(event_data)

        for notification in notifications:
            notification_service.send_notification(notification)

        logger.info(f"Real-time event {event.id} processed immediately")

        return EventResponse(
            status="success",
            message="Real-time event processed successfully",
            event_id=str(event.id),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing real-time event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/scheduled", response_model=EventResponse)
async def scheduled_event(
    request: Request,
    scheduled_request: ScheduledEventRequest,
    repos=Depends(get_repositories),
):
    """
    Create a new scheduled event that will be managed by the NotificationScheduler.
    """
    try:
        logger.info("Received request to create a scheduled event")

        logger.info(
            f"Creating scheduled event: {scheduled_request.source} with cron {scheduled_request.cron}"
        )

        # Prepare event data with cron schedule
        event_data = {
            "source": scheduled_request.source,
            "cron": scheduled_request.cron,
            **scheduled_request.data,
        }

        # Create the scheduled event in the database
        event = repos.events.create_event(EventType.SCHEDULED.value, event_data)

        logger.info(f"Scheduled event created with ID: {event.id}")

        # Get the scheduler from app state and add the event
        scheduler = request.app.state.notification_scheduler
        if scheduler and scheduled_request.enabled:
            success = scheduler.add_scheduled_event(event)
            if not success:
                raise HTTPException(
                    status_code=500, detail="Failed to register event with scheduler"
                )

        logger.info(f"Scheduled event {event.id} registered with scheduler")

        return EventResponse(
            status="success",
            message="Scheduled event created successfully",
            event_id=str(event.id),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating scheduled event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/scheduled", response_model=EventListResponse)
async def list_scheduled_events(repos=Depends(get_repositories)):
    """
    List all scheduled events.
    """
    try:
        events = repos.events.get_scheduled_events()
        return EventListResponse(
            status="success",
            events=[
                {
                    "id": str(event.id),
                    "type": event.type,
                    "data": event.data,
                    "created_at": (
                        event.created_at.isoformat() if event.created_at else None
                    ),
                    "processed": event.processed,
                }
                for event in events
            ],
        )
    except Exception as e:
        logger.error(f"Error listing scheduled events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
