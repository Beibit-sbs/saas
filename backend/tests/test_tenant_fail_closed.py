import base64
import hashlib
import hmac
import json
import os
import time
from uuid import uuid4

import pytest

from tests.conftest import client


pytestmark = pytest.mark.security_regression


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _mint_custom_access_token(*, include_tid: bool, tid_value: int | None = None) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload: dict[str, object] = {
        "sub": "tenant.failclosed.user",
        "roles": ["admin"],
        "scp": ["admin.read", "admin.write"],
        "src": "test",
        "jti": str(uuid4()),
        "pg": False,
        "iat": now,
        "exp": now + 3600,
        "token_type": "access",
        "ver": 1,
    }
    if include_tid:
        payload["tid"] = tid_value

    header_b64 = _b64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    secret = os.environ["JWT_SECRET"].encode("utf-8")
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url(signature)}"


def test_missing_tenant_claim_fails_closed_for_read_path() -> None:
    token = _mint_custom_access_token(include_tid=False)
    response = client.get(
        "/api/admin/students",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "invalid token tenant" in response.json().get("detail", "")


def test_invalid_tenant_claim_fails_closed() -> None:
    token = _mint_custom_access_token(include_tid=True, tid_value=0)
    response = client.get(
        "/api/admin/students",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "invalid token tenant" in response.json().get("detail", "")


def test_write_without_valid_tenant_context_fails_closed() -> None:
    token = _mint_custom_access_token(include_tid=False)
    response = client.post(
        "/api/admin/local-users",
        headers={"Authorization": f"Bearer {token}"},
        json={"login": "blocked", "password": "blocked", "display_name": "Blocked", "roles": ["admin"]},
    )
    assert response.status_code == 401
    assert "invalid token tenant" in response.json().get("detail", "")


def test_read_without_authentication_fails_closed() -> None:
    response = client.get("/api/admin/students")
    assert response.status_code == 401


def test_developer_api_rejects_manual_tenant_override() -> None:
    response = client.get(
        "/api/dev/students",
        headers={
            "X-App-Key": "app_key_any",
            "X-App-Secret": "app_secret_any",
            "X-Tenant-Id": "2",
        },
    )
    assert response.status_code == 400
    assert "manual tenant override is forbidden" in response.json().get("detail", "")
