"""Reagent production batches."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class ReagentProduction(BaseModel):
    __tablename__ = "reagent_productions"

    kit_id: Mapped[int] = mapped_column(
        ForeignKey("reagent_kits.id", ondelete="RESTRICT"), nullable=False
    )
    batch_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


__all__ = ["ReagentProduction"]
