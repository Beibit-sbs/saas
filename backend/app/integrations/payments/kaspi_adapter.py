"""L.1 — KaspiPay integration adapter (stub)."""
from __future__ import annotations

import uuid

import httpx

KASPI_BASE_URL = "https://kaspi.kz/online"
DEFAULT_TIMEOUT = 10


class KaspiPayError(Exception):
    pass

_RequestError = httpx.RequestError


def create_order(
    merchant_id: str,
    amount: float,
    callback_url: str,
    *,
    currency: str = "KZT",
    description: str = "",
) -> dict:
    """Create a Kaspi Pay order. Returns qr_code and order_id."""
    if not merchant_id:
        raise ValueError("merchant_id is required")
    if amount <= 0:
        raise ValueError("amount must be positive")
    if not callback_url:
        raise ValueError("callback_url is required")

    payload = {
        "merchantId": merchant_id,
        "amount": amount,
        "currency": currency,
        "callbackUrl": callback_url,
        "description": description,
    }
    try:
        resp = httpx.post(f"{KASPI_BASE_URL}/payment/create", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as exc:
        raise KaspiPayError(f"KaspiPay create_order failed: {exc}") from exc

    return {
        "order_id": data.get("orderId", str(uuid.uuid4())),
        "qr_code": data.get("qrCode", ""),
        "status": "PENDING",
    }


def check_status(order_id: str) -> str:
    """Check payment status. Returns PENDING / PAID / FAILED / REFUNDED."""
    if not order_id:
        raise ValueError("order_id is required")
    try:
        resp = httpx.get(
            f"{KASPI_BASE_URL}/payment/status/{order_id}",
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("status", "PENDING")
    except httpx.RequestError as exc:
        raise KaspiPayError(f"KaspiPay check_status failed: {exc}") from exc


def refund(order_id: str, amount: float) -> bool:
    """Initiate a refund. Returns True on success."""
    if not order_id:
        raise ValueError("order_id is required")
    if amount <= 0:
        raise ValueError("amount must be positive")
    try:
        resp = httpx.post(
            f"{KASPI_BASE_URL}/payment/refund",
            json={"orderId": order_id, "amount": amount},
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("success", False)
    except httpx.RequestError as exc:
        raise KaspiPayError(f"KaspiPay refund failed: {exc}") from exc
