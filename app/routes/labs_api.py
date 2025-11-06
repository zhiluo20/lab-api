"""Labs CRUD API."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models.lab_history import LabHistory
from ..models.labs import Lab
from ..utils.errors import NotFoundError
from ..utils.pagination import resolve_pagination
from ..utils.security import require_scope


labs_bp = Blueprint("labs", __name__)


@labs_bp.route("/labs", methods=["GET"])
@jwt_required()
def list_labs():
    require_scope("db")
    pagination = resolve_pagination(request)
    query = Lab.query.order_by(Lab.created_at.desc())
    total = query.count()
    labs = query.offset(pagination.offset).limit(pagination.limit).all()
    return jsonify(
        {
            "data": [lab.to_dict() for lab in labs],
            "meta": {"total": total, "page": pagination.page, "size": pagination.size},
        }
    )


@labs_bp.route("/labs", methods=["POST"])
@jwt_required()
def create_lab():
    require_scope("db")
    payload = request.get_json(force=True)
    lab = Lab(
        name=payload["name"],
        description=payload.get("description"),
        location=payload.get("location"),
    )
    db.session.add(lab)
    db.session.flush()
    db.session.add(
        LabHistory(
            lab_id=lab.id, action="created", description=payload.get("description")
        )
    )
    db.session.commit()
    return jsonify({"data": lab.to_dict()}), 201


@labs_bp.route("/labs/<int:lab_id>", methods=["GET"])
@jwt_required()
def get_lab(lab_id: int):
    require_scope("db")
    lab = Lab.query.get(lab_id)
    if not lab:
        raise NotFoundError()
    return jsonify({"data": lab.to_dict()})


@labs_bp.route("/labs/<int:lab_id>", methods=["PUT"])
@jwt_required()
def update_lab(lab_id: int):
    require_scope("db")
    lab = Lab.query.get(lab_id)
    if not lab:
        raise NotFoundError()
    payload = request.get_json(force=True)
    for key in ("name", "description", "location"):
        if key in payload:
            setattr(lab, key, payload[key])
    db.session.add(
        LabHistory(
            lab_id=lab.id, action="updated", description=payload.get("description")
        )
    )
    db.session.commit()
    return jsonify({"data": lab.to_dict()})


@labs_bp.route("/labs/<int:lab_id>", methods=["DELETE"])
@jwt_required()
def delete_lab(lab_id: int):
    require_scope("db")
    lab = Lab.query.get(lab_id)
    if not lab:
        raise NotFoundError()
    db.session.add(
        LabHistory(lab_id=lab.id, action="deleted", description=lab.description)
    )
    db.session.delete(lab)
    db.session.commit()
    return "", 204
