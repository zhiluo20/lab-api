"""Document version history."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import BaseModel


class DocVersion(BaseModel):
    __tablename__ = "doc_versions"

    doc_id: Mapped[int] = mapped_column(
        ForeignKey("docs.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    document = relationship("Doc", back_populates="versions")
    author = relationship("User")


__all__ = ["DocVersion"]
