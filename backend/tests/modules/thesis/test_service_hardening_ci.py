"""Phase CI - Thesis Service Hardening (canonical 10-step hooks).

Verifies:
1. create_thesis_record emits canonical status event and records metric.
2. update_thesis_status emits canonical status event and records metric.
3. create_thesis_record survives outcome failure and still records metric.
4. create_thesis_record enforces active-cap guard fail-closed.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.thesis.schemas import ThesisCreateSchema, ThesisStatusUpdateSchema
from app.modules.thesis import service as svc


def _make_thesis(*, thesis_id: int = 1, status: str = "draft") -> dict[str, object]:
    return {
        "id": thesis_id,
        "tenant_id": "1",
        "thesis_code": "TH-001",
        "student_id": 101,
        "title": "Knowledge Graph Research",
        "advisor_faculty_id": "FAC-1",
        "status": status,
        "defense_date": None,
        "repository_url": None,
    }


def test_create_thesis_record_emits_event_and_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda *a, **k: [])
    monkeypatch.setattr(svc, "create_entity_for_tenant", lambda *a, **k: _make_thesis(thesis_id=7, status="draft"))
    monkeypatch.setattr(svc, "_emit_audit", MagicMock())
    monkeypatch.setattr(svc, "_record_outcome", MagicMock())

    emitted: list[dict[str, object]] = []

    def _emit_domain_event(**kwargs: object) -> None:
        emitted.append(dict(kwargs))

    monkeypatch.setattr(svc, "_emit_domain_event", _emit_domain_event)

    metrics: list[tuple[int, str, int]] = []
    monkeypatch.setattr(svc, "_metric", lambda tenant_id, metric, value=1: metrics.append((tenant_id, metric, value)))

    result = svc.create_thesis_record(
        1,
        ThesisCreateSchema(thesis_code="TH-001", student_id=101, title="Knowledge Graph Research"),
        actor="admin@test",
    )

    assert result.id == 7
    assert len(emitted) == 1
    assert emitted[0]["to_status"] == "draft"
    assert (1, "thesis_records_created", 1) in metrics


def test_update_thesis_status_emits_event_and_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    current = _make_thesis(thesis_id=11, status="submitted")
    updated = _make_thesis(thesis_id=11, status="rejected")

    def _list(entity_name: str, tenant_id: int) -> list[dict[str, object]]:
        if entity_name == "thesis_records":
            return [current]
        if entity_name in {"thesis_rejection_risk_alerts", "thesis_overdue_alerts", "integrity_case"}:
            return []
        return []

    monkeypatch.setattr(svc, "list_entities_for_tenant", _list)
    monkeypatch.setattr(svc, "update_entity_for_tenant", lambda *a, **k: updated)
    monkeypatch.setattr(svc, "_emit_audit", MagicMock())
    monkeypatch.setattr(svc, "_record_outcome", MagicMock())
    monkeypatch.setattr(svc, "_ensure_rejection_risk_alert", MagicMock())

    emitted: list[dict[str, object]] = []

    def _emit_domain_event(**kwargs: object) -> None:
        emitted.append(dict(kwargs))

    monkeypatch.setattr(svc, "_emit_domain_event", _emit_domain_event)

    metrics: list[tuple[int, str, int]] = []
    monkeypatch.setattr(svc, "_metric", lambda tenant_id, metric, value=1: metrics.append((tenant_id, metric, value)))

    result = svc.update_thesis_status(
        tenant_id=1,
        thesis_id=11,
        request=ThesisStatusUpdateSchema(status="rejected"),
        actor="admin@test",
    )

    assert result.status == "rejected"
    assert len(emitted) == 1
    assert emitted[0]["from_status"] == "submitted"
    assert emitted[0]["to_status"] == "rejected"
    assert (1, "thesis_status_updates", 1) in metrics


def test_create_thesis_record_survives_outcome_failure_and_records_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda *a, **k: [])
    monkeypatch.setattr(svc, "create_entity_for_tenant", lambda *a, **k: _make_thesis(thesis_id=9, status="draft"))
    monkeypatch.setattr(svc, "_emit_audit", MagicMock())
    monkeypatch.setattr(svc, "_emit_domain_event", MagicMock())

    metrics: list[tuple[int, str, int]] = []
    monkeypatch.setattr(svc, "_metric", lambda tenant_id, metric, value=1: metrics.append((tenant_id, metric, value)))

    mock_brain = MagicMock()
    mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")

    with patch("app.modules.brain_core.service.brain_core_service", mock_brain):
        result = svc.create_thesis_record(
            1,
            ThesisCreateSchema(thesis_code="TH-009", student_id=109, title="Graph Safety"),
            actor="admin@test",
        )

    assert result.id == 9
    assert (1, "thesis_records_created", 1) in metrics


def test_create_thesis_record_cap_guard_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    cap = svc._THESIS_STATUS_MAX_ACTIVE.get("draft", 200)
    existing = [{"id": i, "thesis_code": f"TH-{i}", "status": "draft"} for i in range(cap)]

    monkeypatch.setattr(
        svc,
        "list_entities_for_tenant",
        lambda entity_name, tenant_id: existing if entity_name == "thesis_records" else [],
    )

    with pytest.raises(ValueError, match="cap"):
        svc.create_thesis_record(
            1,
            ThesisCreateSchema(thesis_code="TH-OVER", student_id=1000, title="Cap Test"),
            actor="admin@test",
        )
