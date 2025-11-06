"""Helpers for consistent pagination handling."""

from __future__ import annotations

from dataclasses import dataclass

from flask import Request


@dataclass(slots=True)
class Pagination:
    page: int
    size: int
    limit: int
    offset: int


DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def resolve_pagination(
    request: Request, default_size: int = DEFAULT_PAGE_SIZE
) -> Pagination:
    """Resolve page and size query params into sane defaults."""
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
    page = max(page, 1)

    try:
        size = int(request.args.get("size", default_size))
    except ValueError:
        size = default_size
    size = max(1, min(size, MAX_PAGE_SIZE))

    limit = size
    offset = (page - 1) * size
    return Pagination(page=page, size=size, limit=limit, offset=offset)
