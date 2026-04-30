"""W36 domain-depth tests — syllabus_governance: active syllabus dept cap + review backlog side effect."""
from __future__ import annotations

import importlib
import types


def _load_service() -> types.ModuleType:
    return importlib.import_module("app.modules.syllabus_governance.service")


def test_w36_source_contains_cap_dict_and_backlog_helper() -> None:
    import inspect

    svc = _load_service()
    src = inspect.getsource(svc)
    assert "_DEPT_MAX_ACTIVE_SYLLABI" in src
    assert "_ACTIVE_SYLLABUS_STATUSES" in src
    assert "_HIGH_WORKLOAD_STATUSES" in src
    assert "_ensure_review_backlog_record" in src


def test_w36_create_syllabus_raises_when_dept_cap_reached(monkeypatch) -> None:
    import pytest

    svc = _load_service()
    monkeypatch.setattr(svc, "_check_faculty_has_active_contract_for_syllabus", lambda *a, **kw: None)

    from app.modules.syllabus_governance.schemas import SyllabusCreateSchema

    cap = svc._DEPT_MAX_ACTIVE_SYLLABI["medicine"]
    fake_rows = [{"department_id": "medicine", "status": "draft"} for _ in range(cap)]

    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda name, tid: fake_rows)

    with pytest.raises(ValueError, match="department 'medicine'"):
        svc.create_syllabus(
            tenant_id=1,
            payload=SyllabusCreateSchema(
                course_code="MED-501",
                course_title="Clinical Methods",
                department_id="medicine",
                faculty_id="FAC-10",
                term_id="TERM-2026",
                status="draft",
            ),
            actor="test-actor",
        )


def test_w36_create_syllabus_succeeds_below_cap(monkeypatch) -> None:
    svc = _load_service()
    monkeypatch.setattr(svc, "_check_faculty_has_active_contract_for_syllabus", lambda *a, **kw: None)

    from app.modules.syllabus_governance.schemas import SyllabusCreateSchema

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

    result = svc.create_syllabus(
        tenant_id=3,
        payload=SyllabusCreateSchema(
            course_code="CS-301",
            course_title="Algorithms",
            department_id="cs",
            faculty_id="FAC-5",
            term_id="TERM-2026",
            status="draft",
            credit_hours=4,
        ),
        actor="admin",
    )

    assert result.course_code == "CS-301"
    assert len(created_entities) == 1
    assert created_entities[0][0] == "syllabi"


def test_w36_review_backlog_side_effect_on_under_review_syllabus(monkeypatch) -> None:
    svc = _load_service()
    monkeypatch.setattr(svc, "_check_faculty_has_active_contract_for_syllabus", lambda *a, **kw: None)

    from app.modules.syllabus_governance.schemas import SyllabusCreateSchema

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

    svc.create_syllabus(
        tenant_id=9,
        payload=SyllabusCreateSchema(
            course_code="LAW-201",
            course_title="Constitutional Law",
            department_id="law",
            faculty_id="FAC-33",
            term_id="TERM-2026",
            status="under_review",
        ),
        actor="admin",
    )

    entity_names = [name for name, _ in created_entities]
    assert "syllabi" in entity_names
    assert "syllabus_review_backlogs" in entity_names
    backlog = next(r for name, r in created_entities if name == "syllabus_review_backlogs")
    assert backlog["integration_source"] == "syllabus_review_queue"
    assert backlog["course_code"] == "LAW-201"
