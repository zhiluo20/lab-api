"""Administrative web views for managing users, roles, and documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from flask import Blueprint, flash, redirect, render_template, request, url_for
import sqlalchemy as sa
from sqlalchemy import or_

from ..extensions import db
from ..models.activity_log import ActivityLog
from ..models.doc import Doc
from ..models.doc_comment import DocComment
from ..models.doc_share import DocShare
from ..models.doc_version import DocVersion
from ..models.login_log import LoginLog
from ..models.role import Role
from ..models.role_permission import RolePermission
from ..models.user import User
from ..models.user_permissions import UserPermissionEntry
from ..models.user_role import UserRole
from ..services.auth_service import AuthService
from ..utils.errors import UnauthorizedError
from ..utils.security import decode_user_token, hash_password

admin_bp = Blueprint("admin", __name__, template_folder="../templates")

auth_service = AuthService()


@dataclass
class AdminContext:
    token: str
    user: User
    decoded: dict


def _log_activity(
    actor_id: int | None,
    action: str,
    target_type: str,
    target_id: str | None,
    details: dict | None = None,
) -> None:
    db.session.add(
        ActivityLog(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or {},
        )
    )
    db.session.commit()


def _get_admin_context(token: Optional[str]) -> AdminContext:
    if not token:
        raise UnauthorizedError(message="Missing token")
    user, decoded = decode_user_token(token)
    if not user.is_admin:
        raise UnauthorizedError(message="Admin privileges required")
    return AdminContext(token=token, user=user, decoded=decoded)


def _apply_user_filters(
    query, search: str | None, status: str | None
) -> Iterable[User]:
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(or_(User.username.ilike(like), User.email.ilike(like)))
    if status == "active":
        query = query.filter(User.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(User.is_active.is_(False))
    return query


@admin_bp.route("/admin")
def admin_index():
    token = request.args.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError:
        return redirect(url_for("web.login_page"))
    user_count = User.query.count()
    doc_count = Doc.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    roles = Role.query.count()
    recent_logs = (
        ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10).all()
    )
    return render_template(
        "admin_dashboard.html",
        token=ctx.token,
        current_user=ctx.user,
        stats={
            "users": user_count,
            "docs": doc_count,
            "active_users": active_users,
            "roles": roles,
        },
        recent_logs=recent_logs,
    )


@admin_bp.route("/admin/users", methods=["GET"])
def list_users():
    token = request.args.get("token")
    search = request.args.get("search")
    status = request.args.get("status")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    query = _apply_user_filters(User.query, search, status)
    users = query.order_by(User.created_at.desc()).all()
    roles = Role.query.order_by(Role.name.asc()).all()
    return render_template(
        "admin_users.html",
        users=users,
        roles=roles,
        token=ctx.token,
        current_user=ctx.user,
        filters={"search": search or "", "status": status or ""},
    )


@admin_bp.route("/admin/users/create", methods=["POST"])
def create_user():
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip() or "ChangeMe123!"
    role_ids = request.form.getlist("roles")
    scopes = request.form.getlist("scopes")
    status = request.form.get("status", "active")

    if not username or not email:
        flash("Username and email are required.", "error")
        return redirect(url_for("admin.list_users", token=ctx.token))

    if User.query.filter(or_(User.username == username, User.email == email)).first():
        flash("User with the same username or email already exists.", "error")
        return redirect(url_for("admin.list_users", token=ctx.token))

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        is_active=status != "inactive",
        is_admin="admin" in request.form.getlist("flags"),
    )
    db.session.add(user)
    db.session.flush()

    for scope in scopes or ["db", "doc"]:
        if scope not in {"db", "doc"}:
            continue
        db.session.add(UserPermissionEntry(user_id=user.id, scope=scope))

    for role_id in role_ids:
        role = Role.query.get(role_id)
        if role:
            db.session.add(UserRole(user_id=user.id, role_id=role.id))

    db.session.commit()
    _log_activity(
        ctx.user.id, "create_user", "user", str(user.id), {"username": username}
    )
    flash("User created successfully.", "success")
    return redirect(url_for("admin.list_users", token=ctx.token))


@admin_bp.route("/admin/users/<int:user_id>/update", methods=["POST"])
def update_user(user_id: int):
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    user = User.query.get_or_404(user_id)
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    status = request.form.get("status", "active")
    flags = request.form.getlist("flags")
    role_ids = {int(rid) for rid in request.form.getlist("roles")}

    if username:
        user.username = username
    if email:
        user.email = email
    if password:
        user.password_hash = hash_password(password)

    user.is_active = status != "inactive"
    user.is_admin = "admin" in flags

    # Sync roles
    current_roles = {assignment.role_id for assignment in user.roles}
    to_add = role_ids - current_roles
    to_remove = current_roles - role_ids

    for rid in to_add:
        db.session.add(UserRole(user_id=user.id, role_id=rid))
    if to_remove:
        UserRole.query.filter(
            UserRole.user_id == user.id, UserRole.role_id.in_(to_remove)
        ).delete(synchronize_session=False)

    db.session.commit()
    _log_activity(
        ctx.user.id, "update_user", "user", str(user.id), {"username": user.username}
    )
    flash("User updated.", "success")
    return redirect(url_for("admin.list_users", token=ctx.token))


@admin_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id: int):
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    _log_activity(
        ctx.user.id, "delete_user", "user", str(user_id), {"username": username}
    )
    flash("User deleted.", "success")
    return redirect(url_for("admin.list_users", token=ctx.token))


@admin_bp.route("/admin/users/<int:user_id>/scopes", methods=["POST"])
def update_user_scopes(user_id: int):
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    scope = request.form.get("scope")
    action = request.form.get("action")
    if scope not in {"db", "doc"}:
        flash("Invalid scope", "error")
        return redirect(url_for("admin.list_users", token=ctx.token))

    user = User.query.get_or_404(user_id)
    existing_scopes = {p.scope for p in user.permissions}
    if action == "add" and scope not in existing_scopes:
        user.permissions.append(UserPermissionEntry(scope=scope))
    elif action == "remove" and scope in existing_scopes:
        entry = next((p for p in user.permissions if p.scope == scope), None)
        if entry:
            db.session.delete(entry)
    else:
        flash("No changes applied", "info")
        return redirect(url_for("admin.list_users", token=ctx.token))

    db.session.commit()
    _log_activity(
        ctx.user.id,
        "update_scope",
        "user",
        str(user.id),
        {"scope": scope, "action": action},
    )
    flash("Scopes updated.", "success")
    return redirect(url_for("admin.list_users", token=ctx.token))


@admin_bp.route("/admin/users/<int:user_id>/status", methods=["POST"])
def update_user_status(user_id: int):
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    action = request.form.get("action")
    user = User.query.get_or_404(user_id)

    if action == "toggle_admin":
        user.is_admin = not user.is_admin
        flash(f"Admin flag set to {user.is_admin}", "success")
        _log_activity(
            ctx.user.id,
            "toggle_admin",
            "user",
            str(user.id),
            {"is_admin": user.is_admin},
        )
    elif action == "toggle_active":
        user.is_active = not user.is_active
        flash(f"Active flag set to {user.is_active}", "success")
        _log_activity(
            ctx.user.id,
            "toggle_active",
            "user",
            str(user.id),
            {"is_active": user.is_active},
        )
    else:
        flash("Unknown action", "error")

    db.session.commit()
    return redirect(url_for("admin.list_users", token=ctx.token))


@admin_bp.route("/admin/users/<int:user_id>/logs", methods=["GET"])
def user_login_logs(user_id: int):
    token = request.args.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    user = User.query.get_or_404(user_id)
    logs = (
        LoginLog.query.filter_by(user_id=user.id)
        .order_by(LoginLog.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template(
        "admin_user_logs.html",
        token=ctx.token,
        current_user=ctx.user,
        target_user=user,
        logs=logs,
    )


@admin_bp.route("/admin/roles", methods=["GET"])
def list_roles():
    token = request.args.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    roles = Role.query.order_by(Role.name.asc()).all()
    return render_template(
        "admin_roles.html",
        token=ctx.token,
        current_user=ctx.user,
        roles=roles,
        known_resources=["users", "documents", "shares", "settings", "analytics"],
        known_actions=["manage", "write", "read", "comment", "share"],
    )


@admin_bp.route("/admin/roles/create", methods=["POST"])
def create_role():
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    name = request.form.get("name", "").strip().lower()
    description = request.form.get("description", "").strip()
    is_default = request.form.get("is_default") == "on"

    if not name:
        flash("Role name required.", "error")
        return redirect(url_for("admin.list_roles", token=ctx.token))

    if Role.query.filter_by(name=name).first():
        flash("Role already exists.", "error")
        return redirect(url_for("admin.list_roles", token=ctx.token))

    role = Role(name=name, description=description, is_default=is_default)
    db.session.add(role)
    db.session.commit()
    _log_activity(ctx.user.id, "create_role", "role", str(role.id), {"name": name})
    flash("Role created.", "success")
    return redirect(url_for("admin.list_roles", token=ctx.token))


@admin_bp.route("/admin/roles/<int:role_id>/permissions", methods=["POST"])
def update_role_permissions(role_id: int):
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    role = Role.query.get_or_404(role_id)
    resource = request.form.get("resource")
    action = request.form.get("action")
    mode = request.form.get("mode")

    if mode == "add":
        if not RolePermission.query.filter_by(
            role_id=role.id, resource=resource, action=action
        ).first():
            db.session.add(
                RolePermission(role_id=role.id, resource=resource, action=action)
            )
            flash("Permission added.", "success")
    elif mode == "remove":
        RolePermission.query.filter_by(
            role_id=role.id, resource=resource, action=action
        ).delete()
        flash("Permission removed.", "success")

    db.session.commit()
    _log_activity(
        ctx.user.id,
        "update_role_permission",
        "role",
        str(role.id),
        {"resource": resource, "action": action, "mode": mode},
    )
    return redirect(url_for("admin.list_roles", token=ctx.token))


@admin_bp.route("/admin/roles/<int:role_id>/delete", methods=["POST"])
def delete_role(role_id: int):
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    role = Role.query.get_or_404(role_id)
    if role.name == "admin":
        flash("Cannot delete core admin role.", "error")
        return redirect(url_for("admin.list_roles", token=ctx.token))

    db.session.delete(role)
    db.session.commit()
    _log_activity(ctx.user.id, "delete_role", "role", str(role_id), {})
    flash("Role deleted.", "success")
    return redirect(url_for("admin.list_roles", token=ctx.token))


@admin_bp.route("/admin/documents", methods=["GET"])
def list_documents():
    token = request.args.get("token")
    search = request.args.get("search", "")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    query = Doc.query
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(or_(Doc.name.ilike(like), Doc.description.ilike(like)))
    documents = query.order_by(Doc.updated_at.desc()).paginate(
        page=request.args.get("page", 1, type=int), per_page=20, error_out=False
    )
    return render_template(
        "admin_documents.html",
        token=ctx.token,
        current_user=ctx.user,
        documents=documents,
        search=search,
    )


@admin_bp.route("/admin/documents/<int:doc_id>", methods=["GET"])
def document_detail(doc_id: int):
    token = request.args.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    doc = Doc.query.get_or_404(doc_id)
    versions = (
        DocVersion.query.filter_by(doc_id=doc.id)
        .order_by(DocVersion.version_number.desc())
        .all()
    )
    comments = (
        DocComment.query.filter_by(doc_id=doc.id)
        .order_by(DocComment.created_at.desc())
        .all()
    )
    shares = DocShare.query.filter_by(doc_id=doc.id).all()
    return render_template(
        "admin_document_detail.html",
        token=ctx.token,
        current_user=ctx.user,
        document=doc,
        versions=versions,
        comments=comments,
        shares=shares,
    )


@admin_bp.route("/admin/documents/<int:doc_id>/versions", methods=["POST"])
def create_document_version(doc_id: int):
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    doc = Doc.query.get_or_404(doc_id)
    note = request.form.get("note", "")
    version_number = (
        db.session.query(sa.func.coalesce(sa.func.max(DocVersion.version_number), 0))
        .filter_by(doc_id=doc.id)
        .scalar()
        + 1
    )
    db.session.add(
        DocVersion(
            doc_id=doc.id,
            version_number=version_number,
            path=doc.path,
            created_by=ctx.user.id,
            note=note,
        )
    )
    db.session.commit()
    _log_activity(
        ctx.user.id,
        "create_doc_version",
        "doc",
        str(doc.id),
        {"version": version_number},
    )
    flash("Version recorded.", "success")
    return redirect(url_for("admin.document_detail", doc_id=doc.id, token=ctx.token))


@admin_bp.route("/admin/documents/<int:doc_id>/comments", methods=["POST"])
def add_document_comment(doc_id: int):
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    doc = Doc.query.get_or_404(doc_id)
    content = request.form.get("content", "").strip()
    if not content:
        flash("Comment cannot be empty.", "error")
        return redirect(
            url_for("admin.document_detail", doc_id=doc.id, token=ctx.token)
        )

    db.session.add(DocComment(doc_id=doc.id, user_id=ctx.user.id, content=content))
    db.session.commit()
    _log_activity(ctx.user.id, "comment_doc", "doc", str(doc.id), {})
    flash("Comment added.", "success")
    return redirect(url_for("admin.document_detail", doc_id=doc.id, token=ctx.token))


@admin_bp.route("/admin/documents/<int:doc_id>/share", methods=["POST"])
def share_document(doc_id: int):
    token = request.form.get("token")
    try:
        ctx = _get_admin_context(token)
    except UnauthorizedError as exc:
        flash(exc.message, "error")
        return redirect(url_for("web.login_page"))

    doc = Doc.query.get_or_404(doc_id)
    access_level = request.form.get("access_level", "viewer")
    shared_with_email = request.form.get("shared_with_email", "").strip()
    shared_with_user_id = request.form.get("shared_with_user_id")

    share = DocShare(
        doc_id=doc.id,
        shared_with_email=shared_with_email or None,
        shared_with_user_id=int(shared_with_user_id) if shared_with_user_id else None,
        access_level=access_level,
        created_by=ctx.user.id,
    )
    db.session.add(share)
    db.session.commit()
    _log_activity(
        ctx.user.id, "share_doc", "doc", str(doc.id), {"access_level": access_level}
    )
    flash("Share saved.", "success")
    return redirect(url_for("admin.document_detail", doc_id=doc.id, token=ctx.token))
