"""
Admissions Module - Phase 1: Schema, Models, Migration

This module provides the core data layer for the AI University Operating System
Admissions functionality, with strict tenant isolation and production-safe design.

Phase 1 includes:
- SQLAlchemy ORM models (models.py)
- Alembic migration (backend/alembic/versions/a1b2c3d4e5f6_create_admissions_tables.py)

Phase 2 (not in this phase):
- Pydantic schemas (schemas.py)
- Service layer (service.py)
- FastAPI routes (router.py)
- Tests

Usage:
    from app.modules.admissions.models import (
        ApplicantModel,
        ApplicationModel,
        ApplicationDocumentModel,
        ApplicationStageHistoryModel,
        ApplicationDecisionModel,
    )
"""

from .models import (
    ApplicantModel,
    ApplicationModel,
    ApplicationDocumentModel,
    ApplicationStageHistoryModel,
    ApplicationDecisionModel,
)

__all__ = [
    "ApplicantModel",
    "ApplicationModel",
    "ApplicationDocumentModel",
    "ApplicationStageHistoryModel",
    "ApplicationDecisionModel",
]
