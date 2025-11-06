"""User model definition."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import BaseModel


class User(BaseModel):
    """Represents an authenticated platform user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    permissions: Mapped[List["UserPermissionEntry"]] = relationship(
        "UserPermissionEntry",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    docs: Mapped[List["Doc"]] = relationship("Doc", back_populates="owner")
    roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    login_logs: Mapped[List["LoginLog"]] = relationship(
        "LoginLog", back_populates="user", cascade="all, delete-orphan"
    )
    comments: Mapped[List["DocComment"]] = relationship(
        "DocComment", back_populates="author", cascade="all, delete-orphan"
    )

    def has_scope(self, scope: str) -> bool:
        return any(permission.scope == scope for permission in self.permissions)

    @property
    def scopes(self) -> List[str]:
        return [permission.scope for permission in self.permissions]

    def to_dict(self) -> dict[str, object]:
        data = super().to_dict()
        data.pop("password_hash", None)
        data["roles"] = [
            assignment.role.name for assignment in self.roles if assignment.role
        ]
        return data


if TYPE_CHECKING:
    from .doc import Doc
    from .user_permissions import UserPermissionEntry
    from .user_role import UserRole
    from .login_log import LoginLog
    from .doc_comment import DocComment


__all__ = ["User"]
