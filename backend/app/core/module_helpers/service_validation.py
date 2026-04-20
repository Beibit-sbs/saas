from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class MutationResult(Generic[T]):
    """Wrap a service mutation return with an idempotent-replay flag."""
    entity: T
    idempotent_replay: bool = False


class TenantRequiredError(ValueError):
    """Raised when tenant_id is absent or invalid."""


class DomainValidationError(ValueError):
    """Raised for domain-level request validation errors (HTTP 400)."""


class TenantResourceNotFoundError(ValueError):
    """Raised when a resource is missing in tenant scope (HTTP 404)."""


class OptimisticLockConflictError(ValueError):
    """Raised when expected and current versions diverge (HTTP 409)."""


@dataclass(frozen=True)
class ResourceIdentity:
    resource_name: str
    resource_id: int | None = None


def validate_tenant_id_provided(tenant_id: int | None) -> int:
    """Validate tenant_id using a strict fail-closed contract."""
    if tenant_id is None:
        raise TenantRequiredError("tenant_id must be provided explicitly")
    try:
        normalized = int(tenant_id)
    except (TypeError, ValueError) as exc:
        raise TenantRequiredError("tenant_id must be a positive integer") from exc
    if normalized <= 0:
        raise TenantRequiredError("tenant_id must be a positive integer")
    return normalized


def assert_resource_belongs_to_tenant(
    resource: object | None,
    tenant_id: int,
    *,
    resource_name: str = "resource",
    resource_id: int | None = None,
) -> None:
    """Assert that a loaded ORM resource belongs to tenant_id."""
    if resource is None:
        suffix = f" {resource_id}" if resource_id is not None else ""
        raise TenantResourceNotFoundError(
            f"{resource_name}{suffix} not found or does not belong to tenant {tenant_id}"
        )

    resource_tenant_id = getattr(resource, "tenant_id", None)
    if resource_tenant_id != tenant_id:
        suffix = f" {resource_id}" if resource_id is not None else ""
        raise TenantResourceNotFoundError(
            f"{resource_name}{suffix} not found or does not belong to tenant {tenant_id}"
        )


def validate_version_match(current_version: int, expected_version: int) -> None:
    """Validate optimistic lock version. Raises conflict on mismatch."""
    if int(current_version) != int(expected_version):
        raise OptimisticLockConflictError(
            f"Version mismatch: expected {expected_version}, but current version is {current_version}"
        )
