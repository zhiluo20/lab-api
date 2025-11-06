"""Reagent kit master records."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import BaseModel


class ReagentKit(BaseModel):
    __tablename__ = "reagent_kits"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


__all__ = ["ReagentKit"]
