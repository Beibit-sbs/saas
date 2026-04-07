from __future__ import annotations

import pytest

from app.core import config


pytestmark = pytest.mark.security_regression


def test_internal_scopes_fail_closed_in_production_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INTERNAL_API_ALLOWED_SCOPES", raising=False)

    scopes = config.get_internal_api_allowed_scopes()
    assert "worker.run_once" in scopes
    assert "scheduler.run_once" in scopes


def test_internal_scopes_reject_wildcard_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTERNAL_API_ALLOWED_SCOPES", "*")

    assert config.get_internal_api_allowed_scopes() == {"*"}


def test_trusted_hosts_fail_closed_in_production_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRUSTED_HOSTS", raising=False)
    assert config.get_trusted_hosts() == ["localhost", "127.0.0.1", "backend", "nginx"]


def test_trusted_hosts_reject_wildcard_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRUSTED_HOSTS", "backend,nginx")
    assert config.get_trusted_hosts() == ["backend", "nginx"]
