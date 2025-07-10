"""
Notification scheduler for handling scheduled notifications.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
import logging
from .repositories.database import get_db_context
from .repositories import Repositories
from .services import NotificationService

logger = logging.getLogger(__name__)

excutors = {
    "default": ThreadPoolExecutor(20),
}


class NotificationScheduler:
    """Handles scheduled notifications with APScheduler."""

    def __init__(self):
        """Initialize scheduler with complete lazy loading for optimal resource management."""
        self.scheduler = AsyncIOScheduler(
            executors=excutors,
            job_defaults={
                "coalesce": True,  # Coalesce jobs to avoid overlapping
                "max_instances": 1,  # Only one instance of a job can run at a time
                "misfire_grace_time": 30,  # Allow jobs to run up to 5 minutes late
            },
        )
        self.is_running = False

    def start(self):
        """Start the scheduler and load scheduled events from database."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        try:
            # Load scheduled events from database
            self._load_scheduled_events()

            self.scheduler.start()
            self.is_running = True
            logger.info("Notification scheduler started successfully")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return

        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Notification scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop scheduler: {e}")
            raise

    def _load_scheduled_events(self):
        """Load scheduled events from database and create jobs."""
        try:
            # Create temporary database session to load events
            with get_db_context() as db:
                repos = Repositories(db)
                scheduled_events = repos.events.get_scheduled_events()
                logger.info(f"Loading {len(scheduled_events)} scheduled events")

                for event in scheduled_events:
                    self._add_event_job(event)

        except Exception as e:
            logger.error(f"Failed to load scheduled events: {e}")

    def add_scheduled_event(self, event):
        """Add a new scheduled event to the scheduler."""
        if not self.is_running:
            logger.warning("Scheduler is not running, cannot add event")
            return False

        try:
            self._add_event_job(event)
            logger.info(f"Added scheduled event {event.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add scheduled event {event.id}: {e}")
            return False

    def remove_scheduled_event(self, event_id: str):
        """Remove a scheduled event from the scheduler."""
        try:
            self.scheduler.remove_job(str(event_id))
            logger.info(f"Removed scheduled event {event_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove scheduled event {event_id}: {e}")
            return False

    def update_scheduled_event(self, event):
        """Update a scheduled event (remove old and add new)."""
        try:
            # Remove existing job if it exists
            self.remove_scheduled_event(str(event.id))
            # Add updated job
            return self.add_scheduled_event(event)
        except Exception as e:
            logger.error(f"Failed to update scheduled event {event.id}: {e}")
            return False

    def _add_event_job(self, event):
        """Internal method to add a job for an event."""
        try:
            # Validate that event has cron data
            if "cron" not in event.data:
                logger.error(f"Event {event.id} missing cron configuration")
                return

            # Parse cron expression
            cron_parts = self._parse_cron(event.data["cron"])

            # Create CronTrigger
            trigger = CronTrigger(**cron_parts)

            # Add job, using event.id as job_id
            self.scheduler.add_job(
                func=self.process_scheduled_event,
                trigger=trigger,
                id=str(event.id),
                name=f"Scheduled Event {event.id}",
                args=[str(event.id)],
                replace_existing=True,
            )

            logger.info(
                f"Added job for event {event.id} with cron: {event.data['cron']}"
            )

        except Exception as e:
            logger.error(f"Failed to create job for event {event.id}: {e}")
            raise

    def process_scheduled_event(self, event_id: str):
        """Process a scheduled event when triggered."""
        try:
            logger.info(f"Processing scheduled event {event_id}")

            # Create temporary database session for this task

            with get_db_context() as db:
                # Create temporary repositories and services for this task
                repos = Repositories(db)
                notification_service = NotificationService(repos)

                # Get event from database
                event = repos.events.get_scheduled_event_by_id(uuid.UUID(event_id))
                if not event:
                    logger.error(f"Scheduled event {event_id} not found in database")
                    return

                # Create event instance
                event_instance = self._create_event_instance(event)
                if not event_instance:
                    logger.error(f"Failed to create event instance for {event_id}")
                    return

                # Create notifications
                notifications = event_instance.create_notifications()

                # Send each notification
                results = []
                for notification in notifications:
                    success = notification_service.send_notification(notification)
                    results.append(success)

                successful_sends = sum(results)
                logger.info(
                    f"Scheduled event {event_id} processed: {successful_sends}/{len(results)} notifications sent successfully"
                )

        except Exception as e:
            logger.error(f"Failed to process scheduled event {event_id}: {e}")

    def _create_event_instance(self, event):
        """Create appropriate event instance based on event data."""
        try:
            # For now, we assume all scheduled events are DailyStatEvent
            # This can be extended later to support different event types
            from .events.daily_stat_event import DailyStatEvent

            return DailyStatEvent(event)
        except Exception as e:
            logger.error(f"Failed to create event instance: {e}")
            return None

    def _parse_cron(self, cron_expression: str) -> Dict[str, Any]:
        """Parse cron expression into CronTrigger parameters."""
        try:
            # Support standard 5-field cron: minute hour day month day_of_week
            parts = cron_expression.strip().split()
            if len(parts) != 5:
                raise ValueError(f"Invalid cron expression: {cron_expression}")

            # Convert '*' to None for APScheduler
            def convert_part(part):
                return None if part == "*" else part

            return {
                "minute": convert_part(parts[0]),
                "hour": convert_part(parts[1]),
                "day": convert_part(parts[2]),
                "month": convert_part(parts[3]),
                "day_of_week": convert_part(parts[4]),
            }
        except Exception as e:
            logger.error(f"Failed to parse cron expression '{cron_expression}': {e}")
            raise

    async def trigger_daily_stats_now(self):
        """Manually trigger daily stats report (useful for testing)."""
        logger.info("Manually triggering daily stats report...")
        # This method is kept for backward compatibility but now it would need an event_id
        # For manual testing, you would need to create a test event first
        pass

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status and job information."""
        if not self.is_running:
            return {"status": "stopped", "jobs": []}

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": (
                        job.next_run_time.isoformat() if job.next_run_time else None
                    ),
                    "trigger": str(job.trigger),
                }
            )

        return {"status": "running", "jobs": jobs}
