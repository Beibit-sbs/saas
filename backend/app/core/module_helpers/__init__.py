from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.router_errors import (
    integrity_error_to_http,
    permission_error_to_http,
    tenant_not_found_to_http,
    validation_error_to_http,
)
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    OptimisticLockConflictError,
    TenantRequiredError,
    TenantResourceNotFoundError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)

__all__ = [
    "build_audit_action",
    "integrity_error_to_http",
    "permission_error_to_http",
    "tenant_not_found_to_http",
    "validation_error_to_http",
    "DomainValidationError",
    "OptimisticLockConflictError",
    "TenantRequiredError",
    "TenantResourceNotFoundError",
    "assert_resource_belongs_to_tenant",
    "validate_tenant_id_provided",
    "validate_version_match",
]
