"""Generic activity log for auditing administrative actions."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..config import settings
from . import BaseModel


def _json_type():
    uri = settings.database_uri
    if uri.startswith("sqlite"):
        return SQLiteJSON
    if uri.startswith("mysql"):
        return MySQLJSON
    return JSONB


class ActivityLog(BaseModel):
    __tablename__ = "activity_logs"

    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[dict | None] = mapped_column(
        _json_type(), nullable=True, default=dict
    )

    actor = relationship("User")


__all__ = ["ActivityLog"]
