from __future__ import annotations

import pytest

from app.modules.integration_provider_readiness import EXPECTED_ENTITY_COUNT, EXPECTED_TABLE_COUNT
from app.modules.integration_provider_readiness import models


MODEL_CLASSES = models.ALL_MODELS
PRIMARY_MODELS = (
    models.ProviderRegistry,
    models.ProviderProfileVersion,
    models.ProviderCapabilityMatrix,
    models.ProviderReadinessAssessment,
    models.ProviderEvidenceItem,
    models.ProviderComplianceReview,
    models.ProviderSecurityReview,
    models.ProviderRiskRegister,
    models.ProviderAuditRecord,
    models.ProviderHealthSnapshot,
    models.ProviderIntegrationPlan,
    models.ProviderDependencyEdge,
    models.ProviderExceptionCase,
    models.ProviderStatusHistory,
    models.ProviderRoleAssignment,
    models.ProviderDashboardSnapshot,
    models.ProviderReportArtifact,
    models.ProviderPolicyViolation,
)


class TestModelInventory:
    def test_expected_entity_count(self) -> None:
        assert len(models.ENTITY_MODEL_NAMES) == EXPECTED_ENTITY_COUNT == 18

    def test_expected_table_count(self) -> None:
        assert len(models.TABLE_NAMES) == EXPECTED_TABLE_COUNT == 22

    @pytest.mark.parametrize("table_name", models.TABLE_NAMES)
    def test_table_name_prefix(self, table_name: str) -> None:
        assert table_name.startswith("ipr_")

    @pytest.mark.parametrize("model_class", PRIMARY_MODELS, ids=[cls.__name__ for cls in PRIMARY_MODELS])
    def test_model_has_tenant_id(self, model_class) -> None:
        assert "tenant_id" in model_class.__table__.columns

    @pytest.mark.parametrize("model_class", PRIMARY_MODELS, ids=[cls.__name__ for cls in PRIMARY_MODELS])
    def test_model_has_provider_id(self, model_class) -> None:
        assert "provider_id" in model_class.__table__.columns

    @pytest.mark.parametrize("model_class", PRIMARY_MODELS, ids=[cls.__name__ for cls in PRIMARY_MODELS])
    def test_model_has_readiness_only_flag(self, model_class) -> None:
        assert "readiness_only" in model_class.__table__.columns

    @pytest.mark.parametrize("model_class", PRIMARY_MODELS, ids=[cls.__name__ for cls in PRIMARY_MODELS])
    def test_model_has_provider_connected_flag(self, model_class) -> None:
        assert "provider_connected" in model_class.__table__.columns

    @pytest.mark.parametrize("model_class", PRIMARY_MODELS, ids=[cls.__name__ for cls in PRIMARY_MODELS])
    def test_model_has_credentials_stored_flag(self, model_class) -> None:
        assert "credentials_stored" in model_class.__table__.columns

    @pytest.mark.parametrize("model_class", PRIMARY_MODELS, ids=[cls.__name__ for cls in PRIMARY_MODELS])
    def test_model_has_external_submission_flag(self, model_class) -> None:
        assert "external_submission" in model_class.__table__.columns

    @pytest.mark.parametrize("model_class", PRIMARY_MODELS, ids=[cls.__name__ for cls in PRIMARY_MODELS])
    def test_model_has_fake_health_metrics_flag(self, model_class) -> None:
        assert "fake_health_metrics" in model_class.__table__.columns

    @pytest.mark.parametrize("model_class", PRIMARY_MODELS, ids=[cls.__name__ for cls in PRIMARY_MODELS])
    def test_model_has_fake_readiness_metrics_flag(self, model_class) -> None:
        assert "fake_readiness_metrics" in model_class.__table__.columns


class TestProviderRegistryShape:
    def test_provider_registry_has_owner_columns(self) -> None:
        table = models.ProviderRegistry.__table__.columns
        assert "business_owner_role" in table
        assert "technical_owner_role" in table
        assert "security_owner_role" in table

    def test_provider_registry_has_visibility_columns(self) -> None:
        table = models.ProviderRegistry.__table__.columns
        assert "auditor_visibility" in table
        assert "executive_visibility" in table
