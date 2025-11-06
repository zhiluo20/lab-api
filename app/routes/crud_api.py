"""Generic CRUD API endpoints operating on whitelisted tables."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..models import TABLE_MODELS
from ..services.crud_service import crud_service
from ..utils.errors import APIError
from ..utils.pagination import resolve_pagination
from ..utils.security import require_scope


crud_bp = Blueprint("crud", __name__)


@crud_bp.route("/meta", methods=["GET"])
@jwt_required()
def get_metadata():
    require_scope("db")
    payload = {
        table: [column.name for column in model.__table__.columns]
        for table, model in TABLE_MODELS.items()
    }
    return jsonify({"data": payload})


@crud_bp.route("/meta/<string:table>", methods=["GET"])
@jwt_required()
def get_table_metadata(table: str):
    require_scope("db")
    model = TABLE_MODELS.get(table)
    if not model:
        raise APIError(code="table_unknown", message="Table not found", status_code=404)
    return jsonify(
        {
            "data": {
                "table": table,
                "columns": [
                    {
                        "name": column.name,
                        "type": str(column.type),
                        "nullable": column.nullable,
                    }
                    for column in model.__table__.columns
                ],
            }
        }
    )


@crud_bp.route("/table/<string:table>", methods=["GET"])
@jwt_required()
def list_table_entries(table: str):
    require_scope("db")
    pagination = resolve_pagination(request)
    result = crud_service.list(table, limit=pagination.limit, offset=pagination.offset)
    result["meta"].update({"page": pagination.page, "size": pagination.size})
    return jsonify(result)


@crud_bp.route("/table/<string:table>", methods=["POST"])
@jwt_required()
def create_table_entry(table: str):
    require_scope("db")
    payload = request.get_json(force=True)
    created = crud_service.create(table, payload)
    return jsonify({"data": created}), 201


@crud_bp.route("/table/<string:table>/<int:pk>", methods=["PUT"])
@jwt_required()
def update_table_entry(table: str, pk: int):
    require_scope("db")
    payload = request.get_json(force=True)
    updated = crud_service.update(table, pk, payload)
    return jsonify({"data": updated})


@crud_bp.route("/table/<string:table>/<int:pk>", methods=["DELETE"])
@jwt_required()
def delete_table_entry(table: str, pk: int):
    require_scope("db")
    crud_service.delete(table, pk)
    return "", 204
