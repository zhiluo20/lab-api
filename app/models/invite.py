"""Invite code model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class InviteCode(BaseModel):
    """Registration invites for controlled onboarding."""

    __tablename__ = "invite_codes"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    uses: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def can_be_used(self, email: str | None = None) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        if self.uses >= self.max_uses:
            return False
        if self.email and email and self.email.lower() != email.lower():
            return False
        return True

    def mark_used(self) -> None:
        self.uses += 1


__all__ = ["InviteCode"]
