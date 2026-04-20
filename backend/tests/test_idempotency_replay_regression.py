from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from app.core.module_helpers.service_validation import MutationResult
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.jobs import service as jobs_service
from app.platform.uow import UnitOfWork
from tests.conftest import ADMIN_HEADERS, client


def test_jobs_replay_contract_remains_explicit() -> None:
    jobs_service.clear_jobs_state()
    marker = uuid4().hex

    first = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "backup.run", "payload": {"source": marker}, "max_retries": 1},
    )
    assert first.status_code == 200, first.text
    first_body = first.json()["job"]
    assert first_body["deduplicated"] is False

    second = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "backup.run", "payload": {"source": marker}, "max_retries": 1},
    )
    assert second.status_code == 200, second.text
    second_body = second.json()["job"]
    assert second_body["deduplicated"] is True
    assert isinstance(second_body.get("dedup_key"), str)
    assert second_body["dedup_key"]
    assert int(second_body["id"]) == int(first_body["id"])


def test_integrations_replay_contract_remains_explicit() -> None:
    marker = uuid4().hex
    payload = {
        "enabled": True,
        "server_uri": f"ldap://cross-domain-{marker}.example.local:389",
        "bind_dn": "CN=svc_bind,OU=ServiceAccounts,DC=example,DC=local",
        "base_dn": "DC=example,DC=local",
        "user_filter": "(sAMAccountName={username})",
    }

    first = client.put("/api/admin/integrations/ldap", json=payload, headers=ADMIN_HEADERS)
    assert first.status_code == 200, first.text
    assert first.json()["idempotent_replay"] is False

    second = client.put("/api/admin/integrations/ldap", json=payload, headers=ADMIN_HEADERS)
    assert second.status_code == 200, second.text
    assert second.json()["idempotent_replay"] is True
    assert second.json()["ldap"]["server_uri"] == first.json()["ldap"]["server_uri"]


def test_rbac_roles_upsert_replay_contract_remains_explicit(reset_shared_state) -> None:
    """ERP-QA-27: POST /rbac/roles replay contract — same (name, permissions) → idempotent_replay=True."""
    from uuid import uuid4
    suffix = uuid4().hex[:8]
    role_name = f"replay-reg-27-{suffix}"
    payload = {"name": role_name, "permissions": ["records.read"]}

    first = client.post("/api/admin/rbac/roles", headers=ADMIN_HEADERS, json=payload)
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert "idempotent_replay" in first_body, "idempotent_replay field must be present"
    assert first_body["idempotent_replay"] is False

    second = client.post("/api/admin/rbac/roles", headers=ADMIN_HEADERS, json=payload)
    assert second.status_code == 200, second.text
    assert second.json()["idempotent_replay"] is True
    assert second.json()["role"] == first_body["role"]


def test_billing_replay_contract_remains_explicit() -> None:
    marker = uuid4().hex[:8]
    plan_code = f"cross-domain-{marker}"

    created = client.post(
        "/api/v1/admin/billing/plans",
        headers=ADMIN_HEADERS,
        json={
            "code": plan_code,
            "name": "Cross Domain Replay Plan",
            "price_cents": 3100,
            "features": {"analytics": True},
            "limits": {"analytics_queries": 75},
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["idempotent_replay"] is False

    first = client.put(
        "/api/v1/admin/tenants/1/billing/subscription",
        headers=ADMIN_HEADERS,
        json={"plan_code": plan_code},
    )
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.put(
        "/api/v1/admin/tenants/1/billing/subscription",
        headers=ADMIN_HEADERS,
        json={"plan_code": plan_code},
    )
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert second_body["subscription"]["plan_code"] == plan_code
    assert second_body["subscription"]["started_at"] == first_body["subscription"]["started_at"]


def test_billing_plan_create_replay_contract_remains_explicit() -> None:
    marker = uuid4().hex[:8]
    payload = {
        "code": f"plan-replay-{marker}",
        "name": "Plan Replay",
        "price_cents": 4100,
        "features": {"analytics": True},
        "limits": {"analytics_queries": 90},
    }

    first = client.post(
        "/api/v1/admin/billing/plans",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.post(
        "/api/v1/admin/billing/plans",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert second.status_code == 201, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert int(second_body["plan"]["id"]) == int(first_body["plan"]["id"])

    conflicting = client.post(
        "/api/v1/admin/billing/plans",
        headers=ADMIN_HEADERS,
        json={**payload, "price_cents": 4200},
    )
    assert conflicting.status_code == 400, conflicting.text


def test_tenant_create_replay_contract_remains_explicit() -> None:
    suffix = uuid4().hex[:8]
    payload = {
        "slug": f"tenant-replay-{suffix}",
        "name": f"Tenant Replay {suffix}",
    }

    first = client.post(
        "/api/v1/admin/tenants",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.post(
        "/api/v1/admin/tenants",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert second.status_code == 201, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert int(second_body["tenant_id"]) == int(first_body["tenant_id"])

    conflicting = client.post(
        "/api/v1/admin/tenants",
        headers=ADMIN_HEADERS,
        json={**payload, "name": "Different Name"},
    )
    assert conflicting.status_code == 400, conflicting.text


def test_notifications_replay_contract_remains_explicit_with_idempotency_key() -> None:
    marker = uuid4().hex[:8]
    headers = {**ADMIN_HEADERS, "Idempotency-Key": f"notif-regression-{marker}"}
    payload = {
        "tenant_id": 1,
        "channel": "email",
        "target": f"ops-regression-{marker}@example.com",
        "subject": "Idempotency Regression",
        "payload": {"event": "notification.dispatch"},
    }

    first = client.post("/api/v1/admin/notifications", headers=headers, json=payload)
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.post("/api/v1/admin/notifications", headers=headers, json=payload)
    assert second.status_code == 201, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert int(second_body["notification"]["id"]) == int(first_body["notification"]["id"])


def test_webhooks_replay_contract_remains_explicit() -> None:
    marker = uuid4().hex[:8]
    target_url = f"https://example.com/webhooks/regression/{marker}"
    payload = {
        "tenant_id": 1,
        "event_type": "student.created",
        "target_url": target_url,
        "signing_secret": "webhook-regression-signing-secret-1234",
    }

    first = client.post("/api/v1/admin/webhooks/subscriptions", headers=ADMIN_HEADERS, json=payload)
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.post("/api/v1/admin/webhooks/subscriptions", headers=ADMIN_HEADERS, json=payload)
    assert second.status_code == 201, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert int(second_body["subscription"]["id"]) == int(first_body["subscription"]["id"])

    deactivate_first = client.post(
        f"/api/v1/admin/webhooks/subscriptions/{int(first_body['subscription']['id'])}/deactivate",
        headers=ADMIN_HEADERS,
    )
    assert deactivate_first.status_code == 200, deactivate_first.text
    deactivate_first_body = deactivate_first.json()
    assert deactivate_first_body["idempotent_replay"] is False

    deactivate_second = client.post(
        f"/api/v1/admin/webhooks/subscriptions/{int(first_body['subscription']['id'])}/deactivate",
        headers=ADMIN_HEADERS,
    )
    assert deactivate_second.status_code == 200, deactivate_second.text
    deactivate_second_body = deactivate_second.json()
    assert deactivate_second_body["idempotent_replay"] is True


def test_feature_flags_replay_contract_remains_explicit() -> None:
    marker = uuid4().hex[:8]

    first = client.put(
        f"/api/v1/admin/features/analytics/replay_{marker}",
        headers=ADMIN_HEADERS,
        json={"enabled": True, "rollout_percentage": 42},
    )
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.put(
        f"/api/v1/admin/features/analytics/replay_{marker}",
        headers=ADMIN_HEADERS,
        json={"enabled": True, "rollout_percentage": 42},
    )
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert second_body["flag"]["enabled"] is True
    assert int(second_body["flag"]["rollout_percentage"]) == 42


def test_tenant_profile_mutations_replay_contract_remains_explicit() -> None:
    from uuid import uuid4 as _uuid4
    suffix = _uuid4().hex[:8]

    created = client.post(
        "/api/v1/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": f"replay-tenant-{suffix}", "name": f"Replay Tenant {suffix}"},
    )
    assert created.status_code == 201, created.text
    tenant_id = int(created.json()["tenant_id"])

    # settings: first write → not replay; repeat → replay
    settings_first = client.patch(
        f"/api/v1/admin/tenants/{tenant_id}/settings",
        headers=ADMIN_HEADERS,
        json={"settings": {"locale": "en"}},
    )
    assert settings_first.status_code == 200, settings_first.text
    assert settings_first.json()["idempotent_replay"] is False

    settings_second = client.patch(
        f"/api/v1/admin/tenants/{tenant_id}/settings",
        headers=ADMIN_HEADERS,
        json={"settings": {"locale": "en"}},
    )
    assert settings_second.status_code == 200, settings_second.text
    assert settings_second.json()["idempotent_replay"] is True
    assert settings_second.json()["tenant"]["settings"]["locale"] == "en"

    # quotas: first write → not replay; repeat → replay
    quotas_first = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/quotas",
        headers=ADMIN_HEADERS,
        json={"values": {"api_calls": 5000}},
    )
    assert quotas_first.status_code == 200, quotas_first.text
    assert quotas_first.json()["idempotent_replay"] is False

    quotas_second = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/quotas",
        headers=ADMIN_HEADERS,
        json={"values": {"api_calls": 5000}},
    )
    assert quotas_second.status_code == 200, quotas_second.text
    assert quotas_second.json()["idempotent_replay"] is True

    # limits: first write → not replay; repeat → replay
    limits_first = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/limits",
        headers=ADMIN_HEADERS,
        json={"values": {"max_users": 50}},
    )
    assert limits_first.status_code == 200, limits_first.text
    assert limits_first.json()["idempotent_replay"] is False

    limits_second = client.put(
        f"/api/v1/admin/tenants/{tenant_id}/limits",
        headers=ADMIN_HEADERS,
        json={"values": {"max_users": 50}},
    )
    assert limits_second.status_code == 200, limits_second.text
    assert limits_second.json()["idempotent_replay"] is True


def test_ai_risk_thresholds_replay_contract_remains_explicit() -> None:
    # First write — unique values unlikely to be pre-set
    first = client.put(
        "/api/v1/admin/platform/ai/risk-thresholds",
        headers=ADMIN_HEADERS,
        json={"risk_grade_threshold": 73, "severe_risk_grade_threshold": 48},
    )
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False
    assert first_body["thresholds"]["risk_grade_threshold"] == 73
    assert first_body["thresholds"]["severe_risk_grade_threshold"] == 48

    # Repeat identical write → replay
    second = client.put(
        "/api/v1/admin/platform/ai/risk-thresholds",
        headers=ADMIN_HEADERS,
        json={"risk_grade_threshold": 73, "severe_risk_grade_threshold": 48},
    )
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert second_body["thresholds"]["risk_grade_threshold"] == 73

    # Changed value → not replay
    third = client.put(
        "/api/v1/admin/platform/ai/risk-thresholds",
        headers=ADMIN_HEADERS,
        json={"risk_grade_threshold": 65, "severe_risk_grade_threshold": 48},
    )
    assert third.status_code == 200, third.text
    assert third.json()["idempotent_replay"] is False


def test_developer_installation_and_subscription_replay_contract_remains_explicit() -> None:
    create_resp = client.post(
        "/api/v1/admin/platform/developer/apps",
        headers=ADMIN_HEADERS,
        json={
            "name": f"Replay App {uuid4().hex[:8]}",
            "description": "developer replay regression",
            "owner_email": "owner@example.com",
            "scopes": ["students.read"],
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    app_id = int(create_resp.json()["id"])

    install_first = client.post(
        f"/api/v1/admin/platform/developer/apps/{app_id}/installations",
        headers=ADMIN_HEADERS,
        json={"tenant_id": 1},
    )
    assert install_first.status_code == 201, install_first.text
    install_first_body = install_first.json()
    assert install_first_body["idempotent_replay"] is False

    install_second = client.post(
        f"/api/v1/admin/platform/developer/apps/{app_id}/installations",
        headers=ADMIN_HEADERS,
        json={"tenant_id": 1},
    )
    assert install_second.status_code == 201, install_second.text
    install_second_body = install_second.json()
    assert install_second_body["idempotent_replay"] is True
    assert int(install_second_body["installation"]["id"]) == int(install_first_body["installation"]["id"])

    subscribe_first = client.post(
        f"/api/v1/admin/platform/developer/apps/{app_id}/subscriptions",
        headers=ADMIN_HEADERS,
        json={"event_type": "student.created"},
    )
    assert subscribe_first.status_code == 201, subscribe_first.text
    subscribe_first_body = subscribe_first.json()
    assert subscribe_first_body["idempotent_replay"] is False

    subscribe_second = client.post(
        f"/api/v1/admin/platform/developer/apps/{app_id}/subscriptions",
        headers=ADMIN_HEADERS,
        json={"event_type": "student.created"},
    )
    assert subscribe_second.status_code == 201, subscribe_second.text
    subscribe_second_body = subscribe_second.json()
    assert subscribe_second_body["idempotent_replay"] is True
    assert int(subscribe_second_body["subscription"]["id"]) == int(subscribe_first_body["subscription"]["id"])


def test_federation_tenant_link_replay_contract_remains_explicit() -> None:
    institution = client.post(
        "/api/v1/admin/platform/federation/institutions",
        headers=ADMIN_HEADERS,
        json={
            "name": f"Replay Federation {uuid4().hex[:8]}",
            "code": f"FED-{uuid4().hex[:8].upper()}",
            "country": "US",
            "type": "university",
            "metadata": {},
        },
    )
    assert institution.status_code == 201, institution.text
    institution_id = int(institution.json()["institution"]["id"])

    first = client.post(
        f"/api/v1/admin/platform/federation/institutions/{institution_id}/tenants",
        headers=ADMIN_HEADERS,
        json={"tenant_id": 1, "role": "institution_admin"},
    )
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.post(
        f"/api/v1/admin/platform/federation/institutions/{institution_id}/tenants",
        headers=ADMIN_HEADERS,
        json={"tenant_id": 1, "role": "institution_admin"},
    )
    assert second.status_code == 201, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert int(second_body["member"]["id"]) == int(first_body["member"]["id"])

    third = client.post(
        f"/api/v1/admin/platform/federation/institutions/{institution_id}/tenants",
        headers=ADMIN_HEADERS,
        json={"tenant_id": 1, "role": "viewer"},
    )
    assert third.status_code == 201, third.text
    assert third.json()["idempotent_replay"] is False


def test_federation_institution_create_replay_contract_remains_explicit() -> None:
    payload = {
        "name": f"Institution Replay {uuid4().hex[:8]}",
        "code": f"INST-{uuid4().hex[:8].upper()}",
        "country": "US",
        "type": "university",
        "metadata": {"region": "west"},
    }

    first = client.post(
        "/api/v1/admin/platform/federation/institutions",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.post(
        "/api/v1/admin/platform/federation/institutions",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert second.status_code == 201, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert int(second_body["institution"]["id"]) == int(first_body["institution"]["id"])

    conflicting = client.post(
        "/api/v1/admin/platform/federation/institutions",
        headers=ADMIN_HEADERS,
        json={**payload, "name": "Different Name"},
    )
    assert conflicting.status_code == 400, conflicting.text


def test_identity_provider_upsert_replay_contract_remains_explicit() -> None:
    tenant_id = 1
    headers = {
        "Authorization": f"Bearer {create_access_token('identity-admin@example.com', ['admin'], 'test', tenant_id=tenant_id)}"
    }
    payload = {
        "provider": f"entra-{uuid4().hex[:6]}",
        "type": "oidc",
        "enabled": True,
        "issuer": "https://idp.example.com",
        "client_id": "client-123",
        "client_secret": "secret-123",
        "redirect_uri": "https://app.example.com/api/auth/oidc/callback",
        "scopes": ["openid", "profile", "email"],
        "tenant_scope": "tenant",
        "saml_metadata_url": "",
        "saml_sso_url": "",
        "saml_entity_id": "",
    }

    first = client.put(
        f"/api/admin/identity/providers/{payload['provider']}",
        headers=headers,
        json=payload,
    )
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.put(
        f"/api/admin/identity/providers/{payload['provider']}",
        headers=headers,
        json=payload,
    )
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert second_body["provider"]["provider"] == payload["provider"]

    third = client.put(
        f"/api/admin/identity/providers/{payload['provider']}",
        headers=headers,
        json={**payload, "client_id": "client-456"},
    )
    assert third.status_code == 200, third.text
    assert third.json()["idempotent_replay"] is False


def test_backup_settings_replay_contract_remains_explicit() -> None:
    marker = uuid4().hex[:8]
    profile_id = f"replay{marker}"
    payload = {
        "active_profile": profile_id,
        "retention_days": 7,
        "retention_min_files": 1,
        "profiles": [
            {
                "id": profile_id,
                "label": "Replay Profile",
                "path": f"/tmp/app-backups/{profile_id}",
            }
        ],
    }

    first = client.put("/api/admin/backups/settings", headers=ADMIN_HEADERS, json=payload)
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.put("/api/admin/backups/settings", headers=ADMIN_HEADERS, json=payload)
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert second_body["active_profile"] == profile_id

    third = client.put(
        "/api/admin/backups/settings",
        headers=ADMIN_HEADERS,
        json={**payload, "retention_days": 14},
    )
    assert third.status_code == 200, third.text
    assert third.json()["idempotent_replay"] is False


def test_education_graph_mutations_replay_contract_remains_explicit() -> None:
    tenant_id = 1
    suffix = uuid4().hex[:8]

    create_skill_first = client.post(
        "/api/v1/admin/skills",
        headers={**ADMIN_HEADERS, "X-Tenant-ID": str(tenant_id)},
        json={
            "tenant_id": tenant_id,
            "skill_key": f"calc_{suffix}",
            "name": "Calculus",
            "description": "math skill",
            "category": "Mathematics",
            "level": "intermediate",
        },
    )
    assert create_skill_first.status_code == 201, create_skill_first.text
    first_skill_body = create_skill_first.json()
    assert first_skill_body["idempotent_replay"] is False
    skill_id = int(first_skill_body["skill"]["id"])

    create_skill_second = client.post(
        "/api/v1/admin/skills",
        headers={**ADMIN_HEADERS, "X-Tenant-ID": str(tenant_id)},
        json={
            "tenant_id": tenant_id,
            "skill_key": f"calc_{suffix}",
            "name": "Calculus",
            "description": "math skill",
            "category": "Mathematics",
            "level": "intermediate",
        },
    )
    assert create_skill_second.status_code == 201, create_skill_second.text
    second_skill_body = create_skill_second.json()
    assert second_skill_body["idempotent_replay"] is True
    assert int(second_skill_body["skill"]["id"]) == skill_id

    map_first = client.post(
        "/api/v1/admin/course-skills",
        headers={**ADMIN_HEADERS, "X-Tenant-ID": str(tenant_id)},
        json={
            "tenant_id": tenant_id,
            "course_id": f"course_{suffix}",
            "skill_id": skill_id,
            "weight": 2.5,
        },
    )
    assert map_first.status_code == 201, map_first.text
    first_map_body = map_first.json()
    assert first_map_body["idempotent_replay"] is False

    map_second = client.post(
        "/api/v1/admin/course-skills",
        headers={**ADMIN_HEADERS, "X-Tenant-ID": str(tenant_id)},
        json={
            "tenant_id": tenant_id,
            "course_id": f"course_{suffix}",
            "skill_id": skill_id,
            "weight": 2.5,
        },
    )
    assert map_second.status_code == 201, map_second.text
    second_map_body = map_second.json()
    assert second_map_body["idempotent_replay"] is True


def test_automation_rule_create_replay_contract_remains_explicit() -> None:
    suffix = uuid4().hex[:8]
    tenant = client.post(
        "/api/v1/admin/tenants",
        headers=ADMIN_HEADERS,
        json={"slug": f"auto-rule-regression-{suffix}", "name": f"Auto Rule Tenant {suffix}"},
    )
    assert tenant.status_code == 201, tenant.text
    tenant_id = tenant.json()["tenant_id"]

    payload = {
        "tenant_id": tenant_id,
        "name": f"Regression Rule {suffix}",
        "event_type": "grade.submitted",
        "condition_json": {},
        "actions_json": [],
        "is_active": True,
    }

    first = client.post("/api/v1/admin/platform/automation/rules", headers=ADMIN_HEADERS, json=payload)
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["idempotent_replay"] is False

    second = client.post("/api/v1/admin/platform/automation/rules", headers=ADMIN_HEADERS, json=payload)
    assert second.status_code == 201, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert int(second_body["id"]) == int(first_body["id"])

    conflicting = client.post(
        "/api/v1/admin/platform/automation/rules",
        headers=ADMIN_HEADERS,
        json={**payload, "event_type": "enrollment.created"},
    )
    assert conflicting.status_code == 400, conflicting.text


def test_developer_app_create_replay_contract_remains_explicit(reset_shared_state) -> None:
    """ERP-QA-24: POST /platform/developer/apps must expose idempotent_replay in the 201 response."""
    payload = {
        "name": "erp-qa-24-regression-app",
        "description": "regression",
        "owner_email": "regression@example.com",
        "scopes": ["read", "write"],
    }
    first = client.post("/api/v1/admin/platform/developer/apps", headers=ADMIN_HEADERS, json=payload)
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert "idempotent_replay" in first_body, "idempotent_replay field must be present"
    assert first_body["idempotent_replay"] is False

    second = client.post("/api/v1/admin/platform/developer/apps", headers=ADMIN_HEADERS, json=payload)
    assert second.status_code == 201, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert int(second_body["id"]) == int(first_body["id"])


def test_automation_template_instantiate_replay_contract_remains_explicit(reset_shared_state) -> None:
    """ERP-QA-25: POST /platform/automation/templates/{key}/instantiate must expose idempotent_replay field."""
    payload = {"rule_name": "erp-qa-25-replay-regression", "rule_description": "regression"}
    template_key = "erp-qa-25-regression-template"

    with UnitOfWork() as uow:
        uow.automation_template_repository.create_template(
            template_key=template_key,
            title="ERP-QA-25 Regression Template",
            description="Template for replay regression test",
            category="Testing",
            event_type="enrollment.created",
            condition_json={},
            actions_json=[{"type": "send_notification", "channel": "email", "template": "welcome"}],
            conn=uow.conn,
        )

    first = client.post(
        f"/api/v1/admin/platform/automation/templates/{template_key}/instantiate",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert "idempotent_replay" in first_body, "idempotent_replay field must be present"
    assert first_body["idempotent_replay"] is False

    second = client.post(
        f"/api/v1/admin/platform/automation/templates/{template_key}/instantiate",
        headers=ADMIN_HEADERS,
        json=payload,
    )
    assert second.status_code == 201, second.text
    assert second.json()["idempotent_replay"] is True
    assert int(second.json()["id"]) == int(first_body["id"])


def test_rbac_assign_replay_contract_remains_explicit(reset_shared_state) -> None:
    """ERP-QA-26: POST /rbac/assign must expose idempotent_replay field."""
    from uuid import uuid4

    suffix = uuid4().hex[:8]
    role_name = f"erp-qa-26-regression-{suffix}"

    # Create role
    role_resp = client.post(
        "/api/admin/rbac/roles",
        headers=ADMIN_HEADERS,
        json={"name": role_name, "permissions": ["read"]},
    )
    assert role_resp.status_code == 200, role_resp.text

    user_id = f"user.erp26.reg.{suffix}@example.com"
    payload = {"user_id": user_id, "role": role_name}

    first = client.post("/api/admin/rbac/assign", headers=ADMIN_HEADERS, json=payload)
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert "idempotent_replay" in first_body, "idempotent_replay field must be present"
    assert first_body["idempotent_replay"] is False

    second = client.post("/api/admin/rbac/assign", headers=ADMIN_HEADERS, json=payload)
    assert second.status_code == 200, second.text
    assert second.json()["idempotent_replay"] is True
    assert second.json()["roles"] == first_body["roles"]


def test_service_account_create_replay_contract_remains_explicit() -> None:
    marker = uuid4().hex[:8]
    payload = {
        "name": f"svc-replay-{marker}",
        "permissions": ["admin.integrations.manage"],
        "platform_global": False,
    }

    first = client.post("/api/admin/service-accounts", headers=ADMIN_HEADERS, json=payload)
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert "idempotent_replay" in first_body, "idempotent_replay field must be present"
    assert first_body["idempotent_replay"] is False

    second = client.post("/api/admin/service-accounts", headers=ADMIN_HEADERS, json=payload)
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True


def test_job_enqueue_idempotent_replay_contract_remains_explicit() -> None:
    """ERP-QA-29: POST /api/admin/jobs top-level idempotent_replay reflects deduplicated state."""
    from app.modules.jobs import service as jobs_service

    jobs_service.clear_jobs_state()
    marker = uuid4().hex

    first = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "notify.send", "payload": {"ref": marker}, "max_retries": 1},
    )
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert "idempotent_replay" in first_body, "idempotent_replay must be a top-level field"
    assert first_body["idempotent_replay"] is False

    second = client.post(
        "/api/admin/jobs",
        headers=ADMIN_HEADERS,
        json={"job_type": "notify.send", "payload": {"ref": marker}, "max_retries": 1},
    )
    assert second.status_code == 200, second.text
    second_body = second.json()
    assert second_body["idempotent_replay"] is True
    assert int(second_body["job"]["id"]) == int(first_body["job"]["id"])


# ---------------------------------------------------------------------------
# University-domain idempotency regression tests (ERP-QA-39)
# ---------------------------------------------------------------------------
# University modules require a PostgreSQL session (no in-memory fallback).
# These tests override the DB dependency with a mock and monkeypatch service
# methods with stateful callables to verify the HTTP contract:
#   - Response includes top-level ``idempotent_replay`` field
#   - First call → replay=False, duplicate call → replay=True
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 4, 17, 12, 0, 0, tzinfo=UTC)


def _student_read_schema(*, student_id: int = 1001, tenant_id: int = 1):
    from app.modules.students.schemas import StudentProfileReadSchema

    return StudentProfileReadSchema(
        id=student_id,
        tenant_id=tenant_id,
        person_id=101,
        student_number=f"ADM-{tenant_id}-{student_id}",
        cohort_year=2026,
        academic_level=None,
        current_status="admitted",
        admission_source="admissions_workflow",
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        updated_by="owner@example.com",
        created_at=_NOW,
        updated_at=_NOW,
    )


def _binding_read_schema(*, binding_id: int = 3001, student_id: int = 1001, program_id: int = 501):
    from app.modules.students.schemas import StudentProgramBindingReadSchema

    return StudentProgramBindingReadSchema(
        id=binding_id,
        tenant_id=1,
        student_profile_id=student_id,
        program_id=program_id,
        is_primary=True,
        binding_state="active",
        started_at=_NOW,
        ended_at=None,
        metadata_json={},
        version=1,
        created_by="owner@example.com",
        updated_by="owner@example.com",
        created_at=_NOW,
        updated_at=_NOW,
    )


def _org_unit_read_schema(*, unit_id: int = 100, code: str = "ORG-1"):
    from app.modules.org_structure.schemas import OrgUnitReadSchema

    return OrgUnitReadSchema(
        id=unit_id,
        tenant_id=1,
        name="Test Faculty",
        code=code,
        unit_type="faculty",
        parent_unit_id=None,
        active=True,
        head_person_id=None,
        email=None,
        phone=None,
        location=None,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _grade_read_schema(*, grade_id: int = 5001, enrollment_id: int = 2001):
    from app.modules.grades.schemas import GradeReadSchema

    return GradeReadSchema(
        id=grade_id,
        tenant_id=1,
        enrollment_id=enrollment_id,
        grade_code="A",
        grade_points=Decimal("4.0"),
        grading_scale_id=1,
        submitted_by="owner@example.com",
        submitted_at=_NOW,
        version=1,
        metadata_json={},
    )


def _transcript_snapshot_schema(*, snapshot_id: int = 7001, student_id: int = 1001):
    from app.modules.transcripts.schemas import TranscriptSnapshotSchema

    return TranscriptSnapshotSchema(
        id=snapshot_id,
        tenant_id=1,
        student_profile_id=student_id,
        snapshot_json={"gpa": "3.5", "courses": []},
        generated_by="owner@example.com",
        generated_at=_NOW,
    )


def _override_db(dep_fn):
    """Register a mock session as dependency override and return cleanup fn."""
    mock_session = MagicMock()
    app.dependency_overrides[dep_fn] = lambda: mock_session
    return mock_session


def _cleanup_db(dep_fn):
    app.dependency_overrides.pop(dep_fn, None)


# -- students create --------------------------------------------------------

def test_students_create_replay_contract_remains_explicit(monkeypatch) -> None:
    """ERP-QA-39: POST /api/admin/students returns idempotent_replay on replay."""
    from app.modules.students.dependencies import get_students_db
    from app.modules.students.service import StudentLifecycleService

    _override_db(get_students_db)
    seen_person_ids: list[int] = []
    entity = _student_read_schema()

    async def fake_create(self, tenant_id, request, created_by):
        replay = request.person_id in seen_person_ids
        seen_person_ids.append(request.person_id)
        return MutationResult(entity=entity, idempotent_replay=replay)

    monkeypatch.setattr(StudentLifecycleService, "create_student_profile", fake_create)

    marker = uuid4().hex[:8]
    payload = {"person_id": 101, "student_number": f"S-{marker}", "cohort_year": 2026}

    try:
        first = client.post("/api/admin/students", headers=ADMIN_HEADERS, json=payload)
        assert first.status_code == 201, first.text
        assert first.json()["idempotent_replay"] is False
        assert "student" in first.json()

        second = client.post("/api/admin/students", headers=ADMIN_HEADERS, json=payload)
        assert second.status_code == 201, second.text
        assert second.json()["idempotent_replay"] is True
        assert int(second.json()["student"]["id"]) == int(first.json()["student"]["id"])
    finally:
        _cleanup_db(get_students_db)


# -- students change_status -------------------------------------------------

def test_students_change_status_replay_contract_remains_explicit(monkeypatch) -> None:
    """ERP-QA-39: PATCH /api/admin/students/{id}/status returns idempotent_replay on no-op."""
    from app.modules.students.dependencies import get_students_db
    from app.modules.students.service import StudentLifecycleService

    _override_db(get_students_db)
    call_count = [0]
    entity = _student_read_schema()

    async def fake_change(self, tenant_id, student_profile_id, request, actor_id):
        call_count[0] += 1
        return MutationResult(entity=entity, idempotent_replay=call_count[0] > 1)

    monkeypatch.setattr(StudentLifecycleService, "change_student_status", fake_change)

    try:
        first = client.patch(
            "/api/admin/students/1001/status",
            headers=ADMIN_HEADERS,
            json={"to_status": "active", "expected_version": 1},
        )
        assert first.status_code == 200, first.text
        assert first.json()["idempotent_replay"] is False

        second = client.patch(
            "/api/admin/students/1001/status",
            headers=ADMIN_HEADERS,
            json={"to_status": "active", "expected_version": 1},
        )
        assert second.status_code == 200, second.text
        assert second.json()["idempotent_replay"] is True
    finally:
        _cleanup_db(get_students_db)


# -- students program binding -----------------------------------------------

def test_students_program_binding_replay_contract_remains_explicit(monkeypatch) -> None:
    """ERP-QA-39: POST /api/admin/students/{id}/program-bindings returns idempotent_replay."""
    from app.modules.students.dependencies import get_students_db
    from app.modules.students.service import StudentLifecycleService

    _override_db(get_students_db)
    call_count = [0]
    entity = _binding_read_schema()

    async def fake_bind(self, tenant_id, request, actor_id):
        call_count[0] += 1
        return MutationResult(entity=entity, idempotent_replay=call_count[0] > 1)

    monkeypatch.setattr(StudentLifecycleService, "bind_student_to_program", fake_bind)

    try:
        first = client.post(
            "/api/admin/students/1001/program-bindings",
            headers=ADMIN_HEADERS,
            json={"student_profile_id": 1001, "program_id": 501},
        )
        assert first.status_code == 201, first.text
        assert first.json()["idempotent_replay"] is False
        assert "binding" in first.json()

        second = client.post(
            "/api/admin/students/1001/program-bindings",
            headers=ADMIN_HEADERS,
            json={"student_profile_id": 1001, "program_id": 501},
        )
        assert second.status_code == 201, second.text
        assert second.json()["idempotent_replay"] is True
        assert int(second.json()["binding"]["id"]) == int(first.json()["binding"]["id"])
    finally:
        _cleanup_db(get_students_db)


# -- org_structure create ---------------------------------------------------

def test_org_structure_create_replay_contract_remains_explicit(monkeypatch) -> None:
    """ERP-QA-39: POST /api/admin/org-units returns idempotent_replay on duplicate code."""
    from app.modules.org_structure.dependencies import get_org_structure_db
    from app.modules.org_structure import service as org_service

    _override_db(get_org_structure_db)
    seen_codes: list[str] = []
    marker = uuid4().hex[:8]
    entity = _org_unit_read_schema(code=f"FAC-{marker}")

    def fake_create(db, tenant_id, payload):
        replay = payload.code in seen_codes
        seen_codes.append(payload.code)
        return MutationResult(entity=entity, idempotent_replay=replay)

    monkeypatch.setattr(org_service, "create_org_unit", fake_create)

    payload = {"name": "Test Faculty", "code": f"FAC-{marker}", "unit_type": "faculty"}

    try:
        first = client.post("/api/admin/org-units", headers=ADMIN_HEADERS, json=payload)
        assert first.status_code == 201, first.text
        assert first.json()["idempotent_replay"] is False
        assert "unit" in first.json()

        second = client.post("/api/admin/org-units", headers=ADMIN_HEADERS, json=payload)
        assert second.status_code == 201, second.text
        assert second.json()["idempotent_replay"] is True
        assert int(second.json()["unit"]["id"]) == int(first.json()["unit"]["id"])
    finally:
        _cleanup_db(get_org_structure_db)


# -- org_structure update ---------------------------------------------------

def test_org_structure_update_replay_contract_remains_explicit(monkeypatch) -> None:
    """ERP-QA-39: PATCH /api/admin/org-units/{id} returns idempotent_replay on no-op."""
    from app.modules.org_structure.dependencies import get_org_structure_db
    from app.modules.org_structure import service as org_service

    _override_db(get_org_structure_db)
    call_count = [0]
    entity = _org_unit_read_schema()

    def fake_update(db, tenant_id, unit_id, payload):
        call_count[0] += 1
        return MutationResult(entity=entity, idempotent_replay=call_count[0] > 1)

    monkeypatch.setattr(org_service, "update_org_unit", fake_update)

    try:
        first = client.patch(
            "/api/admin/org-units/100",
            headers=ADMIN_HEADERS,
            json={"name": "Updated Faculty"},
        )
        assert first.status_code == 200, first.text
        assert first.json()["idempotent_replay"] is False

        second = client.patch(
            "/api/admin/org-units/100",
            headers=ADMIN_HEADERS,
            json={"name": "Updated Faculty"},
        )
        assert second.status_code == 200, second.text
        assert second.json()["idempotent_replay"] is True
    finally:
        _cleanup_db(get_org_structure_db)


# -- org_structure deactivate -----------------------------------------------

def test_org_structure_deactivate_replay_contract_remains_explicit(monkeypatch) -> None:
    """ERP-QA-39: DELETE /api/admin/org-units/{id} returns idempotent_replay on already-inactive."""
    from app.modules.org_structure.dependencies import get_org_structure_db
    from app.modules.org_structure import service as org_service

    _override_db(get_org_structure_db)
    call_count = [0]
    entity = _org_unit_read_schema()

    def fake_deactivate(db, tenant_id, unit_id):
        call_count[0] += 1
        return MutationResult(entity=entity, idempotent_replay=call_count[0] > 1)

    monkeypatch.setattr(org_service, "deactivate_org_unit", fake_deactivate)

    try:
        first = client.delete("/api/admin/org-units/100", headers=ADMIN_HEADERS)
        assert first.status_code == 200, first.text
        assert first.json()["idempotent_replay"] is False
        assert "unit" in first.json()

        second = client.delete("/api/admin/org-units/100", headers=ADMIN_HEADERS)
        assert second.status_code == 200, second.text
        assert second.json()["idempotent_replay"] is True
    finally:
        _cleanup_db(get_org_structure_db)


# -- grades submit ----------------------------------------------------------

def test_grades_submit_replay_contract_remains_explicit(monkeypatch) -> None:
    """ERP-QA-39: POST /api/admin/grades/submit returns idempotent_replay on duplicate enrollment."""
    from app.modules.grades.dependencies import get_grades_db
    from app.modules.grades.service import GradeLifecycleService

    _override_db(get_grades_db)
    seen_enrollments: list[int] = []
    entity = _grade_read_schema()

    async def fake_submit(self, tenant_id, request, actor_id):
        replay = request.enrollment_id in seen_enrollments
        seen_enrollments.append(request.enrollment_id)
        return MutationResult(entity=entity, idempotent_replay=replay)

    monkeypatch.setattr(GradeLifecycleService, "submit_grade", fake_submit)

    payload = {"enrollment_id": 2001, "grading_scale_id": 1, "grade_code": "A"}

    try:
        first = client.post("/api/admin/grades/submit", headers=ADMIN_HEADERS, json=payload)
        assert first.status_code == 201, first.text
        assert first.json()["idempotent_replay"] is False
        assert "grade" in first.json()

        second = client.post("/api/admin/grades/submit", headers=ADMIN_HEADERS, json=payload)
        assert second.status_code == 201, second.text
        assert second.json()["idempotent_replay"] is True
        assert int(second.json()["grade"]["id"]) == int(first.json()["grade"]["id"])
    finally:
        _cleanup_db(get_grades_db)


# -- grades change ----------------------------------------------------------

def test_grades_change_replay_contract_remains_explicit(monkeypatch) -> None:
    """ERP-QA-39: PATCH /api/admin/grades/change returns idempotent_replay on no-op."""
    from app.modules.grades.dependencies import get_grades_db
    from app.modules.grades.service import GradeLifecycleService

    _override_db(get_grades_db)
    call_count = [0]
    entity = _grade_read_schema()

    async def fake_change(self, tenant_id, request, actor_id):
        call_count[0] += 1
        return MutationResult(entity=entity, idempotent_replay=call_count[0] > 1)

    monkeypatch.setattr(GradeLifecycleService, "change_grade", fake_change)

    payload = {
        "enrollment_id": 2001,
        "grading_scale_id": 1,
        "new_grade_code": "A",
        "expected_version": 1,
    }

    try:
        first = client.patch("/api/admin/grades/change", headers=ADMIN_HEADERS, json=payload)
        assert first.status_code == 200, first.text
        assert first.json()["idempotent_replay"] is False

        second = client.patch("/api/admin/grades/change", headers=ADMIN_HEADERS, json=payload)
        assert second.status_code == 200, second.text
        assert second.json()["idempotent_replay"] is True
    finally:
        _cleanup_db(get_grades_db)


# -- transcripts snapshot ---------------------------------------------------

def test_transcripts_snapshot_replay_contract_remains_explicit(monkeypatch) -> None:
    """ERP-QA-39: POST /api/admin/students/{id}/transcript/snapshot returns idempotent_replay."""
    from app.modules.transcripts.dependencies import get_transcripts_db
    from app.modules.transcripts.service import TranscriptService

    _override_db(get_transcripts_db)
    entity = _transcript_snapshot_schema()

    async def fake_snapshot(self, tenant_id, *, student_profile_id, actor_id):
        return MutationResult(entity=entity, idempotent_replay=False)

    monkeypatch.setattr(TranscriptService, "create_transcript_snapshot", fake_snapshot)

    try:
        first = client.post(
            "/api/admin/students/1001/transcript/snapshot",
            headers=ADMIN_HEADERS,
        )
        assert first.status_code == 201, first.text
        assert "idempotent_replay" in first.json(), "idempotent_replay field must be present"
        assert first.json()["idempotent_replay"] is False
        assert "snapshot" in first.json()
    finally:
        _cleanup_db(get_transcripts_db)