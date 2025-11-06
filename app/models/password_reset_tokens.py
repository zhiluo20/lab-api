"""Password reset token model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import BaseModel


class PasswordResetToken(BaseModel):
    """Single-use password reset tokens for self-service recovery."""

    __tablename__ = "password_reset_tokens"

    token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User")

    def is_valid(self) -> bool:
        return not self.used and self.expires_at >= datetime.utcnow()


__all__ = ["PasswordResetToken"]
