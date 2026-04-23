"""Phase VII-VII1: Research ethics module tests."""
from __future__ import annotations

import pytest

from app.modules.research_ethics import service as ethics_service
from tests.conftest import ADMIN_HEADERS, client as test_client


def test_list_ethics_reviews_empty(monkeypatch) -> None:
    monkeypatch.setattr(ethics_service, "list_entities_for_tenant", lambda name, tid: [])
    assert ethics_service.list_ethics_reviews(tenant_id=1) == []


def test_list_ethics_reviews_filter_by_status(monkeypatch) -> None:
    rows = [
        {
            "id": 1,
            "review_code": "IRB-001",
            "project_title": "Genome Study",
            "principal_investigator_id": "PI-1",
            "review_type": "irb",
            "status": "pending",
            "risk_level": "minimal",
            "tenant_id": 1,
        },
        {
            "id": 2,
            "review_code": "IRB-002",
            "project_title": "Survey Research",
            "principal_investigator_id": "PI-2",
            "review_type": "irb",
            "status": "approved",
            "risk_level": "minimal",
            "tenant_id": 1,
        },
    ]
    monkeypatch.setattr(ethics_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = ethics_service.list_ethics_reviews(tenant_id=1, status="pending")
    assert len(result) == 1
    assert result[0]["review_code"] == "IRB-001"


def test_list_ethics_reviews_filter_by_risk(monkeypatch) -> None:
    rows = [
        {
            "id": 1,
            "review_code": "IRB-003",
            "project_title": "Clinical Trial",
            "principal_investigator_id": "PI-3",
            "review_type": "irb",
            "status": "pending",
            "risk_level": "high",
            "tenant_id": 2,
        },
        {
            "id": 2,
            "review_code": "IRB-004",
            "project_title": "Observation Study",
            "principal_investigator_id": "PI-4",
            "review_type": "irb",
            "status": "approved",
            "risk_level": "minimal",
            "tenant_id": 2,
        },
    ]
    monkeypatch.setattr(ethics_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = ethics_service.list_ethics_reviews(tenant_id=2, risk_level="high")
    assert len(result) == 1
    assert result[0]["review_code"] == "IRB-003"


def test_get_research_ethics_brain_context_at_risk(monkeypatch) -> None:
    rows = [
        {"id": 1, "review_code": "IRB-1", "status": "pending", "risk_level": "high", "tenant_id": 3},
        {"id": 2, "review_code": "IRB-2", "status": "rejected", "risk_level": "minimal", "tenant_id": 3},
        {"id": 3, "review_code": "IRB-3", "status": "approved", "risk_level": "minimal", "tenant_id": 3},
    ]
    monkeypatch.setattr(ethics_service, "list_entities_for_tenant", lambda name, tid: rows)
    ctx = ethics_service.get_research_ethics_brain_context(tenant_id=3)
    assert ctx["total_reviews"] == 3
    assert ctx["pending_reviews"] == 1
    assert ctx["rejected_reviews"] == 1
    assert ctx["high_risk_reviews"] == 1
    assert ctx["compliance_status"] == "at_risk"


def test_get_research_ethics_brain_context_empty(monkeypatch) -> None:
    monkeypatch.setattr(ethics_service, "list_entities_for_tenant", lambda name, tid: [])
    ctx = ethics_service.get_research_ethics_brain_context(tenant_id=1)
    assert ctx["total_reviews"] == 0
    assert ctx["compliance_status"] == "compliant"


def test_http_list_ethics_reviews_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.research_ethics.router.list_ethics_reviews",
        lambda tenant_id, status=None, risk_level=None: [],
    )
    resp = test_client.get("/api/admin/research-ethics/reviews", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    assert resp.json()["records"] == []


def test_http_create_ethics_review(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {
        "id": 10,
        "review_code": "IRB-010",
        "project_title": "Data Privacy Study",
        "principal_investigator_id": "PI-10",
        "review_type": "irb",
        "status": "pending",
        "submission_date": None,
        "decision_date": None,
        "risk_level": "minimal",
        "notes": None,
        "integration_source": None,
        "tenant_id": 1,
    }
    monkeypatch.setattr(
        "app.modules.research_ethics.router.create_ethics_review",
        lambda payload, tenant_id: created,
    )
    resp = test_client.post(
        "/api/admin/research-ethics/reviews",
        json={
            "review_code": "IRB-010",
            "project_title": "Data Privacy Study",
            "principal_investigator_id": "PI-10",
            "review_type": "irb",
            "status": "pending",
        },
        headers=dict(ADMIN_HEADERS),
    )
    assert resp.status_code == 201
    assert resp.json()["record"]["id"] == 10


def test_http_brain_context_ethics(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = {
        "module": "research_ethics",
        "tenant_id": 1,
        "total_reviews": 4,
        "pending_reviews": 1,
        "approved_reviews": 2,
        "rejected_reviews": 1,
        "high_risk_reviews": 0,
        "compliance_status": "at_risk",
    }
    monkeypatch.setattr(
        "app.modules.research_ethics.router.get_research_ethics_brain_context",
        lambda tenant_id: ctx,
    )
    resp = test_client.get("/api/admin/research-ethics/brain-context", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    body = resp.json()
    assert body["module"] == "research_ethics"
    assert body["compliance_status"] == "at_risk"
