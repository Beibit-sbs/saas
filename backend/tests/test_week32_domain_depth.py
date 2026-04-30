"""W32 domain-depth tests — student_life: counseling case concern_type cap + alert record side effect."""
from __future__ import annotations

import importlib
import types


def _load_service() -> types.ModuleType:
    return importlib.import_module("app.modules.student_life.service")


# ---------------------------------------------------------------------------
# W32.1 — cap dict and side-effect helper present in source
# ---------------------------------------------------------------------------
def test_w32_source_contains_cap_dict_and_alert_helper() -> None:
    import inspect
    svc = _load_service()
    src = inspect.getsource(svc)
    assert "_CONCERN_TYPE_MAX_ACTIVE_CASES" in src
    assert "_ACTIVE_COUNSELING_STATUSES" in src
    assert "_ensure_student_alert_record" in src
    assert "_SERIOUS_CONCERN_TYPES" in src


# ---------------------------------------------------------------------------
# W32.2 — cap guard raises ValueError when active count >= cap
# ---------------------------------------------------------------------------
def test_w32_create_raises_when_counseling_cap_reached(monkeypatch) -> None:
    svc = _load_service()

    cap = svc._CONCERN_TYPE_MAX_ACTIVE_CASES["mental_health"]

    fake_cases = [
        {"concern_type": "mental_health", "status": "open"}
        for _ in range(cap)
    ]
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda name, tid: fake_cases)

    from app.modules.student_life.schemas import CounselingCaseCreateSchema
    import pytest

    with pytest.raises(ValueError, match="mental_health"):
        svc.create_counseling_case(
            tenant_id=1,
            request=CounselingCaseCreateSchema(
                case_code="CC-999",
                student_id="S001",
                concern_type="mental_health",
                status="open",
            ),
            actor="test_actor",
        )


# ---------------------------------------------------------------------------
# W32.3 — case below cap is created without error
# ---------------------------------------------------------------------------
def test_w32_create_succeeds_below_cap(monkeypatch) -> None:
    svc = _load_service()

    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda name, tid: [])
    created: list[dict] = []

    def fake_create(entity_name, payload, tid):
        record = {**payload, "id": len(created) + 1, "tenant_id": str(tid)}
        created.append(record)
        return record

    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)
    monkeypatch.setattr(svc, "log_admin_action", lambda **kwargs: None)

    from app.modules.student_life.schemas import CounselingCaseCreateSchema

    result = svc.create_counseling_case(
        tenant_id=3,
        request=CounselingCaseCreateSchema(
            case_code="CC-001",
            student_id="S042",
            concern_type="academic",
            status="open",
        ),
        actor="admin",
    )
    assert result.case_code == "CC-001"
    assert len(created) == 1
    assert created[0]["case_code"] == "CC-001"
    assert created[0]["concern_type"] == "academic"


# ---------------------------------------------------------------------------
# W32.4 — alert record side effect fires for serious concern types
# ---------------------------------------------------------------------------
def test_w32_alert_record_side_effect_on_serious_concern(monkeypatch) -> None:
    svc = _load_service()

    created_entities: list[tuple[str, dict]] = []

    def fake_list(entity_name, tid):
        return []

    def fake_create(entity_name, payload, tid):
        record = {**payload, "id": len(created_entities) + 1, "tenant_id": str(tid)}
        created_entities.append((entity_name, record))
        return record

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)
    monkeypatch.setattr(svc, "log_admin_action", lambda **kwargs: None)

    from app.modules.student_life.schemas import CounselingCaseCreateSchema

    svc.create_counseling_case(
        tenant_id=7,
        request=CounselingCaseCreateSchema(
            case_code="CC-SER-01",
            student_id="S099",
            concern_type="harassment",
            status="open",
        ),
        actor="admin",
    )

    entity_names = [name for name, _ in created_entities]
    assert "student_life_counseling_cases" in entity_names
    assert "student_life_alert_records" in entity_names
    alert = next(r for name, r in created_entities if name == "student_life_alert_records")
    assert alert["integration_source"] == "counseling_serious_concern"
    assert alert["concern_type"] == "harassment"
