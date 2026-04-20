"""
Tests for interventions/effectiveness_router.py — cohort endpoints.

Exercises list/detail/finalize/outcomes/latest/analyze HTTP paths including error branches.
"""

from __future__ import annotations

from datetime import date, datetime, UTC
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from tests.conftest import _auth_headers, client
from app.main import app
from app.modules.interventions.dependencies import get_interventions_db
from app.modules.auth.token_service import create_access_token
from app.modules.rbac import service as rbac_service

BASE = "/api/admin/interventions/cohorts"


def _make_headers_with_permissions(user_id: str, roles: list[str], tenant_id: int, extra_perms: set[str]) -> dict[str, str]:
    base_perms = set(rbac_service.resolve_permissions_for_tenant(roles, tenant_id=tenant_id))
    all_perms = sorted(base_perms | extra_perms)
    token = create_access_token(user_id=user_id, roles=roles, auth_source="test", tenant_id=tenant_id, permissions=all_perms)
    return {"Authorization": f"Bearer {token}"}


_EXTRA_PERMS = {"interventions:view", "interventions:execute_playbook"}
ADMIN_HEADERS = _make_headers_with_permissions("owner@example.com", ["admin"], 1, _EXTRA_PERMS)


_now = datetime(2026, 4, 20, 10, 0, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _override_interventions_db():
    session = MagicMock(spec=Session)
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.refresh = MagicMock()
    app.dependency_overrides[get_interventions_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_interventions_db, None)


# ---------------------------------------------------------------------------
# mock cohort / outcome objects
# ---------------------------------------------------------------------------


def _mock_cohort(cohort_id: int = 1):
    """Return a dict that Pydantic v2 model_validate() can handle."""
    return {
        "id": cohort_id,
        "tenant_id": 1,
        "playbook_id": 10,
        "cohort_name": "Test Cohort",
        "analysis_window_start": date(2026, 1, 1),
        "analysis_window_end": date(2026, 3, 31),
        "student_count": 50,
        "data_completeness_pct": Decimal("0.95"),
        "status": "analyzed",
        "created_by": "owner@example.com",
        "created_at": _now,
    }


def _mock_outcome(outcome_id: int = 1):
    """Return a dict that Pydantic v2 model_validate() can handle."""
    return {
        "id": outcome_id,
        "tenant_id": 1,
        "cohort_id": 1,
        "outcome_type": "dropout_rate",
        "segment_name": None,
        "outcome_value_treated": Decimal("0.85"),
        "outcome_value_control": Decimal("0.70"),
        "uplift_pp": Decimal("15.0"),
        "uplift_confidence_p5": Decimal("8.0"),
        "uplift_confidence_p95": Decimal("22.0"),
        "measurement_completeness_pct": Decimal("0.90"),
        "measured_at": _now,
        "notes": None,
    }


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


class TestListCohorts:
    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_success(self, mock_cls):
        svc = mock_cls.return_value
        svc.list_cohorts.return_value = [_mock_cohort(1), _mock_cohort(2)]
        resp = client.get(BASE, headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["id"] == 1

    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_list_infers_status_field(self, mock_cls):
        svc = mock_cls.return_value
        draft = _mock_cohort(1)
        draft["student_count"] = 0
        draft["data_completeness_pct"] = None
        draft["status"] = "draft"
        finalized = _mock_cohort(2)
        finalized["student_count"] = 30
        finalized["data_completeness_pct"] = None
        finalized["status"] = "finalized"
        analyzed = _mock_cohort(3)
        analyzed["student_count"] = 40
        analyzed["data_completeness_pct"] = Decimal("0.91")
        analyzed["status"] = "analyzed"

        svc.list_cohorts.return_value = [draft, finalized, analyzed]
        resp = client.get(BASE, headers=ADMIN_HEADERS)

        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["status"] == "draft"
        assert data[1]["status"] == "finalized"
        assert data[2]["status"] == "analyzed"

    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_domain_error(self, mock_cls):
        from app.core.module_helpers.service_validation import DomainValidationError
        svc = mock_cls.return_value
        svc.list_cohorts.side_effect = DomainValidationError("invalid tenant")
        resp = client.get(BASE, headers=ADMIN_HEADERS)
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /finalize
# ---------------------------------------------------------------------------


class TestFinalizeCohort:
    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_success(self, mock_cls):
        cohort = _mock_cohort()
        svc = mock_cls.return_value
        svc.finalize_cohort.return_value = cohort
        resp = client.post(
            f"{BASE}/finalize",
            headers=ADMIN_HEADERS,
            json={
                "playbook_id": 10,
                "cohort_name": "Test Cohort",
                "analysis_window_start": "2026-01-01",
                "analysis_window_end": "2026-03-31",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["cohort_name"] == "Test Cohort"
        assert data["playbook_id"] == 10

    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_finalize_existing_success(self, mock_cls):
        cohort = _mock_cohort(11)
        cohort["status"] = "finalized"
        cohort["student_count"] = 1

        svc = mock_cls.return_value
        svc.finalize_existing_cohort.return_value = cohort

        resp = client.post(f"{BASE}/11/finalize", headers=ADMIN_HEADERS, json={})
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == 11
        assert body["status"] == "finalized"

    def test_validation_error(self):
        resp = client.post(
            f"{BASE}/finalize",
            headers=ADMIN_HEADERS,
            json={"playbook_id": 10},  # missing required fields
        )
        assert resp.status_code == 400

    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_domain_error(self, mock_cls):
        from app.core.module_helpers.service_validation import DomainValidationError
        svc = mock_cls.return_value
        svc.finalize_cohort.side_effect = DomainValidationError("window invalid")
        resp = client.post(
            f"{BASE}/finalize",
            headers=ADMIN_HEADERS,
            json={
                "playbook_id": 10,
                "cohort_name": "C",
                "analysis_window_start": "2026-01-01",
                "analysis_window_end": "2026-03-31",
            },
        )
        assert resp.status_code == 400

    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_not_found_error(self, mock_cls):
        from app.core.module_helpers.service_validation import TenantResourceNotFoundError
        svc = mock_cls.return_value
        svc.finalize_cohort.side_effect = TenantResourceNotFoundError("pb not found")
        resp = client.post(
            f"{BASE}/finalize",
            headers=ADMIN_HEADERS,
            json={
                "playbook_id": 999,
                "cohort_name": "C",
                "analysis_window_start": "2026-01-01",
                "analysis_window_end": "2026-03-31",
            },
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /{cohort_id}/outcomes
# ---------------------------------------------------------------------------


class TestGetCohortOutcomes:
    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_success(self, mock_cls):
        svc = mock_cls.return_value
        svc.get_outcomes.return_value = [_mock_outcome()]
        resp = client.get(f"{BASE}/1/outcomes", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_not_found(self, mock_cls):
        from app.core.module_helpers.service_validation import TenantResourceNotFoundError
        svc = mock_cls.return_value
        svc.get_outcomes.side_effect = TenantResourceNotFoundError("no cohort")
        resp = client.get(f"{BASE}/999/outcomes", headers=ADMIN_HEADERS)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /latest/by-playbook/{playbook_id}
# ---------------------------------------------------------------------------


class TestGetLatestByPlaybook:
    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_success(self, mock_cls):
        cohort = _mock_cohort()
        svc = mock_cls.return_value
        svc.get_latest_by_playbook.return_value = cohort
        resp = client.get(f"{BASE}/latest/by-playbook/10", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["playbook_id"] == 10

    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_not_found(self, mock_cls):
        from app.core.module_helpers.service_validation import TenantResourceNotFoundError
        svc = mock_cls.return_value
        svc.get_latest_by_playbook.side_effect = TenantResourceNotFoundError("no cohort for pb")
        resp = client.get(f"{BASE}/latest/by-playbook/999", headers=ADMIN_HEADERS)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /{cohort_id}
# ---------------------------------------------------------------------------


class TestGetCohortDetail:
    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_success(self, mock_cls):
        svc = mock_cls.return_value
        svc.get_cohort.return_value = _mock_cohort(22)
        resp = client.get(f"{BASE}/22", headers=ADMIN_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 22

    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_not_found(self, mock_cls):
        from app.core.module_helpers.service_validation import TenantResourceNotFoundError
        svc = mock_cls.return_value
        svc.get_cohort.side_effect = TenantResourceNotFoundError("no cohort")
        resp = client.get(f"{BASE}/999", headers=ADMIN_HEADERS)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /{cohort_id}/analyze
# ---------------------------------------------------------------------------


class TestAnalyzeCohort:
    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_success(self, mock_cls):
        result = {"cohort_id": 1, "status": "completed", "detail": "Analysis done", "requested_at": _now}
        svc = mock_cls.return_value
        svc.analyze_cohort.return_value = result
        resp = client.post(
            f"{BASE}/1/analyze",
            headers=ADMIN_HEADERS,
            json={"segment_keys": ["gender"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"

    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_analyze_requires_finalized_cohort(self, mock_cls):
        from app.core.module_helpers.service_validation import DomainValidationError

        svc = mock_cls.return_value
        svc.analyze_cohort.side_effect = DomainValidationError("Cohort must be finalized before analysis.")

        resp = client.post(
            f"{BASE}/1/analyze",
            headers=ADMIN_HEADERS,
            json={"segment_keys": []},
        )
        assert resp.status_code == 400
        assert "finalized" in str(resp.json()).lower()

    @patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService")
    def test_domain_error(self, mock_cls):
        from app.core.module_helpers.service_validation import DomainValidationError
        svc = mock_cls.return_value
        svc.analyze_cohort.side_effect = DomainValidationError("no data")
        resp = client.post(
            f"{BASE}/1/analyze",
            headers=ADMIN_HEADERS,
            json={"segment_keys": []},
        )
        assert resp.status_code == 400

    def test_empty_body_uses_defaults(self):
        """Empty segment_keys should still parse OK — it's optional with default=[]."""
        with patch("app.modules.interventions.effectiveness_router.InterventionEffectivenessService") as mock_cls:
            result = {"cohort_id": 1, "status": "completed", "detail": "Analysis done", "requested_at": _now}
            mock_cls.return_value.analyze_cohort.return_value = result
            resp = client.post(
                f"{BASE}/1/analyze",
                headers=ADMIN_HEADERS,
                json={},
            )
            assert resp.status_code == 200
