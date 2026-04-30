"""W33 domain-depth tests — research_ethics: active review_type cap + high-risk alert side effect."""
from __future__ import annotations

import importlib
import types


def _load_service() -> types.ModuleType:
    return importlib.import_module("app.modules.research_ethics.service")


def test_w33_source_contains_cap_dict_and_alert_helper() -> None:
    import inspect

    svc = _load_service()
    src = inspect.getsource(svc)
    assert "_REVIEW_TYPE_MAX_ACTIVE_REVIEWS" in src
    assert "_ACTIVE_REVIEW_STATUSES" in src
    assert "_HIGH_RISK_LEVELS" in src
    assert "_ensure_ethics_alert_record" in src


def test_w33_create_raises_when_review_type_cap_reached(monkeypatch) -> None:
    svc = _load_service()
    monkeypatch.setattr(svc, "_check_pi_has_active_contract_for_ethics_review", lambda *a, **kw: None)

    cap = svc._REVIEW_TYPE_MAX_ACTIVE_REVIEWS["irb"]
    fake_rows = [{"review_type": "irb", "status": "pending"} for _ in range(cap)]

    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda name, tid: fake_rows)

    import pytest

    with pytest.raises(ValueError, match="review_type 'irb'"):
        svc.create_ethics_review(
            {
                "review_code": "RE-999",
                "project_title": "Test Review",
                "principal_investigator_id": "PI-1",
                "review_type": "irb",
                "status": "pending",
                "risk_level": "minimal",
            },
            tenant_id=1,
        )


def test_w33_create_succeeds_below_cap(monkeypatch) -> None:
    svc = _load_service()
    monkeypatch.setattr(svc, "_check_pi_has_active_contract_for_ethics_review", lambda *a, **kw: None)

    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda name, tid: [])

    created_entities: list[tuple[str, dict]] = []

    def fake_create(entity_name, payload, tid):
        record = {**payload, "id": len(created_entities) + 1, "tenant_id": tid}
        created_entities.append((entity_name, record))
        return record

    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    result = svc.create_ethics_review(
        {
            "review_code": "RE-001",
            "project_title": "Low Risk Study",
            "principal_investigator_id": "PI-11",
            "review_type": "data_privacy",
            "status": "pending",
            "risk_level": "minimal",
        },
        tenant_id=5,
    )

    assert result["review_code"] == "RE-001"
    assert len(created_entities) == 1
    assert created_entities[0][0] == "ethics_reviews"


def test_w33_alert_record_side_effect_on_high_risk(monkeypatch) -> None:
    svc = _load_service()
    monkeypatch.setattr(svc, "_check_pi_has_active_contract_for_ethics_review", lambda *a, **kw: None)

    created_entities: list[tuple[str, dict]] = []

    def fake_list(entity_name, tid):
        return []

    def fake_create(entity_name, payload, tid):
        record = {**payload, "id": len(created_entities) + 1, "tenant_id": tid}
        created_entities.append((entity_name, record))
        return record

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc.create_ethics_review(
        {
            "review_code": "RE-HR-1",
            "project_title": "Critical Risk Trial",
            "principal_investigator_id": "PI-99",
            "review_type": "clinical",
            "status": "under_review",
            "risk_level": "critical",
        },
        tenant_id=7,
    )

    entity_names = [name for name, _ in created_entities]
    assert "ethics_reviews" in entity_names
    assert "ethics_alert_records" in entity_names
    alert = next(r for name, r in created_entities if name == "ethics_alert_records")
    assert alert["integration_source"] == "research_ethics_high_risk"
