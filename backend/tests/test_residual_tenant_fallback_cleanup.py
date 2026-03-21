import pytest

from app.modules.backup import service as backup_service
from app.modules.feature_flags import service as feature_flags_service
from app.modules.integrations import service as integrations_service


pytestmark = pytest.mark.security_regression


def test_backup_service_requires_explicit_tenant_id() -> None:
    with pytest.raises(ValueError, match="tenant_id is required"):
        backup_service.get_backup_settings_for_admin()


def test_feature_flags_service_requires_explicit_tenant_id() -> None:
    with pytest.raises(ValueError, match="tenant_id is required"):
        feature_flags_service.list_flags()


def test_integrations_admin_wrappers_require_explicit_tenant_id() -> None:
    with pytest.raises(ValueError, match="tenant_id is required"):
        integrations_service.get_ldap_config_for_admin()

    with pytest.raises(ValueError, match="tenant_id is required"):
        integrations_service.list_ai_provider_config_for_admin()