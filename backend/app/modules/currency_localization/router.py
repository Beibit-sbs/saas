"""Phase LXI - Currency localization admin API."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.currency_localization.service import (
    LocalizationError,
    convert_amount,
    format_money,
    get_tenant_locale,
    set_tenant_locale,
    upsert_exchange_rate,
)

router = APIRouter(prefix="/api/admin/currency-localization", tags=["currency-localization"])


class ExchangeRateUpsertPayload(BaseModel):
    tenant_id: int = Field(gt=0)
    base_currency: str = Field(min_length=3, max_length=3)
    quote_currency: str = Field(min_length=3, max_length=3)
    rate: float = Field(gt=0)


class ConvertAmountPayload(BaseModel):
    tenant_id: int = Field(gt=0)
    amount: float = Field(ge=0)
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(min_length=3, max_length=3)


class TenantLocalePayload(BaseModel):
    tenant_id: int = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    language_code: str = Field(min_length=2, max_length=10)
    timezone: str = Field(min_length=1, max_length=128)


@router.put("/exchange-rates")
def upsert_exchange_rate_endpoint(payload: ExchangeRateUpsertPayload) -> dict:
    try:
        result = upsert_exchange_rate(
            base_currency=payload.base_currency,
            quote_currency=payload.quote_currency,
            rate=payload.rate,
            tenant_id=payload.tenant_id,
        )
    except LocalizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(result)


@router.post("/convert")
def convert_amount_endpoint(payload: ConvertAmountPayload) -> dict:
    try:
        converted_amount = convert_amount(
            amount=payload.amount,
            from_currency=payload.from_currency,
            to_currency=payload.to_currency,
            tenant_id=payload.tenant_id,
        )
        formatted_amount = format_money(converted_amount, payload.to_currency)
    except LocalizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "tenant_id": payload.tenant_id,
        "from_currency": payload.from_currency.upper(),
        "to_currency": payload.to_currency.upper(),
        "amount": payload.amount,
        "converted_amount": converted_amount,
        "formatted_converted_amount": formatted_amount,
    }


@router.put("/tenant-locale")
def set_tenant_locale_endpoint(payload: TenantLocalePayload) -> dict:
    try:
        result = set_tenant_locale(
            currency_code=payload.currency_code,
            language_code=payload.language_code,
            timezone=payload.timezone,
            tenant_id=payload.tenant_id,
        )
    except LocalizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return asdict(result)


@router.get("/tenant-locale/{tenant_id}")
def get_tenant_locale_endpoint(tenant_id: int) -> dict:
    if tenant_id <= 0:
        raise HTTPException(status_code=400, detail="tenant_id must be > 0")

    result = get_tenant_locale(tenant_id)
    if result is None:
        raise HTTPException(status_code=404, detail="tenant locale profile not found")
    return asdict(result)


@router.get("/format-money")
def format_money_endpoint(amount: float, currency_code: str) -> dict:
    try:
        value = format_money(amount, currency_code)
    except LocalizationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "amount": amount,
        "currency_code": currency_code.upper(),
        "formatted": value,
    }
