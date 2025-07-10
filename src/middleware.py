"""
Middleware for logging and request tracking.
"""

import logging
import time
import uuid
from typing import Callable, Optional, List
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""

    def __init__(self, app, logger_name: str = "src.middleware"):
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())[:8]
        
        # Start timing
        start_time = time.time()
        
        # Log request
        self.logger.info(
            f"[{request_id}] {request.method} {request.url.path} - Started",
            extra={"request_id": request_id}
        )
        
        # Log request details in debug mode
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(
                f"[{request_id}] Headers: {dict(request.headers)}",
                extra={"request_id": request_id}
            )
            if request.query_params:
                self.logger.debug(
                    f"[{request_id}] Query params: {dict(request.query_params)}",
                    extra={"request_id": request_id}
                )

        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            self.logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"{response.status_code} - {process_time:.3f}s",
                extra={"request_id": request_id}
            )
            
            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            self.logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"ERROR - {process_time:.3f}s - {str(exc)}",
                extra={"request_id": request_id},
                exc_info=True
            )
            
            # Store request ID in request state for exception handlers
            request.state.request_id = request_id
            
            # Re-raise to let exception handlers deal with it
            raise exc


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware to reduce noise from health check endpoints."""

    def __init__(self, app, health_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.health_paths = health_paths or ["/health", "/healthz", "/ping", "/"]
        self.logger = logging.getLogger("src.middleware.healthcheck")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip detailed logging for health check endpoints
        if request.url.path in self.health_paths:
            # Only log health checks in debug mode
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Health check: {request.method} {request.url.path}")
        
        return await call_next(request)
