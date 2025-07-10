"""
Template system using Jinja2 for message templating with file-based and database storage.
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path
from jinja2 import (
    Environment,
    BaseLoader,
    Template,
    TemplateNotFound,
    TemplateRuntimeError,
)
from .models import TemplateData
from sqlalchemy.orm import Session
import hashlib


class TemplateManager:

    def __init__(self, template_dir: str = "templates"):
        self.env = Environment(loader=BaseLoader())
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(exist_ok=True)

    def render(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Render a template with the given variables."""

        template_file = self.template_dir / f"{template_id}"
        if not template_file.exists():
            raise TemplateNotFound(f"Template '{template_id}' not found")
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                template_content = f.read()

            template = self.env.from_string(template_content)
            return template.render(variables)
        except Exception as e:
            raise TemplateRuntimeError(f"Error rendering template '{template_id}': {e}")

    def get_content_hash(self, content: str) -> str:
        """Generate a sha2 hash for the given content."""

        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get_all_template_ids(self) -> List[str]:
        """Get all template IDs in the templates directory."""
        return [f.stem for f in self.template_dir.glob("*.j2") if f.is_file()]


def get_template_manager() -> TemplateManager:
    """Get a template manager that reads from the templates directory."""
    return TemplateManager()
