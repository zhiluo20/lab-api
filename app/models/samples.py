"""Sample model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import BaseModel


class Sample(BaseModel):
    __tablename__ = "samples"

    lab_id: Mapped[int] = mapped_column(
        ForeignKey("labs.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    lab = relationship("Lab", back_populates="samples")

    histories = relationship(
        "SampleHistory", back_populates="sample", cascade="all, delete-orphan"
    )


__all__ = ["Sample"]
