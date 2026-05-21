"""Student Lifecycle Suite backend foundation module."""

from app.modules.student_lifecycle import models, permissions, repository, router, schemas, service

MODULE_NAME = "student_lifecycle"
TABLE_PREFIX = "sl_"
PROVIDER_INTEGRATION_ENABLED = False
SIS_SYNC_ENABLED = False
PLATONUS_LIVE_INTEGRATION_ENABLED = False
AUTONOMOUS_DECISION_ENABLED = False
FAKE_TRANSCRIPT_ENABLED = False
HIDDEN_SCORE_ENABLED = False
FAKE_METRICS_ENABLED = False

__all__ = [
    "AUTONOMOUS_DECISION_ENABLED",
    "FAKE_METRICS_ENABLED",
    "FAKE_TRANSCRIPT_ENABLED",
    "HIDDEN_SCORE_ENABLED",
    "MODULE_NAME",
    "PLATONUS_LIVE_INTEGRATION_ENABLED",
    "PROVIDER_INTEGRATION_ENABLED",
    "SIS_SYNC_ENABLED",
    "TABLE_PREFIX",
    "models",
    "permissions",
    "repository",
    "router",
    "schemas",
    "service",
]