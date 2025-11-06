"""History of reagent specifications."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class ReagentSpecHistory(BaseModel):
    __tablename__ = "reagent_spec_history"

    spec_id: Mapped[int] = mapped_column(
        ForeignKey("reagent_kit_specs.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = ["ReagentSpecHistory"]
