"""Historical snapshots of file ledger entries."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class FileLedgerHistory(BaseModel):
    __tablename__ = "file_ledger_history"

    ledger_id: Mapped[int] = mapped_column(
        ForeignKey("file_ledger.id", ondelete="CASCADE"), nullable=False
    )
    snapshot: Mapped[str] = mapped_column(Text, nullable=False)


__all__ = ["FileLedgerHistory"]
