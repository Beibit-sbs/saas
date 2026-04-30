"""W34 domain-depth tests — procurement: active vendor category cap + high-risk contract alert side effect."""
from __future__ import annotations

import importlib
import types


def _load_service() -> types.ModuleType:
    return importlib.import_module("app.modules.procurement.service")


def test_w34_source_contains_cap_dict_and_alert_helper() -> None:
    import inspect

    svc = _load_service()
    src = inspect.getsource(svc)
    assert "_VENDOR_CATEGORY_MAX_ACTIVE" in src
    assert "_ACTIVE_VENDOR_STATUSES" in src
    assert "_HIGH_RISK_SCORE_THRESHOLD" in src
    assert "_ensure_risk_alert_record" in src


def test_w34_create_vendor_raises_when_category_cap_reached(monkeypatch) -> None:
    import pytest

    svc = _load_service()

    from app.modules.procurement.schemas import VendorCreateSchema

    cap = svc._VENDOR_CATEGORY_MAX_ACTIVE["it"]
    fake_vendors = [{"category": "it", "status": "active"} for _ in range(cap)]

    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda name, tid: fake_vendors)

    with pytest.raises(ValueError, match="category 'it'"):
        svc.create_vendor(
            tenant_id=1,
            request=VendorCreateSchema(
                vendor_code="VND-999",
                name="Test IT Vendor",
                category="it",
                sla_breach_rate=0.0,
                on_time_delivery_rate=1.0,
                status="active",
            ),
            actor="test-actor",
        )


def test_w34_create_vendor_succeeds_below_cap(monkeypatch) -> None:
    svc = _load_service()

    from app.modules.procurement.schemas import VendorCreateSchema

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

    result = svc.create_vendor(
        tenant_id=3,
        request=VendorCreateSchema(
            vendor_code="VND-001",
            name="Catering Co",
            category="catering",
            sla_breach_rate=0.05,
            on_time_delivery_rate=0.95,
            status="active",
            contact_name="Jane Smith",
        ),
        actor="admin",
    )

    assert result.vendor_code == "VND-001"
    assert len(created_entities) == 1
    assert created_entities[0][0] == "procurement_vendors"


def test_w34_risk_alert_side_effect_on_high_risk_contract(monkeypatch) -> None:
    svc = _load_service()
    monkeypatch.setattr(svc, "_check_vendor_active_for_contract", lambda *a, **kw: None)

    from app.modules.procurement.schemas import ContractCreateSchema

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

    svc.create_contract(
        tenant_id=4,
        request=ContractCreateSchema(
            contract_code="CTR-HR-1",
            vendor_code="VND-HI",
            title="High Risk Infrastructure Contract",
            risk_score=0.9,
            sla_target_met=False,
            status="draft",
        ),
        actor="admin",
    )

    entity_names = [name for name, _ in created_entities]
    assert "procurement_contracts" in entity_names
    assert "procurement_risk_alerts" in entity_names
    alert = next(r for name, r in created_entities if name == "procurement_risk_alerts")
    assert alert["integration_source"] == "procurement_risk"
    assert alert["vendor_code"] == "VND-HI"
