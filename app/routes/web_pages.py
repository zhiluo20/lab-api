"""Simple HTML views for manual interactions."""

from __future__ import annotations

from flask import Blueprint, current_app, redirect, render_template, request, url_for
from flask_jwt_extended import decode_token
from flask_jwt_extended.exceptions import JWTExtendedException

from ..config import Settings
from ..models.doc import Doc
from ..models.user import User
from ..services.auth_service import AuthService
from ..services.onlyoffice_service import onlyoffice_service
from ..utils.errors import APIError


web_bp = Blueprint("web", __name__, template_folder="../templates")

auth_service = AuthService()


def get_settings() -> Settings:
    return current_app.config["APP_SETTINGS"]


@web_bp.route("/login", methods=["GET", "POST"])
def login_page():
    error: str | None = None
    token_bundle: dict[str, str] | None = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        try:
            token_bundle = auth_service.authenticate_user(username, password)
        except APIError as exc:  # pragma: no cover - UI convenience
            error = exc.message
        except Exception as exc:  # pragma: no cover - unexpected
            error = str(exc)
    return render_template("login.html", error=error, tokens=token_bundle)


def _decode_user_token(token: str) -> tuple[User, dict]:
    try:
        decoded = decode_token(token, allow_expired=False)
    except JWTExtendedException as exc:
        raise APIError(code="invalid_token", message=str(exc), status_code=400) from exc
    identity = decoded["sub"]
    if isinstance(identity, dict):
        if identity.get("sub_type") != "user":
            raise APIError(
                code="invalid_token",
                message="Token is not a user token",
                status_code=400,
            )
        user_id = identity.get("user_id")
    else:  # pragma: no cover - compatibility
        user_id = identity
    user = User.query.get(user_id)
    if not user:
        raise APIError(code="user_missing", message="User not found", status_code=404)
    return user, decoded


@web_bp.route("/list", methods=["GET"])
def docs_list():
    token = request.args.get("token")
    if not token:
        return redirect(url_for("web.login_page"))
    user, decoded = _decode_user_token(token)
    scopes = decoded.get("scopes", [])
    if "doc" not in scopes:
        raise APIError(
            code="scope_missing", message="Token missing doc scope", status_code=403
        )
    docs = Doc.query.order_by(Doc.updated_at.desc()).all()
    return render_template("list.html", docs=docs, token=token, user=user)


@web_bp.route("/edit/<int:doc_id>", methods=["GET"])
def docs_edit(doc_id: int):
    token = request.args.get("token")
    if not token:
        return redirect(url_for("web.login_page"))
    user, decoded = _decode_user_token(token)
    scopes = decoded.get("scopes", [])
    if "doc" not in scopes:
        raise APIError(
            code="scope_missing", message="Token missing doc scope", status_code=403
        )
    doc = Doc.query.get(doc_id)
    if not doc:
        raise APIError(code="not_found", message="Document not found", status_code=404)
    config_payload = onlyoffice_service.document_access_payload(doc, user)
    return render_template("edit.html", doc=doc, config=config_payload, token=token)
