"""Password reset related service."""

from __future__ import annotations

from datetime import datetime, timedelta

from ..config import Settings, settings as default_settings
from ..extensions import db
from ..models.password_reset_tokens import PasswordResetToken
from ..models.user import User
from ..utils.errors import APIError
from ..utils.security import generate_token


class PasswordService:
    """Utility service for issuing and consuming password reset tokens."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or default_settings
        self.expiry_duration = timedelta(hours=1)

    def create_password_reset(self, user: User) -> str:
        token = generate_token(16)
        reset = PasswordResetToken(
            token=token,
            user=user,
            expires_at=datetime.utcnow() + self.expiry_duration,
        )
        db.session.add(reset)
        db.session.commit()
        return token

    def consume_token(self, token: str) -> PasswordResetToken:
        reset = PasswordResetToken.query.filter_by(token=token).one_or_none()
        if not reset or not reset.is_valid():
            raise APIError(
                code="invalid_token",
                message="Reset token is invalid or expired",
                status_code=400,
            )
        reset.used = True
        db.session.add(reset)
        db.session.commit()
        return reset
