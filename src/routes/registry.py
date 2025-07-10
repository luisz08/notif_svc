from fastapi import APIRouter, Depends
from datetime import datetime
from ..events import EventManager
from ..repositories import get_repositories
from ..channels import ChannelManager
from ..templates import TemplateManager, get_template_manager

router = APIRouter(prefix="/registry", tags=["registry"])


@router.get("/event-sources")
async def get_event_sources(repos=Depends(get_repositories)):
    """Get all registered event sources."""
    # This would typically query a database or configuration service
    event_manager = EventManager(repos)
    sources = event_manager.get_event_source()
    return {"sources": sources}


@router.get("/channels")
async def get_channels():
    """Get all registered notification channels."""
    # This would typically query a database or configuration service
    channel_manager = ChannelManager()
    channels = channel_manager.get_all_channel_infos()
    return {"channels": channels}


@router.get("/templates")
async def get_templates():
    """Get all registered notification templates."""
    # This would typically query a database or configuration service
    template_manager = get_template_manager()
    templates = template_manager.get_all_template_ids()
    return {"templates": templates}
