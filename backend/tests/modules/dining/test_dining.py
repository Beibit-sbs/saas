"""Phase VI-VI2: Dining module tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch


from app.modules.dining import service as dining_service
from tests.conftest import ADMIN_HEADERS, client as test_client


def test_list_dining_menus_empty(monkeypatch) -> None:
    monkeypatch.setattr(dining_service, "list_entities_for_tenant", lambda name, tid: [])
    assert dining_service.list_dining_menus(tenant_id=1) == []


def test_list_dining_menus_filter_by_meal_type(monkeypatch) -> None:
    rows = [
        {"id": 1, "menu_code": "M-1", "facility_code": "CAFE-A", "meal_type": "lunch", "status": "active", "tenant_id": 1},
        {"id": 2, "menu_code": "M-2", "facility_code": "CAFE-A", "meal_type": "dinner", "status": "active", "tenant_id": 1},
    ]
    monkeypatch.setattr(dining_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = dining_service.list_dining_menus(tenant_id=1, meal_type="lunch")
    assert len(result) == 1
    assert result[0]["menu_code"] == "M-1"


def test_create_dining_menu_capacity_exceeded_fires_signal(monkeypatch) -> None:
    created = {
        "id": 10,
        "menu_code": "M-10",
        "facility_code": "CAFE-B",
        "meal_type": "breakfast",
        "date": "2026-05-01",
        "status": "active",
        "capacity": 50,
        "available_capacity": 0,
        "tenant_id": 1,
    }
    monkeypatch.setattr(dining_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.dining.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = dining_service.create_dining_menu(
            {
                "menu_code": "M-10",
                "facility_code": "CAFE-B",
                "meal_type": "breakfast",
                "status": "active",
                "capacity": 50,
                "available_capacity": 0,
            },
            tenant_id=1,
        )

    assert record["id"] == 10
    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "campus.dining.capacity_exceeded"
    assert call_kwargs["payload_json"]["available_capacity"] == 0


def test_create_dining_menu_capacity_ok_no_signal(monkeypatch) -> None:
    created = {
        "id": 11, "menu_code": "M-11", "facility_code": "CAFE-C",
        "meal_type": "lunch", "status": "active", "capacity": 100,
        "available_capacity": 30, "tenant_id": 1,
    }
    monkeypatch.setattr(dining_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.dining.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        dining_service.create_dining_menu(
            {"menu_code": "M-11", "facility_code": "CAFE-C", "meal_type": "lunch", "status": "active", "capacity": 100, "available_capacity": 30},
            tenant_id=1,
        )

    publisher.publish_event.assert_not_called()


def test_get_dining_brain_context_high_risk(monkeypatch) -> None:
    menus = [
        {"id": 1, "menu_code": "M-1", "meal_type": "lunch", "status": "active", "capacity": 50, "available_capacity": 0, "tenant_id": 1},
        {"id": 2, "menu_code": "M-2", "meal_type": "dinner", "status": "active", "capacity": 80, "available_capacity": 10, "tenant_id": 1},
    ]
    orders = [{"id": 1, "order_code": "O-1", "menu_code": "M-1", "facility_code": "CAFE-A", "meal_type": "lunch", "status": "pending", "tenant_id": 1}]

    def mock_list(name, tid):
        if name == "dining_menus":
            return menus
        return orders

    monkeypatch.setattr(dining_service, "list_entities_for_tenant", mock_list)
    ctx = dining_service.get_dining_brain_context(tenant_id=1)
    assert ctx["risk_level"] == "high"
    assert ctx["capacity_exceeded_menus"] == 1
    assert ctx["total_orders"] == 1


def test_http_list_dining_menus_empty() -> None:
    response = test_client.get("/api/admin/dining/menus", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["records"] == []


def test_http_create_dining_menu() -> None:
    payload = {
        "menu_code": "M-HTTP-1",
        "facility_code": "CAFE-HTTP",
        "meal_type": "lunch",
        "status": "active",
        "capacity": 60,
        "available_capacity": 60,
    }
    response = test_client.post("/api/admin/dining/menus", json=payload, headers=ADMIN_HEADERS)
    assert response.status_code == 201
    data = response.json()["record"]
    assert data["menu_code"] == "M-HTTP-1"
    assert data["meal_type"] == "lunch"


def test_http_get_dining_brain_context() -> None:
    response = test_client.get("/api/admin/dining/brain-context", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    ctx = response.json()
    assert ctx["module"] == "dining"
    assert "risk_level" in ctx
