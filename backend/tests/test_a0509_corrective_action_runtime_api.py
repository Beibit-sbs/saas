from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.core.tenant import get_current_tenant
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.quality_accreditation.dependencies import get_quality_accreditation_db
from app.modules.quality_accreditation.models import QualityAuditFinding, QualityEvidenceRegistry, QualityImprovementAction
from app.modules.quality_accreditation.quality_accreditation_corrective_action_schemas import (
    CorrectiveActionItem,
    CorrectiveActionRuntimeResponse,
    CorrectiveActionSummary,
)
from app.modules.quality_accreditation.quality_accreditation_corrective_action_service import CorrectiveActionRuntimeService
from tests.conftest import client


BASE = "/api/v1/quality-accreditation/corrective-actions"


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_quality_accreditation_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_quality_accreditation_db, None)
    app.dependency_overrides.pop(get_current_tenant, None)


def _headers(*, tenant_id: int = 1, permissions: list[str] | None = None, roles: list[str] | None = None) -> dict[str, str]:
    token = create_access_token(
        user_id="710",
        roles=roles or ["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permissions if permissions is not None else ["quality_accreditation.summary.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def _build_rows(tenant_id: int):
    ts = datetime(2026, 6, 11, tzinfo=UTC)
    return {
        QualityImprovementAction: [
            SimpleNamespace(
                id=tenant_id * 10 + 1,
                tenant_id=tenant_id,
                action_ref=f"ACT-{tenant_id}-1",
                title="Close curriculum evidence gaps",
                standard_ref=f"STD-{tenant_id}-A",
                plan_ref=f"PLAN-{tenant_id}-1",
                owner_ref="academic_operations",
                status="ACTIVE",
                updated_at=ts,
                archived_at=ts + timedelta(days=10),
            ),
            SimpleNamespace(
                id=tenant_id * 10 + 2,
                tenant_id=tenant_id,
                action_ref=f"ACT-{tenant_id}-2",
                title="Resolve faculty documentation backlog",
                standard_ref=f"STD-{tenant_id}-B",
                plan_ref=f"PLAN-{tenant_id}-2",
                owner_ref="quality_accreditation",
                status="DELAYED",
                updated_at=ts,
                archived_at=ts - timedelta(days=3),
            ),
        ],
        QualityEvidenceRegistry: [
            SimpleNamespace(tenant_id=tenant_id, standard_ref=f"STD-{tenant_id}-A"),
            SimpleNamespace(tenant_id=tenant_id, standard_ref=f"STD-{tenant_id}-A"),
            SimpleNamespace(tenant_id=tenant_id, standard_ref=f"STD-{tenant_id}-B"),
        ],
        QualityAuditFinding: [
            SimpleNamespace(tenant_id=tenant_id, finding_ref=f"FIND-{tenant_id}-001", action_ref=f"ACT-{tenant_id}-1"),
        ],
    }


def test_corrective_action_runtime_requires_auth() -> None:
    assert client.get(BASE).status_code in (401, 403)


def test_corrective_action_runtime_requires_summary_read_permission() -> None:
    response = client.get(BASE, headers=_headers(permissions=[], roles=["student"]))
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("app.modules.quality_accreditation.corrective_action_runtime_router.corrective_action_runtime_service.get_corrective_action_runtime")
def test_corrective_action_runtime_response_contract(mock_service) -> None:
    mock_service.return_value = CorrectiveActionRuntimeResponse(
        tenant_id=1,
        generated_at=datetime(2026, 6, 11, tzinfo=UTC),
        corrective_actions=[
            CorrectiveActionItem(
                action_id="ACT-1",
                action_title="Close curriculum evidence gaps",
                accreditation_standard="STD-A",
                finding_reference="FIND-1",
                owner_unit="academic_operations",
                due_date=datetime(2026, 6, 30, tzinfo=UTC),
                completion_percentage=75,
                status="ACTIVE",
                readiness_score=78,
                risk_level="MEDIUM",
                overdue_flag=False,
                last_updated=datetime(2026, 6, 11, tzinfo=UTC),
            )
        ],
        action_summary=CorrectiveActionSummary(total_actions=1, in_progress_actions=1),
        readiness_summary=[],
        risk_summary=[],
        overdue_summary=[],
    )

    app.dependency_overrides[get_current_tenant] = lambda: {"id": 1, "name": "Tenant-1"}
    response = client.get(BASE, headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == 1
    assert body["runtime_registry"] == "CORRECTIVE_ACTION_RUNTIME"
    assert body["read_only"] is True
    assert body["aggregator_only"] is True
    assert body["corrective_actions"][0]["action_id"] == "ACT-1"


@patch("app.modules.quality_accreditation.quality_accreditation_corrective_action_service.repository.list_resources")
def test_corrective_action_service_is_tenant_scoped(mock_list_resources) -> None:
    rows_by_tenant = {tenant_id: _build_rows(tenant_id) for tenant_id in (6, 14)}

    def _list_resources(_db, model, tenant_id):
        return rows_by_tenant[tenant_id][model]

    mock_list_resources.side_effect = _list_resources
    service = CorrectiveActionRuntimeService()
    session = MagicMock(spec=Session)

    tenant6 = service.get_corrective_action_runtime(session, 6).model_dump(mode="json")
    tenant14 = service.get_corrective_action_runtime(session, 14).model_dump(mode="json")

    assert tenant6["tenant_id"] == 6
    assert tenant14["tenant_id"] == 14
    assert tenant6["corrective_actions"]
    assert tenant14["corrective_actions"]
    assert tenant6["corrective_actions"][0]["action_id"] != tenant14["corrective_actions"][0]["action_id"]


@patch("app.modules.quality_accreditation.corrective_action_runtime_router.corrective_action_runtime_service.get_corrective_action_runtime")
def test_corrective_action_runtime_is_read_only(mock_service) -> None:
    mock_service.return_value = CorrectiveActionRuntimeResponse(
        tenant_id=1,
        generated_at=datetime(2026, 6, 11, tzinfo=UTC),
        corrective_actions=[],
        action_summary=CorrectiveActionSummary(),
        readiness_summary=[],
        risk_summary=[],
        overdue_summary=[],
    )

    headers = _headers()
    assert client.post(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.put(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.patch(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert client.delete(BASE, headers=headers).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
