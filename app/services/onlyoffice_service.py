"""OnlyOffice integration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from flask import url_for

from ..config import Settings, settings as default_settings
from ..models.doc import Doc
from ..models.user import User
from ..utils.errors import APIError
from ..utils.onlyoffice import build_editor_config, verify_callback_token


class OnlyOfficeService:
    """Encapsulates logic for constructing OnlyOffice configuration payloads."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings

    def document_access_payload(self, doc: Doc, user: User) -> Dict[str, Any]:
        file_url = self._build_file_url(doc)
        callback_url = url_for(
            "docs.handle_doc_callback", doc_id=doc.id, _external=True
        )
        config = build_editor_config(
            doc_id=doc.id,
            file_name=doc.name,
            file_url=file_url,
            callback_url=callback_url,
            user_id=user.id,
            user_display_name=user.username,
            settings=self.settings,
        )
        return {"config": config, "documentUrl": file_url}

    def _build_file_url(self, doc: Doc) -> str:
        return url_for("files.serve_file", path=doc.path, _external=True)

    def resolve_file_path(self, doc: Doc) -> Path:
        return Path(self.settings.base_file_dir) / doc.path

    def parse_callback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if "token" in payload:
            if not self.settings.oo_jwt_secret:
                raise APIError(
                    code="oo_secret_missing",
                    message="OO_JWT_SECRET not configured",
                    status_code=500,
                )
            return verify_callback_token(payload["token"], self.settings.oo_jwt_secret)
        return payload


onlyoffice_service = OnlyOfficeService()
