"""
Custom exceptions and exception handlers for the notification service.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class NotificationServiceException(Exception):
    """Base exception for notification service."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details if details is not None else {}
        super().__init__(self.message)

class NotificationSendError(NotificationServiceException):
    """Exception raised when notification sending fails."""
    pass

class SchedulerError(NotificationServiceException):
    """Exception raised when scheduler operations fail."""
    pass

class ConfigurationError(NotificationServiceException):
    """Exception raised when configuration is invalid."""
    pass

class DatabaseError(NotificationServiceException):
    """Exception raised when database operations fail."""
    pass

# Exception handlers
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error for {request.url}: {exc.errors()}")
    
    # Get request ID from state or headers
    request_id = getattr(request.state, 'request_id', None) or request.headers.get("X-Request-ID")
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors,
            "request_id": request_id
        },
        headers={"X-Request-ID": request_id or ""}
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP {exc.status_code} for {request.url}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "request_id": request.headers.get("X-Request-ID")
        },
        headers={"X-Request-ID": request.headers.get("X-Request-ID", "")}
    )

async def notification_service_exception_handler(request: Request, exc: NotificationServiceException):
    """Handle custom notification service exceptions."""
    logger.error(f"Service error for {request.url}: {exc.message}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": exc.message,
            "type": exc.__class__.__name__,
            "details": exc.details,
            "request_id": request.headers.get("X-Request-ID")
        },
        headers={"X-Request-ID": request.headers.get("X-Request-ID", "")}
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception for {request.url}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": "InternalServerError",
            "request_id": request.headers.get("X-Request-ID")
        },
        headers={"X-Request-ID": request.headers.get("X-Request-ID", "")}
    )

def setup_exception_handlers(app):
    """Setup all exception handlers for the FastAPI app."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(NotificationServiceException, notification_service_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
