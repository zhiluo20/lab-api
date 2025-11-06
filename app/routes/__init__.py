"""Route blueprints for the Lab API."""

from __future__ import annotations

from .auth_api import auth_bp
from .crud_api import crud_bp
from .docs_api import docs_bp, files_bp
from .health_api import health_bp
from .labs_api import labs_bp
from .samples_api import samples_bp
from .admin_panel import admin_bp
from .web_pages import web_bp

__all__ = [
    "auth_bp",
    "crud_bp",
    "docs_bp",
    "files_bp",
    "health_bp",
    "labs_bp",
    "samples_bp",
    "admin_bp",
    "web_bp",
]
