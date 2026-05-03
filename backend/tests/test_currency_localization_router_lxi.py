from __future__ import annotations

from dataclasses import asdict
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.currency_localization.router import router
from app.modules.currency_localization.service import ExchangeRate, LocalizationError, TenantLocaleProfile


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_upsert_exchange_rate_endpoint_success():
    payload = {
        "tenant_id": 1,
        "base_currency": "USD",
        "quote_currency": "KZT",
        "rate": 500.0,
    }
    expected = ExchangeRate(1, 1, "USD", "KZT", 500.0, True)

    with patch("app.modules.currency_localization.router.upsert_exchange_rate", return_value=expected):
        response = client.put("/api/admin/currency-localization/exchange-rates", json=payload)

    assert response.status_code == 200
    assert response.json() == asdict(expected)


def test_upsert_exchange_rate_endpoint_validation_error():
    payload = {
        "tenant_id": 1,
        "base_currency": "BTC",
        "quote_currency": "USD",
        "rate": 1.0,
    }

    with patch(
        "app.modules.currency_localization.router.upsert_exchange_rate",
        side_effect=LocalizationError("unsupported base_currency"),
    ):
        response = client.put("/api/admin/currency-localization/exchange-rates", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "unsupported base_currency"


def test_convert_amount_endpoint_success():
    payload = {
        "tenant_id": 1,
        "amount": 10.0,
        "from_currency": "USD",
        "to_currency": "KZT",
    }

    with (
        patch("app.modules.currency_localization.router.convert_amount", return_value=5000.0),
        patch("app.modules.currency_localization.router.format_money", return_value="KZT 5000.00"),
    ):
        response = client.post("/api/admin/currency-localization/convert", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["converted_amount"] == 5000.0
    assert body["formatted_converted_amount"] == "KZT 5000.00"


def test_convert_amount_endpoint_validation_error():
    payload = {
        "tenant_id": 1,
        "amount": 10.0,
        "from_currency": "USD",
        "to_currency": "KZT",
    }

    with patch(
        "app.modules.currency_localization.router.convert_amount",
        side_effect=LocalizationError("exchange rate not found"),
    ):
        response = client.post("/api/admin/currency-localization/convert", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "exchange rate not found"


def test_set_tenant_locale_endpoint_success():
    payload = {
        "tenant_id": 1,
        "currency_code": "KZT",
        "language_code": "kk",
        "timezone": "Asia/Almaty",
    }
    expected = TenantLocaleProfile(1, 1, "KZT", "kk", "Asia/Almaty")

    with patch("app.modules.currency_localization.router.set_tenant_locale", return_value=expected):
        response = client.put("/api/admin/currency-localization/tenant-locale", json=payload)

    assert response.status_code == 200
    assert response.json() == asdict(expected)


def test_get_tenant_locale_endpoint_not_found():
    with patch("app.modules.currency_localization.router.get_tenant_locale", return_value=None):
        response = client.get("/api/admin/currency-localization/tenant-locale/1")

    assert response.status_code == 404


def test_get_tenant_locale_endpoint_success():
    expected = TenantLocaleProfile(3, 1, "USD", "en", "UTC")
    with patch("app.modules.currency_localization.router.get_tenant_locale", return_value=expected):
        response = client.get("/api/admin/currency-localization/tenant-locale/1")

    assert response.status_code == 200
    assert response.json() == asdict(expected)


def test_format_money_endpoint_success():
    with patch("app.modules.currency_localization.router.format_money", return_value="$10.00"):
        response = client.get("/api/admin/currency-localization/format-money?amount=10&currency_code=USD")

    assert response.status_code == 200
    assert response.json()["formatted"] == "$10.00"
