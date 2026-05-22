"""Academic Operations backend foundation module."""

from app.modules.academic_operations import (
    dependencies,
    models,
    permissions,
    repository,
    router,
    schemas,
    service,
)

MODULE_NAME = "academic_operations"
TABLE_PREFIX = "ao_"
TARGET_LEVEL = "L3"
CONTRACT_VERSION = "A-036.2"
FOUNDATION_STATUS = "MATRIX_GUIDED_CANONICAL_AWARE_BACKEND_FOUNDATION"
MASTER_MATRIX_COMMIT = "c79cc31"
MATRIX_ROW_COUNT = 467
DUPLICATE_MODULE_POLICY = "REUSE_CANONICALS_AND_BRIDGE_ONLY"
PROVIDER_INTEGRATION_ENABLED = False
SIS_SYNC_ENABLED = False
PLATONUS_SYNC_ENABLED = False
AUTOMATED_DECISION_ENABLED = False
HIDDEN_SCORE_ENABLED = False
FAKE_METRICS_ENABLED = False

__all__ = [
    "AUTOMATED_DECISION_ENABLED",
    "CONTRACT_VERSION",
    "DUPLICATE_MODULE_POLICY",
    "FAKE_METRICS_ENABLED",
    "FOUNDATION_STATUS",
    "HIDDEN_SCORE_ENABLED",
    "MASTER_MATRIX_COMMIT",
    "MATRIX_ROW_COUNT",
    "MODULE_NAME",
    "PLATONUS_SYNC_ENABLED",
    "PROVIDER_INTEGRATION_ENABLED",
    "SIS_SYNC_ENABLED",
    "TABLE_PREFIX",
    "TARGET_LEVEL",
    "dependencies",
    "models",
    "permissions",
    "repository",
    "router",
    "schemas",
    "service",
]