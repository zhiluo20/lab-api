"""Sample CRUD API."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models.labs import Lab
from ..models.sample_history import SampleHistory
from ..models.samples import Sample
from ..utils.errors import APIError, NotFoundError
from ..utils.pagination import resolve_pagination
from ..utils.security import require_scope


samples_bp = Blueprint("samples", __name__)


@samples_bp.route("/samples", methods=["GET"])
@jwt_required()
def list_samples():
    require_scope("db")
    pagination = resolve_pagination(request)
    query = Sample.query.order_by(Sample.created_at.desc())
    total = query.count()
    items = query.offset(pagination.offset).limit(pagination.limit).all()
    return jsonify(
        {
            "data": [sample.to_dict() for sample in items],
            "meta": {"total": total, "page": pagination.page, "size": pagination.size},
        }
    )


@samples_bp.route("/samples", methods=["POST"])
@jwt_required()
def create_sample():
    require_scope("db")
    payload = request.get_json(force=True)
    lab_id = payload.get("lab_id")
    lab = Lab.query.get(lab_id)
    if not lab:
        raise APIError(
            code="lab_not_found", message="Lab does not exist", status_code=400
        )
    sample = Sample(
        lab_id=lab_id,
        code=payload["code"],
        status=payload.get("status", "pending"),
        description=payload.get("description"),
    )
    db.session.add(sample)
    db.session.flush()
    db.session.add(
        SampleHistory(
            sample_id=sample.id, action="created", notes=payload.get("description")
        )
    )
    db.session.commit()
    return jsonify({"data": sample.to_dict()}), 201


@samples_bp.route("/samples/<int:sample_id>", methods=["GET"])
@jwt_required()
def get_sample(sample_id: int):
    require_scope("db")
    sample = Sample.query.get(sample_id)
    if not sample:
        raise NotFoundError()
    return jsonify({"data": sample.to_dict()})


@samples_bp.route("/samples/<int:sample_id>", methods=["PUT"])
@jwt_required()
def update_sample(sample_id: int):
    require_scope("db")
    sample = Sample.query.get(sample_id)
    if not sample:
        raise NotFoundError()
    payload = request.get_json(force=True)
    for key in ("status", "description"):
        if key in payload:
            setattr(sample, key, payload[key])
    db.session.add(
        SampleHistory(
            sample_id=sample.id, action="updated", notes=payload.get("description")
        )
    )
    db.session.commit()
    return jsonify({"data": sample.to_dict()})


@samples_bp.route("/samples/<int:sample_id>", methods=["DELETE"])
@jwt_required()
def delete_sample(sample_id: int):
    require_scope("db")
    sample = Sample.query.get(sample_id)
    if not sample:
        raise NotFoundError()
    db.session.add(
        SampleHistory(sample_id=sample.id, action="deleted", notes=sample.description)
    )
    db.session.delete(sample)
    db.session.commit()
    return "", 204
