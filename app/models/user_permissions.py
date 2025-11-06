"""User permission association model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import BaseModel


class UserPermissionEntry(BaseModel):
    """Stores per-user scopes."""

    __tablename__ = "user_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "scope", name="uq_user_permissions_user_scope"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(32), nullable=False)

    user = relationship("User", back_populates="permissions")


__all__ = ["UserPermissionEntry"]
