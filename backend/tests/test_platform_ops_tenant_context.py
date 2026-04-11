from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.platform import router_ops


def _request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/api/v1/platform/ops/summary", "headers": []})


def test_resolve_request_tenant_id_rejects_non_positive_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        router_ops,
        "resolve_current_user_claims",
        lambda *_args, **_kwargs: SimpleNamespace(tenant_id=0),
    )

    with pytest.raises(HTTPException) as exc:
        router_ops._resolve_request_tenant_id(_request())

    assert exc.value.status_code == 403
    assert exc.value.detail == "tenant context missing"


def test_resolve_request_tenant_id_accepts_positive_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        router_ops,
        "resolve_current_user_claims",
        lambda *_args, **_kwargs: SimpleNamespace(tenant_id=7),
    )

    assert router_ops._resolve_request_tenant_id(_request()) == 7
