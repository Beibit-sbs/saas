"""A-017.2 — Research ethics router contract coverage.

Closes the remaining maturity gap by pinning the existing admin contract used by
the frontend page. No new backend feature surface is introduced here.
"""

from __future__ import annotations

import pytest

from app.modules.tenants import service as tenant_service
from tests.conftest import ADMIN_HEADERS, _auth_headers, client


def test_a017_2_research_ethics_list_contract_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.research_ethics.service.list_ethics_reviews",
        lambda tenant_id, status=None, risk_level=None: [
            {
                "id": 11,
                "tenant_id": tenant_id,
                "review_code": "IRB-011",
                "project_title": "Human Subjects Retention Study",
                "principal_investigator_id": "FAC-011",
                "review_type": "irb",
                "status": "under_review",
                "submission_date": "2026-05-01",
                "decision_date": None,
                "risk_level": "high",
                "notes": None,
                "integration_source": None,
                "committee_name": "Central IRB",
            }
        ],
    )

    response = client.get("/api/admin/research-ethics/reviews", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()
    assert "records" in body
    assert len(body["records"]) == 1
    record = body["records"][0]
    assert record["id"] == 11
    assert record["tenant_id"] == 1
    assert record["review_code"] == "IRB-011"
    assert record["project_title"] == "Human Subjects Retention Study"
    assert record["principal_investigator_id"] == "FAC-011"
    assert record["review_type"] == "irb"
    assert record["status"] == "under_review"
    assert record["risk_level"] == "high"
    assert record["committee_name"] == "Central IRB"


def test_a017_2_research_ethics_brain_context_contract_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.research_ethics.service.get_research_ethics_brain_context",
        lambda tenant_id: {
            "module": "research_ethics",
            "tenant_id": tenant_id,
            "total_reviews": 7,
            "pending_reviews": 2,
            "approved_reviews": 3,
            "rejected_reviews": 1,
            "high_risk_reviews": 1,
            "compliance_status": "under_review",
        },
    )

    response = client.get("/api/admin/research-ethics/brain-context", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {
        "module": "research_ethics",
        "tenant_id": 1,
        "total_reviews": 7,
        "pending_reviews": 2,
        "approved_reviews": 3,
        "rejected_reviews": 1,
        "high_risk_reviews": 1,
        "compliance_status": "under_review",
    }


def test_a017_2_research_ethics_list_is_tenant_scoped(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _list(tenant_id: int, status: str | None = None, risk_level: str | None = None):
        captured["tenant_id"] = tenant_id
        captured["status"] = status
        captured["risk_level"] = risk_level
        return []

    monkeypatch.setattr("app.modules.research_ethics.service.list_ethics_reviews", _list)

    tenant = tenant_service.create_tenant({"slug": "a0172-research-ethics", "name": "A0172 Research Ethics"})
    tenant_id = int(tenant["id"])
    headers = _auth_headers("tenant.a0172.admin@example.com", ["admin"], tenant_id=tenant_id)
    response = client.get(
        "/api/admin/research-ethics/reviews?status=pending&risk_level=high",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert captured == {"tenant_id": tenant_id, "status": "pending", "risk_level": "high"}


def test_a017_2_research_ethics_list_requires_auth() -> None:
    response = client.get("/api/admin/research-ethics/reviews")
    assert response.status_code in (401, 403)


def test_a017_2_research_ethics_list_forbidden_without_research_permission() -> None:
    viewer_headers = _auth_headers("student.research@example.com", ["student"], tenant_id=1)
    response = client.get("/api/admin/research-ethics/reviews", headers=viewer_headers)
    assert response.status_code == 403


def test_a017_2_research_ethics_create_invalid_payload_returns_validation_error() -> None:
    response = client.post(
        "/api/admin/research-ethics/reviews",
        headers=ADMIN_HEADERS,
        json={
            "project_title": "Missing code payload",
            "principal_investigator_id": "FAC-001",
        },
    )
    assert response.status_code == 422, response.text
    body = response.json()
    assert "detail" in body


def test_a017_2_research_ethics_create_serializes_when_optional_fields_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.research_ethics.service.create_ethics_review",
        lambda payload, tenant_id, actor="system": {
            "id": 77,
            "tenant_id": tenant_id,
            "review_code": payload["review_code"],
            "project_title": payload["project_title"],
            "principal_investigator_id": payload["principal_investigator_id"],
            "review_type": payload.get("review_type", "irb"),
            "status": payload.get("status", "pending"),
            "risk_level": payload.get("risk_level", "minimal"),
        },
    )

    response = client.post(
        "/api/admin/research-ethics/reviews",
        headers=ADMIN_HEADERS,
        json={
            "review_code": "IRB-077",
            "project_title": "Optional Field Tolerance",
            "principal_investigator_id": "FAC-077",
        },
    )
    assert response.status_code == 201, response.text
    record = response.json()["record"]
    assert record["review_code"] == "IRB-077"
    assert record["committee_name"] is None
    assert record["notes"] is None
    assert record["integration_source"] is None
    assert record["decision_date"] is None


def test_a017_2_research_ethics_contract_path_preserves_human_review(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.research_ethics.service.create_ethics_review",
        lambda payload, tenant_id, actor="system": {
            "id": 88,
            "tenant_id": tenant_id,
            "review_code": payload["review_code"],
            "project_title": payload["project_title"],
            "principal_investigator_id": payload["principal_investigator_id"],
            "review_type": payload.get("review_type", "irb"),
            "status": "pending",
            "risk_level": payload.get("risk_level", "minimal"),
            "notes": None,
            "integration_source": None,
            "committee_name": None,
            "submission_date": None,
            "decision_date": None,
        },
    )

    response = client.post(
        "/api/admin/research-ethics/reviews",
        headers=ADMIN_HEADERS,
        json={
            "review_code": "IRB-088",
            "project_title": "Human Review Preserved",
            "principal_investigator_id": "FAC-088",
            "risk_level": "high",
        },
    )
    assert response.status_code == 201, response.text
    record = response.json()["record"]
    assert record["status"] == "pending"
    assert "auto_approved" not in record
    assert "auto_rejected" not in record
    assert "sanctioned" not in record
    assert "recommended_actions" not in record
