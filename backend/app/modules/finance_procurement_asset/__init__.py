"""Finance / Procurement / Asset backend runtime module."""

from app.modules.finance_procurement_asset import (
    dependencies,
    models,
    permissions,
    repository,
    router,
    schemas,
    service,
)

MODULE_NAME = models.MODULE_NAME
API_PREFIX = models.API_PREFIX
RUNTIME_MODE = models.RUNTIME_MODE
EXPECTED_TABLE_COUNT = models.EXPECTED_TABLE_COUNT
EXPECTED_ROUTE_COUNT = models.EXPECTED_ROUTE_COUNT
EXPECTED_PERMISSION_COUNT = models.EXPECTED_PERMISSION_COUNT
TABLE_PREFIX = models.TABLE_PREFIX

__all__ = [
    "API_PREFIX",
    "EXPECTED_PERMISSION_COUNT",
    "EXPECTED_ROUTE_COUNT",
    "EXPECTED_TABLE_COUNT",
    "MODULE_NAME",
    "RUNTIME_MODE",
    "TABLE_PREFIX",
    "dependencies",
    "models",
    "permissions",
    "repository",
    "router",
    "schemas",
    "service",
]