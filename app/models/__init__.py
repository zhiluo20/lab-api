"""Database models for the Lab API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Type

from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import db


class TimestampMixin:
    """Mixin providing created/updated timestamps."""

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class BaseModel(db.Model, TimestampMixin):  # type: ignore[name-defined]
    """Base class with helper serialization."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize simple column attributes."""
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }


from . import (  # noqa: E402
    doc,
    file_change_requests,
    file_ledger,
    file_ledger_history,
    invite,
    lab_history,
    labs,
    password_reset_tokens,
    permission,
    reagent_kit_history,
    reagent_kit_specs,
    reagent_kits,
    reagent_production_history,
    reagent_productions,
    reagent_spec_history,
    sample_history,
    samples,
    user,
    user_permissions,
)

TABLE_MODELS: Dict[str, Type[BaseModel]] = {
    model.__tablename__: model  # type: ignore[attr-defined]
    for model in (
        doc.Doc,
        file_change_requests.FileChangeRequest,
        file_ledger.FileLedger,
        file_ledger_history.FileLedgerHistory,
        invite.InviteCode,
        lab_history.LabHistory,
        labs.Lab,
        password_reset_tokens.PasswordResetToken,
        reagent_kit_history.ReagentKitHistory,
        reagent_kit_specs.ReagentKitSpec,
        reagent_kits.ReagentKit,
        reagent_production_history.ReagentProductionHistory,
        reagent_productions.ReagentProduction,
        reagent_spec_history.ReagentSpecHistory,
        sample_history.SampleHistory,
        samples.Sample,
        user.User,
        user_permissions.UserPermissionEntry,
    )
}

__all__ = [
    "BaseModel",
    "TABLE_MODELS",
    "TimestampMixin",
    "doc",
    "file_change_requests",
    "file_ledger",
    "file_ledger_history",
    "invite",
    "lab_history",
    "labs",
    "password_reset_tokens",
    "permission",
    "reagent_kit_history",
    "reagent_kit_specs",
    "reagent_kits",
    "reagent_production_history",
    "reagent_productions",
    "reagent_spec_history",
    "sample_history",
    "samples",
    "user",
    "user_permissions",
]
