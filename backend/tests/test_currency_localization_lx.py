"""Phase LX — Multi-currency / Multi-language tests (24 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

MODULE = "app.modules.currency_localization.service"


def _rate_row(
    id: int = 1,
    base_currency: str = "USD",
    quote_currency: str = "KZT",
    rate: float = 450.0,
    active: bool = True,
) -> dict:
    return {
        "id": id,
        "base_currency": base_currency,
        "quote_currency": quote_currency,
        "rate": rate,
        "active": active,
    }


def _locale_row(
    id: int = 1,
    currency_code: str = "KZT",
    language_code: str = "kk",
    timezone: str = "Asia/Almaty",
) -> dict:
    return {
        "id": id,
        "currency_code": currency_code,
        "language_code": language_code,
        "timezone": timezone,
    }


def test_upsert_exchange_rate_create_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_rate_row()) as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.currency_localization import service

        result = service.upsert_exchange_rate("usd", "kzt", 450.0, 1)

    assert result.rate_id == 1
    assert result.base_currency == "USD"
    mock_create.assert_called_once()
    mock_pub.publish.assert_called_once()


def test_upsert_exchange_rate_update_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_rate_row(id=10)]),
        patch(f"{MODULE}.update_entity_for_tenant", return_value=_rate_row(id=10, rate=460.0)) as mock_update,
    ):
        from app.modules.currency_localization import service

        result = service.upsert_exchange_rate("USD", "KZT", 460.0, 1)

    assert result.rate_id == 10
    assert result.rate == 460.0
    mock_update.assert_called_once_with(
        "currency_exchange_rates",
        10,
        {"rate": 460.0, "active": True},
        1,
    )


def test_upsert_exchange_rate_invalid_base_currency():
    from app.modules.currency_localization.service import LocalizationError, upsert_exchange_rate

    with pytest.raises(LocalizationError, match="base_currency"):
        upsert_exchange_rate("BTC", "USD", 1.0, 1)


def test_upsert_exchange_rate_invalid_quote_currency():
    from app.modules.currency_localization.service import LocalizationError, upsert_exchange_rate

    with pytest.raises(LocalizationError, match="quote_currency"):
        upsert_exchange_rate("USD", "BTC", 1.0, 1)


def test_upsert_exchange_rate_same_currencies():
    from app.modules.currency_localization.service import LocalizationError, upsert_exchange_rate

    with pytest.raises(LocalizationError, match="must differ"):
        upsert_exchange_rate("USD", "USD", 1.0, 1)


def test_upsert_exchange_rate_invalid_rate():
    from app.modules.currency_localization.service import LocalizationError, upsert_exchange_rate

    with pytest.raises(LocalizationError, match="rate"):
        upsert_exchange_rate("USD", "KZT", 0.0, 1)


def test_upsert_exchange_rate_event_error_suppressed():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_rate_row()),
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        mock_pub.publish.side_effect = RuntimeError("down")
        from app.modules.currency_localization import service

        result = service.upsert_exchange_rate("USD", "KZT", 450.0, 1)

    assert result.rate == 450.0


def test_convert_amount_direct_rate():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_rate_row(rate=500.0)]):
        from app.modules.currency_localization import service

        result = service.convert_amount(10.0, "USD", "KZT", 1)

    assert result == 5000.0


def test_convert_amount_inverse_rate():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_rate_row(base_currency="KZT", quote_currency="USD", rate=500.0)]):
        from app.modules.currency_localization import service

        result = service.convert_amount(5000.0, "USD", "KZT", 1)

    assert result == 10.0


def test_convert_amount_same_currency():
    from app.modules.currency_localization import service

    result = service.convert_amount(123.456, "USD", "USD", 1)
    assert result == 123.46


def test_convert_amount_negative_amount():
    from app.modules.currency_localization.service import LocalizationError, convert_amount

    with pytest.raises(LocalizationError, match="amount"):
        convert_amount(-1.0, "USD", "KZT", 1)


def test_convert_amount_unsupported_source_currency():
    from app.modules.currency_localization.service import LocalizationError, convert_amount

    with pytest.raises(LocalizationError, match="from_currency"):
        convert_amount(10.0, "BTC", "KZT", 1)


def test_convert_amount_unsupported_target_currency():
    from app.modules.currency_localization.service import LocalizationError, convert_amount

    with pytest.raises(LocalizationError, match="to_currency"):
        convert_amount(10.0, "USD", "BTC", 1)


def test_convert_amount_rate_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.currency_localization.service import LocalizationError, convert_amount

        with pytest.raises(LocalizationError, match="not found"):
            convert_amount(10.0, "USD", "KZT", 1)


def test_convert_amount_event_error_suppressed():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_rate_row(rate=500.0)]),
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        mock_pub.publish.side_effect = RuntimeError("down")
        from app.modules.currency_localization import service

        result = service.convert_amount(10.0, "USD", "KZT", 1)

    assert result == 5000.0


def test_set_tenant_locale_create_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_locale_row()) as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.currency_localization import service

        result = service.set_tenant_locale("KZT", "kk", "Asia/Almaty", 1)

    assert result.profile_id == 1
    mock_create.assert_called_once()
    mock_pub.publish.assert_called_once()


def test_set_tenant_locale_update_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_locale_row(id=2)]),
        patch(f"{MODULE}.update_entity_for_tenant", return_value=_locale_row(id=2, language_code="ru")) as mock_update,
    ):
        from app.modules.currency_localization import service

        result = service.set_tenant_locale("KZT", "ru", "Asia/Almaty", 1)

    assert result.profile_id == 2
    assert result.language_code == "ru"
    mock_update.assert_called_once_with(
        "tenant_localization_profiles",
        2,
        {"currency_code": "KZT", "language_code": "ru", "timezone": "Asia/Almaty"},
        1,
    )


def test_set_tenant_locale_invalid_currency():
    from app.modules.currency_localization.service import LocalizationError, set_tenant_locale

    with pytest.raises(LocalizationError, match="currency_code"):
        set_tenant_locale("BTC", "kk", "Asia/Almaty", 1)


def test_set_tenant_locale_invalid_language():
    from app.modules.currency_localization.service import LocalizationError, set_tenant_locale

    with pytest.raises(LocalizationError, match="language_code"):
        set_tenant_locale("KZT", "de", "Asia/Almaty", 1)


def test_set_tenant_locale_missing_timezone():
    from app.modules.currency_localization.service import LocalizationError, set_tenant_locale

    with pytest.raises(LocalizationError, match="timezone"):
        set_tenant_locale("KZT", "kk", "", 1)


def test_get_tenant_locale_none_when_missing():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.currency_localization import service

        result = service.get_tenant_locale(1)

    assert result is None


def test_get_tenant_locale_success():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_locale_row(id=3, currency_code="USD", language_code="en")]):
        from app.modules.currency_localization import service

        result = service.get_tenant_locale(1)

    assert result is not None
    assert result.profile_id == 3
    assert result.currency_code == "USD"
    assert result.language_code == "en"


def test_format_money_success():
    from app.modules.currency_localization import service

    assert service.format_money(12.3, "USD") == "$12.30"
    assert service.format_money(5, "KZT") == "KZT 5.00"


def test_format_money_invalid_currency():
    from app.modules.currency_localization.service import LocalizationError, format_money

    with pytest.raises(LocalizationError, match="currency_code"):
        format_money(10.0, "BTC")
