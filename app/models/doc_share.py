"""Document sharing model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import BaseModel


class DocShare(BaseModel):
    __tablename__ = "doc_shares"

    doc_id: Mapped[int] = mapped_column(
        ForeignKey("docs.id", ondelete="CASCADE"), nullable=False
    )
    shared_with_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    shared_with_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    access_level: Mapped[str] = mapped_column(
        String(32), nullable=False, default="viewer"
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    document = relationship("Doc", back_populates="shares")
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id])
    creator = relationship("User", foreign_keys=[created_by])


__all__ = ["DocShare"]
