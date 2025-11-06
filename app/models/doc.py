"""Document metadata model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import BaseModel


class Doc(BaseModel):
    """Metadata for documents managed by OnlyOffice."""

    __tablename__ = "docs"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    owner = relationship("User", back_populates="docs")


__all__ = ["Doc"]
