"""Sample history entries."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import BaseModel


class SampleHistory(BaseModel):
    __tablename__ = "sample_history"

    sample_id: Mapped[int] = mapped_column(
        ForeignKey("samples.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    sample = relationship("Sample", back_populates="histories")


__all__ = ["SampleHistory"]
