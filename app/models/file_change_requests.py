"""File change request tracking."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class FileChangeRequest(BaseModel):
    __tablename__ = "file_change_requests"

    doc_id: Mapped[int] = mapped_column(
        ForeignKey("docs.id", ondelete="CASCADE"), nullable=False
    )
    requested_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="pending")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = ["FileChangeRequest"]
