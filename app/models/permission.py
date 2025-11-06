"""Permission metadata utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Dict, List


@dataclass(frozen=True)
class Permission:
    code: str
    description: str

    _registry: ClassVar[Dict[str, "Permission"]] = {}

    @classmethod
    def register(cls, code: str, description: str) -> "Permission":
        perm = cls(code=code, description=description)
        cls._registry[code] = perm
        return perm

    @classmethod
    def all(cls) -> List["Permission"]:
        return list(cls._registry.values())


DB_SCOPE = Permission.register("db", "Database CRUD access")
DOC_SCOPE = Permission.register("doc", "Document viewing and editing")
