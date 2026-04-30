"""W35 domain-depth tests — exam_governance: active exam_type cap + proctoring risk alert side effect."""
from __future__ import annotations

import importlib
import types


def _load_service() -> types.ModuleType:
    return importlib.import_module("app.modules.exam_governance.service")


def test_w35_source_contains_cap_dict_and_alert_helper() -> None:
    import inspect

    svc = _load_service()
    src = inspect.getsource(svc)
    assert "_EXAM_TYPE_MAX_ACTIVE" in src
    assert "_ACTIVE_EXAM_STATUSES" in src
    assert "_HIGH_RISK_PROCTORING_MODES" in src
    assert "_ensure_proctoring_alert_record" in src


def test_w35_create_exam_raises_when_type_cap_reached(monkeypatch) -> None:
    import pytest

    svc = _load_service()

    from app.modules.exam_governance.schemas import ExamCreateSchema

    cap = svc._EXAM_TYPE_MAX_ACTIVE["practical"]
    fake_rows = [{"exam_type": "practical", "status": "scheduled"} for _ in range(cap)]

    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda name, tid: fake_rows)

    with pytest.raises(ValueError, match="exam_type 'practical'"):
        svc.create_exam(
            tenant_id=1,
            payload=ExamCreateSchema(
                course_code="CS-101",
                course_title="Intro to CS",
                faculty_id="FAC-1",
                exam_type="practical",
                term_id="TERM-2026",
                status="scheduled",
                proctoring_mode="in_person",
            ),
            actor="test-actor",
        )


def test_w35_create_exam_succeeds_below_cap(monkeypatch) -> None:
    svc = _load_service()

    from app.modules.exam_governance.schemas import ExamCreateSchema

    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda name, tid: [])

    created_entities: list[tuple[str, dict]] = []

    def fake_create(entity_name, payload, tid):
        record = {**payload, "id": len(created_entities) + 1, "tenant_id": str(tid)}
        created_entities.append((entity_name, record))
        return record

    def fake_audit(*args, **kwargs) -> None:
        pass

    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)
    monkeypatch.setattr(svc, "log_admin_action", fake_audit)

    result = svc.create_exam(
        tenant_id=5,
        payload=ExamCreateSchema(
            course_code="BIO-201",
            course_title="Cell Biology",
            faculty_id="FAC-22",
            exam_type="midterm",
            term_id="TERM-2026",
            status="scheduled",
            proctoring_mode="in_person",
            location_room="Hall-A",
        ),
        actor="admin",
    )

    assert result.course_code == "BIO-201"
    assert len(created_entities) == 1
    assert created_entities[0][0] == "exams"


def test_w35_proctoring_alert_side_effect_on_remote_exam(monkeypatch) -> None:
    svc = _load_service()

    from app.modules.exam_governance.schemas import ExamCreateSchema

    created_entities: list[tuple[str, dict]] = []

    def fake_list(entity_name, tid):
        return []

    def fake_create(entity_name, payload, tid):
        record = {**payload, "id": len(created_entities) + 1, "tenant_id": str(tid)}
        created_entities.append((entity_name, record))
        return record

    def fake_audit(*args, **kwargs) -> None:
        pass

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)
    monkeypatch.setattr(svc, "log_admin_action", fake_audit)

    svc.create_exam(
        tenant_id=7,
        payload=ExamCreateSchema(
            course_code="LAW-401",
            course_title="Advanced Contract Law",
            faculty_id="FAC-88",
            exam_type="final",
            term_id="TERM-2026",
            status="scheduled",
            proctoring_mode="remote",
        ),
        actor="admin",
    )

    entity_names = [name for name, _ in created_entities]
    assert "exams" in entity_names
    assert "exam_proctoring_alerts" in entity_names
    alert = next(r for name, r in created_entities if name == "exam_proctoring_alerts")
    assert alert["integration_source"] == "exam_proctoring_risk"
    assert alert["proctoring_mode"] == "remote"
