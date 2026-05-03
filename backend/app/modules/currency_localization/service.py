"""Phase LX — Multi-currency / Multi-language localization service."""
from __future__ import annotations

from dataclasses import dataclass

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

SUPPORTED_CURRENCIES = {"USD", "EUR", "KZT", "RUB", "GBP", "CNY"}
SUPPORTED_LANGUAGES = {"kk", "ru", "en"}


class LocalizationError(Exception):
    """Raised on invalid localization operations."""


@dataclass
class ExchangeRate:
    rate_id: int
    tenant_id: int
    base_currency: str
    quote_currency: str
    rate: float
    active: bool


@dataclass
class TenantLocaleProfile:
    profile_id: int
    tenant_id: int
    currency_code: str
    language_code: str
    timezone: str


def upsert_exchange_rate(
    base_currency: str,
    quote_currency: str,
    rate: float,
    tenant_id: int,
) -> ExchangeRate:
    """Create or update FX rate for tenant."""
    base = (base_currency or "").strip().upper()
    quote = (quote_currency or "").strip().upper()

    if base not in SUPPORTED_CURRENCIES:
        raise LocalizationError("unsupported base_currency")
    if quote not in SUPPORTED_CURRENCIES:
        raise LocalizationError("unsupported quote_currency")
    if base == quote:
        raise LocalizationError("base_currency and quote_currency must differ")
    if rate <= 0:
        raise LocalizationError("rate must be > 0")

    rows = list_entities_for_tenant("currency_exchange_rates", tenant_id)
    existing = next(
        (
            row
            for row in rows
            if row.get("base_currency") == base and row.get("quote_currency") == quote
        ),
        None,
    )

    if existing:
        updated = update_entity_for_tenant(
            "currency_exchange_rates",
            existing["id"],
            {"rate": float(rate), "active": True},
            tenant_id,
        )
        row = updated
    else:
        row = create_entity_for_tenant(
            "currency_exchange_rates",
            {
                "base_currency": base,
                "quote_currency": quote,
                "rate": float(rate),
                "active": True,
            },
            tenant_id,
        )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="localization.exchange_rate_updated",
            payload={"base_currency": base, "quote_currency": quote, "rate": float(rate)},
        )
    except Exception:
        pass

    return ExchangeRate(
        rate_id=row["id"],
        tenant_id=tenant_id,
        base_currency=row["base_currency"],
        quote_currency=row["quote_currency"],
        rate=float(row["rate"]),
        active=bool(row.get("active", True)),
    )


def convert_amount(
    amount: float,
    from_currency: str,
    to_currency: str,
    tenant_id: int,
) -> float:
    """Convert amount using tenant-specific FX table."""
    if amount < 0:
        raise LocalizationError("amount must be >= 0")

    source = (from_currency or "").strip().upper()
    target = (to_currency or "").strip().upper()

    if source not in SUPPORTED_CURRENCIES:
        raise LocalizationError("unsupported from_currency")
    if target not in SUPPORTED_CURRENCIES:
        raise LocalizationError("unsupported to_currency")
    if source == target:
        return round(float(amount), 2)

    rows = list_entities_for_tenant("currency_exchange_rates", tenant_id)

    direct = next(
        (
            row
            for row in rows
            if row.get("base_currency") == source
            and row.get("quote_currency") == target
            and bool(row.get("active", True))
        ),
        None,
    )
    if direct:
        converted = float(amount) * float(direct.get("rate") or 0)
    else:
        inverse = next(
            (
                row
                for row in rows
                if row.get("base_currency") == target
                and row.get("quote_currency") == source
                and bool(row.get("active", True))
            ),
            None,
        )
        if not inverse or float(inverse.get("rate") or 0) <= 0:
            raise LocalizationError("exchange rate not found")
        converted = float(amount) / float(inverse.get("rate") or 1)

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="localization.amount_converted",
            payload={
                "from_currency": source,
                "to_currency": target,
                "amount": float(amount),
                "converted_amount": round(converted, 2),
            },
        )
    except Exception:
        pass

    return round(converted, 2)


def set_tenant_locale(
    currency_code: str,
    language_code: str,
    timezone: str,
    tenant_id: int,
) -> TenantLocaleProfile:
    """Create or update tenant locale profile."""
    currency = (currency_code or "").strip().upper()
    language = (language_code or "").strip().lower()
    tz = (timezone or "").strip()

    if currency not in SUPPORTED_CURRENCIES:
        raise LocalizationError("unsupported currency_code")
    if language not in SUPPORTED_LANGUAGES:
        raise LocalizationError("unsupported language_code")
    if not tz:
        raise LocalizationError("timezone is required")

    rows = list_entities_for_tenant("tenant_localization_profiles", tenant_id)
    existing = rows[0] if rows else None

    if existing:
        row = update_entity_for_tenant(
            "tenant_localization_profiles",
            existing["id"],
            {"currency_code": currency, "language_code": language, "timezone": tz},
            tenant_id,
        )
    else:
        row = create_entity_for_tenant(
            "tenant_localization_profiles",
            {"currency_code": currency, "language_code": language, "timezone": tz},
            tenant_id,
        )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="localization.locale_updated",
            payload={"currency_code": currency, "language_code": language, "timezone": tz},
        )
    except Exception:
        pass

    return TenantLocaleProfile(
        profile_id=row["id"],
        tenant_id=tenant_id,
        currency_code=row["currency_code"],
        language_code=row["language_code"],
        timezone=row["timezone"],
    )


def get_tenant_locale(tenant_id: int) -> TenantLocaleProfile | None:
    """Get tenant locale profile, if configured."""
    rows = list_entities_for_tenant("tenant_localization_profiles", tenant_id)
    if not rows:
        return None

    row = rows[0]
    return TenantLocaleProfile(
        profile_id=row["id"],
        tenant_id=tenant_id,
        currency_code=row["currency_code"],
        language_code=row["language_code"],
        timezone=row["timezone"],
    )


def format_money(amount: float, currency_code: str) -> str:
    """Simple money formatter for supported currencies."""
    currency = (currency_code or "").strip().upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise LocalizationError("unsupported currency_code")

    symbol_map = {
        "USD": "$",
        "EUR": "€",
        "KZT": "KZT ",
        "RUB": "RUB ",
        "GBP": "£",
        "CNY": "¥",
    }
    symbol = symbol_map.get(currency, f"{currency} ")
    return f"{symbol}{float(amount):.2f}"
