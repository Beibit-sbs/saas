"""F3 service-level negative tests.

Validates freeze-guard behaviour and not-found paths without requiring a live DB.
All DB access is monkeypatched to return None / empty list.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantRequiredError,
    TenantResourceNotFoundError,
)
from app.modules.interventions.effectiveness_schemas import (
    CohortAnalyzeRequestSchema,
    CohortFinalizeRequestSchema,
)
from app.modules.interventions.effectiveness_service import (
    InterventionEffectivenessService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(scalar_return=None, scalars_return=None):
    """Return a service wired to a mock SQLAlchemy Session."""
    db = MagicMock()
    db.scalar.return_value = scalar_return
    scalars_mock = MagicMock()
    scalars_mock.__iter__ = MagicMock(return_value=iter(scalars_return or []))
    db.scalars.return_value = scalars_mock
    return InterventionEffectivenessService(db=db)


# ---------------------------------------------------------------------------
# Freeze-guard tests
# ---------------------------------------------------------------------------

def test_finalize_cohort_raises_domain_validation_error() -> None:
    """finalize_cohort is frozen — must always raise DomainValidationError."""
    svc = _make_service()
    payload = CohortFinalizeRequestSchema(
        playbook_id=1,
        cohort_name="cohort-2026-q1",
        analysis_window_start="2026-01-01",
        analysis_window_end="2026-03-31",
    )
    with pytest.raises(DomainValidationError, match="frozen"):
        svc.finalize_cohort(tenant_id=1, actor="tester", payload=payload)


def test_analyze_cohort_raises_domain_validation_error_after_404_check() -> None:
    """analyze_cohort must raise DomainValidationError (frozen) for existing cohort."""
    # Return a fake cohort that passes tenant check
    fake_cohort = MagicMock()
    fake_cohort.tenant_id = 1
    svc = _make_service(scalar_return=fake_cohort)

    payload = CohortAnalyzeRequestSchema(recalculate=True)
    with pytest.raises(DomainValidationError, match="frozen"):
        svc.analyze_cohort(tenant_id=1, cohort_id=99, actor="tester", payload=payload)


def test_analyze_cohort_raises_not_found_when_cohort_missing() -> None:
    """analyze_cohort must raise TenantResourceNotFoundError when cohort is None."""
    svc = _make_service(scalar_return=None)

    payload = CohortAnalyzeRequestSchema(recalculate=False)
    with pytest.raises(TenantResourceNotFoundError, match="not found"):
        svc.analyze_cohort(tenant_id=1, cohort_id=9999, actor="tester", payload=payload)


# ---------------------------------------------------------------------------
# Not-found path tests
# ---------------------------------------------------------------------------

def test_get_outcomes_raises_not_found_when_cohort_missing() -> None:
    """get_outcomes must raise TenantResourceNotFoundError when cohort is absent."""
    svc = _make_service(scalar_return=None)

    with pytest.raises(TenantResourceNotFoundError, match="not found"):
        svc.get_outcomes(tenant_id=1, cohort_id=42)


def test_get_outcomes_returns_empty_list_when_no_outcomes() -> None:
    """get_outcomes returns [] for cohort with zero outcome rows."""
    fake_cohort = MagicMock()
    fake_cohort.tenant_id = 1
    svc = _make_service(scalar_return=fake_cohort, scalars_return=[])

    result = svc.get_outcomes(tenant_id=1, cohort_id=1)
    assert result == []


def test_get_latest_by_playbook_raises_not_found() -> None:
    """get_latest_by_playbook raises TenantResourceNotFoundError when no cohort for playbook."""
    svc = _make_service(scalar_return=None)

    with pytest.raises(TenantResourceNotFoundError, match="No cohort found"):
        svc.get_latest_by_playbook(tenant_id=1, playbook_id=7)


# ---------------------------------------------------------------------------
# Tenant validation guardrail
# ---------------------------------------------------------------------------

def test_finalize_cohort_validates_tenant_id_zero() -> None:
    """tenant_id=0 must be rejected (TenantRequiredError) before freeze guard fires."""
    svc = _make_service()
    payload = CohortFinalizeRequestSchema(
        playbook_id=1,
        cohort_name="cohort-zero-tenant",
        analysis_window_start="2026-01-01",
        analysis_window_end="2026-03-31",
    )
    with pytest.raises(TenantRequiredError, match="positive integer"):
        svc.finalize_cohort(tenant_id=0, actor="tester", payload=payload)
