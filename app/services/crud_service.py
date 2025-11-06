"""Generic CRUD service for whitelisted tables."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import BaseModel, TABLE_MODELS
from ..utils.errors import APIError, NotFoundError


class CRUDService:
    """Perform CRUD operations against whitelisted SQLAlchemy models."""

    def __init__(self, allowed_tables: Iterable[str] | None = None) -> None:
        self.allowed_tables = set(allowed_tables or TABLE_MODELS.keys())

    def _get_model(self, table: str) -> type[BaseModel]:
        if table not in self.allowed_tables:
            raise APIError(
                code="table_not_allowed", message="Table not permitted", status_code=403
            )
        model = TABLE_MODELS.get(table)
        if not model:
            raise APIError(
                code="table_unknown", message="Table not found", status_code=404
            )
        return model

    def list(self, table: str, *, limit: int, offset: int) -> Dict[str, Any]:
        model = self._get_model(table)
        query = model.query
        total = query.count()
        items: List[BaseModel] = query.offset(offset).limit(limit).all()
        return {
            "data": [item.to_dict() for item in items],
            "meta": {"total": total, "limit": limit, "offset": offset},
        }

    def retrieve(self, table: str, pk: int) -> Dict[str, Any]:
        model = self._get_model(table)
        item = model.query.get(pk)
        if not item:
            raise NotFoundError()
        return item.to_dict()

    def create(self, table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        model = self._get_model(table)
        filtered = self._filter_payload(model, payload)
        instance = model(**filtered)
        db.session.add(instance)
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise APIError(
                code="integrity_error",
                message="Constraint violation",
                status_code=400,
                details={"error": str(exc)},
            )
        return instance.to_dict()

    def update(self, table: str, pk: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        model = self._get_model(table)
        instance = model.query.get(pk)
        if not instance:
            raise NotFoundError()
        filtered = self._filter_payload(model, payload, partial=True)
        for key, value in filtered.items():
            setattr(instance, key, value)
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise APIError(
                code="integrity_error",
                message="Constraint violation",
                status_code=400,
                details={"error": str(exc)},
            )
        return instance.to_dict()

    def delete(self, table: str, pk: int) -> None:
        model = self._get_model(table)
        instance = model.query.get(pk)
        if not instance:
            raise NotFoundError()
        db.session.delete(instance)
        db.session.commit()

    def _filter_payload(
        self, model: type[BaseModel], payload: Dict[str, Any], partial: bool = False
    ) -> Dict[str, Any]:
        columns = {
            column.name for column in model.__table__.columns if not column.primary_key
        }
        return {key: value for key, value in payload.items() if key in columns}


crud_service = CRUDService()
