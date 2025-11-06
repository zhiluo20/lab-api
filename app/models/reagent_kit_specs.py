"""Reagent kit specifications."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class ReagentKitSpec(BaseModel):
    __tablename__ = "reagent_kit_specs"

    kit_id: Mapped[int] = mapped_column(
        ForeignKey("reagent_kits.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


__all__ = ["ReagentKitSpec"]
