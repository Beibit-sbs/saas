import pytest

from app.modules.backup.service import get_backup_settings_for_admin
from app.modules.feature_flags.service import list_flags
from app.modules.integrations.service import get_setting
from app.modules.plans.service import get_plan_by_code
from app.modules.tenants.provisioning_service import TenantProvisioningService
from app.modules.tenants.service import get_tenant_by_slug


def test_provisioning_initializes_tenant_defaults() -> None:
    result = TenantProvisioningService.create_tenant_with_defaults(
        tenant_name="Provisioning Tenant",
        admin_email="owner@tenant.example",
        plan_code="pro",
        actor="platform.owner@example.com",
    )

    tenant = result["tenant"]
    plan = result["plan"]
    expected_plan = get_plan_by_code("pro")

    assert expected_plan is not None
    assert int(tenant["plan_id"]) == int(expected_plan["id"])
    assert plan["code"] == "pro"

    tenant_id = int(tenant["id"])
    ldap_enabled = get_setting("ldap.enabled", tenant_id=tenant_id)
    assert ldap_enabled is not None
    assert ldap_enabled.value == "false"

    backups = get_backup_settings_for_admin(tenant_id=tenant_id)
    assert backups["active_profile"] == "local"
    assert len(backups["profiles"]) == 1

    flags = list_flags(tenant_id=tenant_id)
    assert len(flags) >= 1


def test_provisioning_keeps_tenants_isolated() -> None:
    tenant_a = TenantProvisioningService.create_tenant_with_defaults(
        tenant_name="Provisioning A",
        admin_email="a@tenant.example",
        plan_code="free",
        actor="platform.owner@example.com",
    )["tenant"]
    tenant_b = TenantProvisioningService.create_tenant_with_defaults(
        tenant_name="Provisioning B",
        admin_email="b@tenant.example",
        plan_code="enterprise",
        actor="platform.owner@example.com",
    )["tenant"]

    settings_a = get_backup_settings_for_admin(tenant_id=int(tenant_a["id"]))
    settings_b = get_backup_settings_for_admin(tenant_id=int(tenant_b["id"]))

    assert settings_a["profiles"][0]["path"] != settings_b["profiles"][0]["path"]


def test_provisioning_rolls_back_on_bootstrap_error(monkeypatch) -> None:
    def fail_bootstrap(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.modules.tenants.provisioning_service.save_setting", fail_bootstrap)

    with pytest.raises(RuntimeError):
        TenantProvisioningService.create_tenant_with_defaults(
            tenant_name="Rollback Tenant",
            admin_email="rollback@tenant.example",
            plan_code="free",
            actor="platform.owner@example.com",
        )

    assert get_tenant_by_slug("rollback-tenant") is None
