from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class FileRecord:
    tenant_id: int
    file_key: str
    owner_actor: str
    filename: str
    content_type: str
    size_bytes: int
    metadata: dict[str, Any] = field(default_factory=dict)


class FileStorageBackend(Protocol):
    def put(self, key: str, content: bytes, content_type: str) -> None:
        ...

    def get(self, key: str) -> bytes:
        ...


def validate_file_key(file_key: str) -> str:
    normalized = str(file_key).strip().replace("\\", "/")
    if not normalized:
        raise ValueError("file_key is required")
    if normalized.startswith("/"):
        raise ValueError("absolute paths are not allowed")
    if ".." in normalized.split("/"):
        raise ValueError("path traversal is not allowed")
    if len(normalized) > 512:
        raise ValueError("file_key is too long")
    return normalized


def make_tenant_file_key(*, tenant_id: int, namespace: str, filename: str) -> str:
    normalized_tenant_id = int(tenant_id)
    if normalized_tenant_id <= 0:
        raise ValueError("tenant_id must be positive")
    normalized_namespace = str(namespace).strip().lower().replace(" ", "-")
    normalized_filename = str(filename).strip()
    if not normalized_namespace:
        raise ValueError("namespace is required")
    if not normalized_filename:
        raise ValueError("filename is required")
    key = f"tenant/{normalized_tenant_id}/{normalized_namespace}/{normalized_filename}"
    return validate_file_key(key)
