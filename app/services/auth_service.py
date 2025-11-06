"""Authentication and authorization related services."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Optional

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from ..config import Settings, settings as default_settings
from ..extensions import db
from ..utils.errors import APIError, UnauthorizedError
from ..utils.security import generate_token, hash_password, verify_password
from .password_service import PasswordService

from ..models.invite import InviteCode
from ..models.user import User
from ..models.user_permissions import UserPermissionEntry


class AuthService:
    """Domain service encapsulating authentication flows."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._fallback_settings = settings or default_settings

    # ------------------------------------------------------------------
    # Token issuance helpers
    # ------------------------------------------------------------------
    def _issue_tokens(
        self, identity: Any, scopes: Iterable[str], *, is_admin: bool = False
    ) -> Dict[str, Any]:
        claims = {
            "scopes": list(scopes),
            "is_admin": bool(is_admin),
        }
        access = create_access_token(identity=identity, additional_claims=claims)
        refresh = create_refresh_token(identity=identity, additional_claims=claims)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "scopes": claims["scopes"],
            "expires_in": int(self.settings.jwt_access_delta.total_seconds()),
        }

    # ------------------------------------------------------------------
    # API key authentication
    # ------------------------------------------------------------------
    def authenticate_api_key(self, api_key: str) -> Dict[str, Any]:
        scopes = self.settings.api_keys_json.get(api_key)
        if not scopes:
            raise UnauthorizedError(message="Invalid API key")
        identity = {"sub_type": "api_key", "api_key": api_key}
        return self._issue_tokens(identity, scopes, is_admin=False)

    def refresh_tokens(self, identity: Any, claims: Dict[str, Any]) -> Dict[str, Any]:
        """Re-issue access and refresh tokens preserving scope and admin flags."""
        scopes = claims.get("scopes", [])
        is_admin = bool(claims.get("is_admin"))
        return self._issue_tokens(identity, scopes, is_admin=is_admin)

    # ------------------------------------------------------------------
    # User authentication
    # ------------------------------------------------------------------
    def authenticate_user(
        self, username_or_email: str, password: str
    ) -> Dict[str, Any]:
        user = (
            User.query.filter(User.username.ilike(username_or_email)).first()
            or User.query.filter(User.email.ilike(username_or_email)).first()
        )
        if not user or not user.is_active:
            raise UnauthorizedError(message="Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError(message="Invalid credentials")

        user.last_login_at = datetime.utcnow()
        db.session.commit()

        identity = {"sub_type": "user", "user_id": user.id}
        return self._issue_tokens(identity, user.scopes, is_admin=user.is_admin)

    def register_user(
        self,
        *,
        username: str,
        email: str,
        password: str,
        invite_code: str,
        scopes: Optional[Iterable[str]] = None,
    ) -> User:
        invite = InviteCode.query.filter_by(code=invite_code).first()
        if not invite or not invite.can_be_used(email):
            raise APIError(
                code="invalid_invite",
                message="Invite code invalid or expired",
                status_code=400,
            )

        if User.query.filter(
            (User.username == username) | (User.email == email)
        ).first():
            raise APIError(
                code="user_exists",
                message="User with same username or email already exists",
                status_code=409,
            )

        user = User(
            username=username, email=email, password_hash=hash_password(password)
        )
        db.session.add(user)
        db.session.flush()

        invite.mark_used()
        db.session.add(invite)

        scopes_to_assign = list(scopes) if scopes else ["db", "doc"]
        for scope in scopes_to_assign:
            db.session.add(UserPermissionEntry(user_id=user.id, scope=scope))

        db.session.commit()
        return user

    def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedError(message="Current password incorrect")
        user.password_hash = hash_password(new_password)
        db.session.commit()

    def create_invite(
        self,
        *,
        created_by: User,
        email: str | None,
        expires_in_hours: int = 72,
        max_uses: int = 1,
    ) -> InviteCode:
        code = generate_token(8)
        invite = InviteCode(
            code=code,
            email=email,
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            max_uses=max_uses,
        )
        db.session.add(invite)
        db.session.commit()
        return invite

    def request_password_reset(self, email: str) -> Optional[str]:
        user = User.query.filter_by(email=email).first()
        if not user:
            return None
        return self.password_service.create_password_reset(user)

    def perform_password_reset(self, token: str, new_password: str) -> None:
        reset = self.password_service.consume_token(token)
        reset.user.password_hash = hash_password(new_password)
        db.session.commit()

    def ensure_admin_scopes(self, user: User, scopes: Iterable[str]) -> None:
        existing = {perm.scope for perm in user.permissions}
        for scope in scopes:
            if scope not in existing:
                db.session.add(UserPermissionEntry(user_id=user.id, scope=scope))
        db.session.commit()

    @property
    def settings(self) -> Settings:
        try:
            return current_app.config["APP_SETTINGS"]
        except RuntimeError:
            return self._fallback_settings

    @property
    def password_service(self) -> PasswordService:
        return PasswordService(self.settings)


def create_user_cli(app) -> None:
    """Register a Flask CLI command for creating an admin user."""

    import click

    @app.cli.command("create-admin")
    @click.option("--username", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_admin(username: str, email: str, password: str) -> None:
        if User.query.filter(
            (User.username == username) | (User.email == email)
        ).first():
            click.echo("User already exists")
            return
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_admin=True,
        )
        db.session.add(user)
        db.session.flush()
        for scope in ("db", "doc"):
            db.session.add(UserPermissionEntry(user_id=user.id, scope=scope))
        db.session.commit()
        click.echo(f"Created admin user {username}")
