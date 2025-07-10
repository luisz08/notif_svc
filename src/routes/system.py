"""
System-related routes.
"""

from fastapi import APIRouter, Depends
from datetime import datetime

from ..config import config

router = APIRouter(tags=["system"])

@router.get("/")
async def root():
    """Root endpoint."""
    return {"message": config.service.name, "version": config.service.version}

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
