"""Authentication related API endpoints."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..extensions import limiter
from ..services.auth_service import AuthService
from ..utils.errors import APIError
from ..utils.security import ensure_admin, get_current_user


auth_bp = Blueprint("auth", __name__)

auth_service = AuthService()


@auth_bp.route("/", methods=["POST"])
@limiter.limit("20 per minute")
def exchange_api_key():
    payload = request.get_json(force=True)
    api_key = payload.get("api_key")
    if not api_key:
        raise APIError(
            code="missing_api_key", message="api_key is required", status_code=400
        )
    tokens = auth_service.authenticate_api_key(api_key)
    return jsonify(tokens)


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    payload = request.get_json(force=True)
    username = payload.get("username") or payload.get("email")
    password = payload.get("password")
    if not username or not password:
        raise APIError(
            code="invalid_request",
            message="username/email and password required",
            status_code=400,
        )
    tokens = auth_service.authenticate_user(username, password)
    return jsonify(tokens)


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    tokens = auth_service.refresh_tokens(identity, claims)
    return jsonify(tokens)


@auth_bp.route("/change_password", methods=["POST"])
@jwt_required()
def change_password():
    user = get_current_user()
    payload = request.get_json(force=True)
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")
    if not current_password or not new_password:
        raise APIError(
            code="invalid_request", message="Missing password fields", status_code=400
        )
    auth_service.change_password(user, current_password, new_password)
    return jsonify({"status": "ok"})


@auth_bp.route("/request_password_reset", methods=["POST"])
@limiter.limit("5 per hour")
def request_reset():
    payload = request.get_json(force=True)
    email = payload.get("email")
    if not email:
        raise APIError(
            code="invalid_request", message="Email required", status_code=400
        )
    token = auth_service.request_password_reset(email)
    return jsonify({"token": token})


@auth_bp.route("/perform_password_reset", methods=["POST"])
def perform_reset():
    payload = request.get_json(force=True)
    token = payload.get("token")
    password = payload.get("password")
    if not token or not password:
        raise APIError(
            code="invalid_request",
            message="Token and password required",
            status_code=400,
        )
    auth_service.perform_password_reset(token, password)
    return jsonify({"status": "ok"})


@auth_bp.route("/register", methods=["POST"])
@jwt_required(optional=True)
def register():
    payload = request.get_json(force=True)
    invite_code = payload.get("invite_code")
    username = payload.get("username")
    email = payload.get("email")
    password = payload.get("password")
    if not all([invite_code, username, email, password]):
        raise APIError(
            code="invalid_request", message="Missing required fields", status_code=400
        )

    requesting_user = None
    identity = get_jwt_identity()
    if identity and isinstance(identity, dict) and identity.get("sub_type") == "user":
        requesting_user = get_current_user()

    scopes = None
    if requesting_user and payload.get("scopes"):
        scopes_payload = payload["scopes"]
        if isinstance(scopes_payload, str):
            scopes = [
                scope.strip() for scope in scopes_payload.split(",") if scope.strip()
            ]
        elif isinstance(scopes_payload, list):
            scopes = [str(scope) for scope in scopes_payload]
        else:
            raise APIError(
                code="invalid_scope_payload",
                message="scopes must be list or comma separated string",
                status_code=400,
            )
    user = auth_service.register_user(
        username=username,
        email=email,
        password=password,
        invite_code=invite_code,
        scopes=scopes,
    )
    tokens = auth_service.authenticate_user(username, password)
    return jsonify({"user": user.to_dict(), "tokens": tokens}), 201


@auth_bp.route("/create_invite", methods=["POST"])
@jwt_required()
def create_invite():
    ensure_admin()
    user = get_current_user()
    payload = request.get_json(force=True)
    email = payload.get("email")
    expires_in = int(payload.get("expires_in_hours", 72))
    max_uses = int(payload.get("max_uses", 1))
    invite = auth_service.create_invite(
        created_by=user, email=email, expires_in_hours=expires_in, max_uses=max_uses
    )
    return jsonify({"code": invite.code, "expires_at": invite.expires_at}), 201
