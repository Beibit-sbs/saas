"""W92 — thesis: defense finalization requires academic integrity clearance."""
from __future__ import annotations

import datetime as dt

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.thesis.schemas import ThesisStatusUpdateSchema
from app.modules.thesis.service import update_thesis_status



def _make_thesis(*, student_id: int | None = 501, status: str = "approved") -> dict:
    return {
        "id": 10,
        "tenant_id": "1",
        "thesis_code": "TH-501",
        "student_id": student_id,
        "title": "Neural Curriculum Optimization",
        "advisor_faculty_id": "FAC-10",
        "status": status,
        "defense_date": None,
        "repository_url": None,
    }



def test_w92_guard_exists_and_constants_present():
    from app.modules.thesis.service import (
        _BLOCKING_INTEGRITY_CASE_STATUSES,
        _DEFENSE_TRANSITION_STATUSES,
        _check_no_open_integrity_cases_for_defense,
    )

    assert callable(_check_no_open_integrity_cases_for_defense)
    assert _DEFENSE_TRANSITION_STATUSES == frozenset({"defended"})
    assert "flagged" in _BLOCKING_INTEGRITY_CASE_STATUSES
    assert "under_review" in _BLOCKING_INTEGRITY_CASE_STATUSES
    assert "escalated" in _BLOCKING_INTEGRITY_CASE_STATUSES



def test_w92_blocked_when_student_id_missing(monkeypatch):
    thesis = _make_thesis(student_id=None)

    def _list(entity_name, _tenant_id):
        if entity_name == "thesis_records":
            return [thesis]
        return []

    monkeypatch.setattr("app.modules.thesis.service.list_entities_for_tenant", _list)

    with pytest.raises(DomainValidationError, match="missing or invalid student_id"):
        update_thesis_status(
            tenant_id=1,
            thesis_id=10,
            request=ThesisStatusUpdateSchema(status="defended", defense_date=dt.date(2026, 5, 1)),
            actor="test",
        )



def test_w92_blocked_when_integrity_lookup_fails(monkeypatch):
    thesis = _make_thesis(student_id=501)

    def _list(entity_name, _tenant_id):
        if entity_name == "thesis_records":
            return [thesis]
        if entity_name == "integrity_case":
            raise RuntimeError("integrity service unavailable")
        return []

    monkeypatch.setattr("app.modules.thesis.service.list_entities_for_tenant", _list)

    with pytest.raises(DomainValidationError, match="academic_integrity lookup failed"):
        update_thesis_status(
            tenant_id=1,
            thesis_id=10,
            request=ThesisStatusUpdateSchema(status="defended", defense_date=dt.date(2026, 5, 1)),
            actor="test",
        )



def test_w92_blocked_when_student_has_flagged_case(monkeypatch):
    thesis = _make_thesis(student_id=501)

    def _list(entity_name, _tenant_id):
        if entity_name == "thesis_records":
            return [thesis]
        if entity_name == "integrity_case":
            return [{"id": "IC-1", "student_id": 501, "status": "flagged"}]
        return []

    monkeypatch.setattr("app.modules.thesis.service.list_entities_for_tenant", _list)

    with pytest.raises(DomainValidationError, match="open academic integrity cases"):
        update_thesis_status(
            tenant_id=1,
            thesis_id=10,
            request=ThesisStatusUpdateSchema(status="defended", defense_date=dt.date(2026, 5, 1)),
            actor="test",
        )



def test_w92_blocked_when_student_has_under_review_case(monkeypatch):
    thesis = _make_thesis(student_id=501)

    def _list(entity_name, _tenant_id):
        if entity_name == "thesis_records":
            return [thesis]
        if entity_name == "integrity_case":
            return [{"id": "IC-2", "student_id": 501, "status": "under_review"}]
        return []

    monkeypatch.setattr("app.modules.thesis.service.list_entities_for_tenant", _list)

    with pytest.raises(DomainValidationError, match="open academic integrity cases"):
        update_thesis_status(
            tenant_id=1,
            thesis_id=10,
            request=ThesisStatusUpdateSchema(status="defended", defense_date=dt.date(2026, 5, 1)),
            actor="test",
        )



def test_w92_defended_allowed_when_only_resolved_or_dismissed_cases(monkeypatch):
    thesis = _make_thesis(student_id=501)
    updated_thesis = {**thesis, "status": "defended", "defense_date": "2026-05-01"}

    def _list(entity_name, _tenant_id):
        if entity_name == "thesis_records":
            return [thesis]
        if entity_name == "integrity_case":
            return [
                {"id": "IC-3", "student_id": 501, "status": "resolved"},
                {"id": "IC-4", "student_id": 501, "status": "dismissed"},
            ]
        return []

    monkeypatch.setattr("app.modules.thesis.service.list_entities_for_tenant", _list)
    monkeypatch.setattr("app.modules.thesis.service.update_entity_for_tenant", lambda *a, **k: updated_thesis)
    monkeypatch.setattr("app.modules.thesis.service.log_admin_action", lambda **kw: None)
    monkeypatch.setattr("app.modules.thesis.service._emit_domain_event", lambda **kw: None)

    result = update_thesis_status(
        tenant_id=1,
        thesis_id=10,
        request=ThesisStatusUpdateSchema(status="defended", defense_date=dt.date(2026, 5, 1)),
        actor="test",
    )

    assert result.status == "defended"



def test_w92_non_defended_transition_skips_integrity_lookup(monkeypatch):
    thesis = _make_thesis(student_id=501, status="draft")
    updated_thesis = {**thesis, "status": "submitted"}
    calls: list[str] = []

    def _list(entity_name, _tenant_id):
        calls.append(entity_name)
        if entity_name == "thesis_records":
            return [thesis]
        if entity_name == "integrity_case":
            raise AssertionError("integrity lookup should not run for non-defended transition")
        return []

    monkeypatch.setattr("app.modules.thesis.service.list_entities_for_tenant", _list)
    monkeypatch.setattr("app.modules.thesis.service.update_entity_for_tenant", lambda *a, **k: updated_thesis)
    monkeypatch.setattr("app.modules.thesis.service.log_admin_action", lambda **kw: None)
    monkeypatch.setattr("app.modules.thesis.service._emit_domain_event", lambda **kw: None)

    result = update_thesis_status(
        tenant_id=1,
        thesis_id=10,
        request=ThesisStatusUpdateSchema(status="submitted"),
        actor="test",
    )

    assert result.status == "submitted"
    assert "integrity_case" not in calls



def test_w92_open_case_for_other_student_does_not_block(monkeypatch):
    thesis = _make_thesis(student_id=501)
    updated_thesis = {**thesis, "status": "defended", "defense_date": "2026-05-01"}

    def _list(entity_name, _tenant_id):
        if entity_name == "thesis_records":
            return [thesis]
        if entity_name == "integrity_case":
            return [{"id": "IC-9", "student_id": 999, "status": "flagged"}]
        return []

    monkeypatch.setattr("app.modules.thesis.service.list_entities_for_tenant", _list)
    monkeypatch.setattr("app.modules.thesis.service.update_entity_for_tenant", lambda *a, **k: updated_thesis)
    monkeypatch.setattr("app.modules.thesis.service.log_admin_action", lambda **kw: None)
    monkeypatch.setattr("app.modules.thesis.service._emit_domain_event", lambda **kw: None)

    result = update_thesis_status(
        tenant_id=1,
        thesis_id=10,
        request=ThesisStatusUpdateSchema(status="defended", defense_date=dt.date(2026, 5, 1)),
        actor="test",
    )

    assert result.status == "defended"



def test_w92_error_contains_blocking_case_id(monkeypatch):
    thesis = _make_thesis(student_id=501)

    def _list(entity_name, _tenant_id):
        if entity_name == "thesis_records":
            return [thesis]
        if entity_name == "integrity_case":
            return [{"id": "IC-77", "student_id": 501, "status": "escalated"}]
        return []

    monkeypatch.setattr("app.modules.thesis.service.list_entities_for_tenant", _list)

    with pytest.raises(DomainValidationError) as exc_info:
        update_thesis_status(
            tenant_id=1,
            thesis_id=10,
            request=ThesisStatusUpdateSchema(status="defended", defense_date=dt.date(2026, 5, 1)),
            actor="test",
        )

    assert "IC-77" in str(exc_info.value)
