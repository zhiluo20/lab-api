"""Helpers for generating OnlyOffice editor configuration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import jwt

from ..config import Settings


def build_editor_config(
    *,
    doc_id: int,
    file_name: str,
    file_url: str,
    callback_url: str,
    user_id: int,
    user_display_name: str,
    settings: Settings,
) -> Dict[str, Any]:
    """Generate an OnlyOffice editor configuration payload."""

    config: Dict[str, Any] = {
        "document": {
            "fileType": file_name.split(".")[-1] if "." in file_name else "docx",
            "key": f"{doc_id}-{int(datetime.utcnow().timestamp())}",
            "title": file_name,
            "url": file_url,
            "permissions": {
                "download": True,
                "edit": True,
                "print": True,
                "review": True,
            },
        },
        "editorConfig": {
            "callbackUrl": callback_url,
            "mode": "edit",
            "user": {
                "id": str(user_id),
                "name": user_display_name,
            },
        },
    }

    if settings.oo_jwt_secret:
        config["token"] = sign_config(config, settings.oo_jwt_secret)

    return config


def sign_config(config: Dict[str, Any], secret: str) -> str:
    """Sign OnlyOffice configuration using HS256."""
    return jwt.encode(config, secret, algorithm="HS256")


def verify_callback_token(token: str, secret: str) -> Dict[str, Any]:
    """Verify a callback token from OnlyOffice."""
    return jwt.decode(token, secret, algorithms=["HS256"])
