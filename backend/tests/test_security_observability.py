import pytest

from app.modules.auth.token_service import create_access_token, revoke_token, verify_access_token
from app.modules.observability.security_signals import snapshot_security_metrics
from tests.conftest import ADMIN_HEADERS, client


pytestmark = pytest.mark.security_regression


def _event_count(signal: str, outcome: str) -> int:
    events, _ = snapshot_security_metrics()
    return int(events.get((signal, outcome), 0))


def _anomaly_count(signal: str) -> int:
    _, anomalies = snapshot_security_metrics()
    return int(anomalies.get(signal, 0))


def test_cross_tenant_override_denied_emits_security_signal() -> None:
    create_tenant = client.post(
        "/api/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": "tenant-b-signal", "name": "Tenant B Signal", "status": "active"},
    )
    assert create_tenant.status_code == 200, create_tenant.text
    tenant_b_id = int(create_tenant.json()["tenant"]["id"])

    denied = client.get(
        "/api/admin/local-users",
        headers={**ADMIN_HEADERS, "X-Tenant-ID": str(tenant_b_id)},
    )
    assert denied.status_code == 403, denied.text

    assert _event_count("tenant.override.denied", "denied") >= 1


def test_revoked_token_reuse_emits_security_signal() -> None:
    token = create_access_token(user_id="owner@example.com", roles=["admin"], auth_source="test", tenant_id=1)
    claims = verify_access_token(token)
    revoke_token(claims.jti, expires_at=claims.expires_at)

    denied = client.get(
        "/api/auth/me/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 401, denied.text

    assert _event_count("auth.token.revoked_reuse", "denied") >= 1


def test_repeated_metrics_auth_failures_emit_anomaly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("METRICS_TOKEN", "metrics-test-token")

    for _ in range(4):
        response = client.get("/metrics")
        assert response.status_code == 401, response.text

    assert _event_count("metrics.access.denied", "denied") >= 4
    assert _anomaly_count("metrics.access.denied") >= 1
