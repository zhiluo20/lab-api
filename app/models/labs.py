"""Lab model."""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import BaseModel


class Lab(BaseModel):
    __tablename__ = "labs"

    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    samples = relationship("Sample", back_populates="lab", cascade="all, delete-orphan")


__all__ = ["Lab"]
