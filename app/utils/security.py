"""Security utilities for authentication and authorization."""

from __future__ import annotations

import secrets
from typing import Iterable, Sequence, Tuple, Dict, Any

from flask_jwt_extended import get_jwt, get_jwt_identity, decode_token
from flask_jwt_extended.exceptions import JWTExtendedException
from passlib.hash import pbkdf2_sha256, scrypt

from ..models.user import User
from .errors import UnauthorizedError


def hash_password(raw_password: str) -> str:
    """Return a PBKDF2 hashed password string."""
    return pbkdf2_sha256.hash(raw_password)


def verify_password(raw_password: str, hashed_password: str) -> bool:
    """Validate a PBKDF2 or scrypt hash."""
    if hashed_password.startswith("$pbkdf2-sha256$"):
        return pbkdf2_sha256.verify(raw_password, hashed_password)
    if hashed_password.startswith("$scrypt$"):
        return scrypt.verify(raw_password, hashed_password)
    # Default to PBKDF2 for legacy hashes without prefix
    try:
        return pbkdf2_sha256.verify(raw_password, hashed_password)
    except ValueError:
        return False


def generate_token(length: int = 32) -> str:
    """Create a secure random token."""
    return secrets.token_urlsafe(length)


def require_scope(required: str) -> None:
    """Ensure the JWT includes a given scope."""
    claims = get_jwt()
    scopes: Sequence[str] = claims.get("scopes", [])
    if required not in scopes:
        raise UnauthorizedError(message="Scope missing", details={"required": required})


def require_any_scope(required_scopes: Iterable[str]) -> None:
    """Ensure the JWT includes at least one scope."""
    claims = get_jwt()
    token_scopes: set[str] = set(claims.get("scopes", []))
    if not token_scopes.intersection(set(required_scopes)):
        raise UnauthorizedError(
            message="Insufficient scope", details={"required": list(required_scopes)}
        )


def ensure_admin() -> None:
    """Require that the JWT belongs to an administrator."""
    claims = get_jwt()
    if not claims.get("is_admin"):
        raise UnauthorizedError(message="Admin privileges required")


def get_current_user() -> User:
    """Return the authenticated user from the current JWT."""
    identity = get_jwt_identity() or {}
    if identity.get("sub_type") != "user":
        raise UnauthorizedError(message="User token required")
    user_id = identity.get("user_id")
    user: User | None = User.query.get(user_id)
    if not user or not user.is_active:
        raise UnauthorizedError(message="User not found or inactive")
    return user


def token_from_invite(code: str) -> str:
    """Generate deterministic tokens for invite codes (used for testing)."""
    return secrets.token_urlsafe(16) + code[-4:]


def decode_user_token(
    token: str, *, allow_expired: bool = False
) -> Tuple[User, Dict[str, Any]]:
    """Decode a standalone JWT access token and return the associated user."""
    try:
        decoded = decode_token(token, allow_expired=allow_expired)
    except JWTExtendedException as exc:
        raise UnauthorizedError(message=str(exc)) from exc
    identity = decoded.get("sub")
    user_id = None
    if isinstance(identity, dict):
        if identity.get("sub_type") != "user":
            raise UnauthorizedError(message="Token is not a user token")
        user_id = identity.get("user_id")
    else:
        user_id = identity
    user = User.query.get(user_id)
    if not user:
        raise UnauthorizedError(message="User not found")
    return user, decoded
