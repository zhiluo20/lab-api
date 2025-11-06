"""Pytest fixtures for the Lab API."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Generator

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app import create_app  # noqa: E402
from app.config import Settings  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.doc import Doc  # noqa: E402
from app.models.invite import InviteCode  # noqa: E402
from app.models.labs import Lab  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.role_permission import RolePermission  # noqa: E402
from app.models.samples import Sample  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.user_permissions import UserPermissionEntry  # noqa: E402
from app.models.user_role import UserRole  # noqa: E402
from app.utils.security import hash_password  # noqa: E402

TEST_API_KEY = "test-api-key"


@pytest.fixture()
def app(tmp_path: Path) -> Generator:
    base_dir = tmp_path / "docs"
    base_dir.mkdir()

    settings = Settings(
        flask_env="testing",
        secret_key="test",
        jwt_secret_key="test-jwt",
        database_uri=f"sqlite:///{tmp_path}/test.db",
        rate_redis_url=None,
        api_keys_json={TEST_API_KEY: ["db", "doc"]},
        enable_swagger=False,
        base_file_dir=base_dir,
    )

    application = create_app(settings_override=settings)
    application.config.update(TESTING=True)

    with application.app_context():
        db.create_all()
        _seed_default_roles()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_user(app):
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("password"),
        is_admin=True,
    )
    db.session.add(user)
    db.session.flush()
    for scope in ("db", "doc"):
        db.session.add(UserPermissionEntry(user_id=user.id, scope=scope))
    admin_role = Role.query.filter_by(name="admin").first()
    if admin_role:
        db.session.add(UserRole(user_id=user.id, role_id=admin_role.id))
    invite = InviteCode(code="INVITE1", email=None, max_uses=5)
    db.session.add(invite)
    db.session.commit()
    return user


@pytest.fixture()
def invite_code(app):
    invite = InviteCode(code="INVITE2", email=None, max_uses=3)
    db.session.add(invite)
    db.session.commit()
    return invite


@pytest.fixture()
def sample_doc(app, admin_user):
    base_dir: Path = app.config["APP_SETTINGS"].base_file_dir
    file_path = base_dir / "example.docx"
    file_path.write_text("demo document")
    doc = Doc(
        name="Example", path=file_path.name, description="demo", owner_id=admin_user.id
    )
    db.session.add(doc)
    db.session.commit()
    return doc


@pytest.fixture()
def sample_data(app):
    lab = Lab(name="Chem Lab", description="Chemistry")
    db.session.add(lab)
    db.session.flush()
    sample = Sample(lab_id=lab.id, code="SAMPLE-1", status="pending")
    db.session.add(sample)
    db.session.commit()
    return lab, sample


def _seed_default_roles() -> None:
    if Role.query.count():
        return
    admin = Role(
        name="admin", description="Full administrative access.", is_default=False
    )
    editor = Role(
        name="editor", description="Edit and share documents.", is_default=True
    )
    viewer = Role(name="viewer", description="Read-only access.", is_default=False)
    db.session.add_all([admin, editor, viewer])
    db.session.flush()

    def add_perms(role: Role, perms: list[tuple[str, str]]) -> None:
        for resource, action in perms:
            db.session.add(
                RolePermission(role_id=role.id, resource=resource, action=action)
            )

    add_perms(
        admin,
        [
            ("users", "manage"),
            ("roles", "manage"),
            ("documents", "manage"),
            ("shares", "manage"),
            ("settings", "manage"),
        ],
    )
    add_perms(
        editor,
        [("documents", "write"), ("documents", "share"), ("documents", "comment")],
    )
    add_perms(viewer, [("documents", "read")])
    db.session.commit()
