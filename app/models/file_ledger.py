"""Document ledger entries."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class FileLedger(BaseModel):
    __tablename__ = "file_ledger"

    doc_id: Mapped[int] = mapped_column(
        ForeignKey("docs.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    performed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = ["FileLedger"]
