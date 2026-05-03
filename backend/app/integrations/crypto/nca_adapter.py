"""L.3 — NCA ЭЦП (Национальный удостоверяющий центр) adapter (stub)."""
from __future__ import annotations

import base64
import hashlib

import httpx

NCA_BASE_URL = "https://nca.pki.gov.kz/api"
DEFAULT_TIMEOUT = 30


class NcaError(Exception):
    pass


class SignerInfo:
    def __init__(self, iin: str, cn: str, valid: bool, serial: str, not_after: str):
        self.iin = iin
        self.cn = cn
        self.valid = valid
        self.serial = serial
        self.not_after = not_after

    def to_dict(self) -> dict:
        return {
            "iin": self.iin,
            "cn": self.cn,
            "valid": self.valid,
            "serial": self.serial,
            "not_after": self.not_after,
        }


def sign(doc_bytes: bytes, p12_cert: bytes, *, password: str = "") -> bytes:
    """Sign document bytes using p12 certificate. Returns CAdES-BES signature bytes."""
    if not doc_bytes:
        raise ValueError("doc_bytes is required")
    if not p12_cert:
        raise ValueError("p12_cert is required")

    payload = {
        "data": base64.b64encode(doc_bytes).decode(),
        "p12": base64.b64encode(p12_cert).decode(),
        "password": password,
        "signatureType": "CAdES-BES",
    }
    try:
        resp = httpx.post(f"{NCA_BASE_URL}/cms/sign", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        signed_b64 = resp.json().get("cms", "")
        return base64.b64decode(signed_b64) if signed_b64 else b""
    except httpx.RequestError as exc:
        raise NcaError(f"NCA sign failed: {exc}") from exc


def verify_signature(signed_doc: bytes) -> SignerInfo:
    """Verify CAdES-BES signature. Returns SignerInfo with signer details."""
    if not signed_doc:
        raise ValueError("signed_doc is required")

    payload = {
        "cms": base64.b64encode(signed_doc).decode(),
    }
    try:
        resp = httpx.post(f"{NCA_BASE_URL}/cms/verify", json=payload, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return SignerInfo(
            iin=data.get("iin", ""),
            cn=data.get("cn", ""),
            valid=data.get("valid", False),
            serial=data.get("serial", ""),
            not_after=data.get("notAfter", ""),
        )
    except httpx.RequestError as exc:
        raise NcaError(f"NCA verify_signature failed: {exc}") from exc
