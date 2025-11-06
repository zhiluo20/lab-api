"""Document inline comments."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import BaseModel


class DocComment(BaseModel):
    __tablename__ = "doc_comments"

    doc_id: Mapped[int] = mapped_column(
        ForeignKey("docs.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    document = relationship("Doc", back_populates="comments")
    author = relationship("User")


__all__ = ["DocComment"]
