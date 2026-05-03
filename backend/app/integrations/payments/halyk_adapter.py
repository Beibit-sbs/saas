"""L.1 — HalykBank integration adapter (stub)."""
from __future__ import annotations

import uuid

import httpx

HALYK_BASE_URL = "https://epay.homebank.kz"
DEFAULT_TIMEOUT = 10


class HalykBankError(Exception):
    pass


def create_order(
    merchant_id: str,
    amount: float,
    callback_url: str,
    *,
    currency: str = "KZT",
    description: str = "",
) -> dict:
    """Create a Halyk Bank payment order. Returns order_id and redirect_url."""
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
        "backLink": callback_url,
        "description": description,
    }
    try:
        resp = httpx.post(f"{HALYK_BASE_URL}/api/create", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.RequestError as exc:
        raise HalykBankError(f"HalykBank create_order failed: {exc}") from exc

    return {
        "order_id": data.get("invoiceId", str(uuid.uuid4())),
        "redirect_url": data.get("hpUrl", ""),
        "status": "PENDING",
    }


def check_status(order_id: str) -> str:
    """Check payment status. Returns PENDING / PAID / FAILED / REFUNDED."""
    if not order_id:
        raise ValueError("order_id is required")
    try:
        resp = httpx.get(
            f"{HALYK_BASE_URL}/api/check/{order_id}",
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("status", "PENDING")
    except httpx.RequestError as exc:
        raise HalykBankError(f"HalykBank check_status failed: {exc}") from exc


def refund(order_id: str, amount: float) -> bool:
    """Initiate a refund. Returns True on success."""
    if not order_id:
        raise ValueError("order_id is required")
    if amount <= 0:
        raise ValueError("amount must be positive")
    try:
        resp = httpx.post(
            f"{HALYK_BASE_URL}/api/refund",
            json={"invoiceId": order_id, "amount": amount},
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("success", False)
    except httpx.RequestError as exc:
        raise HalykBankError(f"HalykBank refund failed: {exc}") from exc
