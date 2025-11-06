"""Centralised error handling utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from ..extensions import jwt


@dataclass(slots=True)
class APIError(Exception):
    """Typed exception for returning JSON errors from the API layer."""

    code: str
    message: str
    status_code: int = 400
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "error": {"code": self.code, "message": self.message}
        }
        if self.details:
            payload["error"]["details"] = self.details
        return payload


class NotFoundError(APIError):
    """Represents a 404 from the domain layer."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            code="not_found", message=message, status_code=404, details=details
        )


class UnauthorizedError(APIError):
    """Represents a 401 error."""

    def __init__(
        self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            code="unauthorized", message=message, status_code=401, details=details
        )


def register_error_handlers(app: Flask) -> None:
    """Attach error handlers to the given Flask application."""

    @app.errorhandler(APIError)
    def handle_api_error(exc: APIError):
        return jsonify(exc.to_dict()), exc.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):
        payload = {
            "error": {
                "code": exc.name.lower().replace(" ", "_"),
                "message": exc.description,
            }
        }
        return jsonify(payload), exc.code if exc.code else 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        app.logger.exception("Unhandled exception: %s", exc)
        payload = {
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred.",
            }
        }
        return jsonify(payload), 500

    # Flask-JWT-Extended error hooks
    @jwt.unauthorized_loader
    def _missing_jwt(reason: str):
        raise UnauthorizedError(message=reason)

    @jwt.invalid_token_loader
    def _invalid_jwt(reason: str):
        raise UnauthorizedError(message=reason)

    @jwt.revoked_token_loader
    def _revoked_jwt(jwt_header, jwt_payload):
        raise UnauthorizedError(message="Token has been revoked.")

    @jwt.expired_token_loader
    def _expired_jwt(jwt_header, jwt_payload):
        raise UnauthorizedError(message="Token has expired.")
