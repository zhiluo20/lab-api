"""Healthcheck endpoints."""

from __future__ import annotations

from flask import Blueprint, jsonify, Response
from sqlalchemy import text

from ..extensions import db


health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health() -> tuple[Response, int]:
    # Keep trivial DB check to ensure connectivity
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        return jsonify(status="error"), 500
    return jsonify(status="ok"), 200
