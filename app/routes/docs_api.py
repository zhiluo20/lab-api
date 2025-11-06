"""Document and OnlyOffice related API endpoints."""

from __future__ import annotations

from json import dumps
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import jwt_required

from ..config import Settings
from ..extensions import db
from ..models.doc import Doc
from ..models.file_ledger import FileLedger
from ..services.onlyoffice_service import onlyoffice_service
from ..utils.errors import NotFoundError
from ..utils.pagination import resolve_pagination
from ..utils.security import get_current_user, require_scope


def get_settings() -> Settings:
    return current_app.config["APP_SETTINGS"]


docs_bp = Blueprint("docs", __name__)
files_bp = Blueprint("files", __name__)


@docs_bp.route("/docs", methods=["GET"])
@jwt_required()
def list_docs():
    require_scope("doc")
    pagination = resolve_pagination(request)
    query = Doc.query.order_by(Doc.updated_at.desc())
    total = query.count()
    items = query.offset(pagination.offset).limit(pagination.limit).all()
    return jsonify(
        {
            "data": [doc.to_dict() for doc in items],
            "meta": {
                "total": total,
                "page": pagination.page,
                "size": pagination.size,
            },
        }
    )


@docs_bp.route("/docs/<int:doc_id>", methods=["GET"])
@jwt_required()
def get_doc(doc_id: int):
    require_scope("doc")
    doc = Doc.query.get(doc_id)
    if not doc:
        raise NotFoundError()
    return jsonify(doc.to_dict())


@docs_bp.route("/docs/<int:doc_id>/edit", methods=["GET"])
@jwt_required()
def get_doc_editor(doc_id: int):
    require_scope("doc")
    doc = Doc.query.get(doc_id)
    if not doc:
        raise NotFoundError()
    user = get_current_user()
    payload = onlyoffice_service.document_access_payload(doc, user)
    return jsonify(payload)


@docs_bp.route("/docs/<int:doc_id>/callback", methods=["POST"])
def handle_doc_callback(doc_id: int):
    doc = Doc.query.get(doc_id)
    if not doc:
        raise NotFoundError()
    payload = request.get_json(silent=True) or {}
    parsed = onlyoffice_service.parse_callback(payload)
    # Persist callback payload for audit
    db.session.add(
        FileLedger(
            doc_id=doc.id,
            action=str(parsed.get("status", "callback"))[:32],
            comment=dumps(parsed)[:500],
        )
    )
    db.session.commit()
    return jsonify({"status": "received"})


@files_bp.route("/files/<path:path>", methods=["GET"])
def serve_file(path: str):
    settings = get_settings()
    base_dir = Path(settings.base_file_dir).resolve()
    requested_path = (base_dir / path).resolve()
    if base_dir not in requested_path.parents:
        raise NotFoundError()
    if not requested_path.is_file():
        raise NotFoundError()
    return send_file(requested_path)


__all__ = ["docs_bp", "files_bp"]
