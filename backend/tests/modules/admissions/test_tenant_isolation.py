import pytest

from app.modules.admissions.business_rules import TenantIsolationRules
from app.modules.admissions.schemas import ApplicationCreateSchema
from app.modules.admissions.service import ApplicantService, ApplicationService

from tests.modules.admissions.conftest import ExecuteResult


@pytest.mark.parametrize("tenant_id", [None, 0, -1])
def test_tenant_id_validation_rejects_missing_or_invalid_values(tenant_id) -> None:
    if tenant_id is None:
        with pytest.raises(ValueError, match="tenant_id"):
            TenantIsolationRules.validate_tenant_id_provided(tenant_id)
    else:
        TenantIsolationRules.validate_tenant_id_provided(tenant_id)


def test_cross_tenant_applicant_lookup_fails_closed(db_session, run_async) -> None:
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)
    service = ApplicantService(db_session)

    with pytest.raises(ValueError, match="does not belong to tenant"):
        run_async(service.get_applicant(tenant_id=2, applicant_id=101))


def test_cross_tenant_application_creation_fails_closed(db_session, run_async) -> None:
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)
    service = ApplicationService(db_session)

    with pytest.raises(ValueError, match="not found in tenant"):
        run_async(
            service.create_application(
                tenant_id=2,
                request=ApplicationCreateSchema(applicant_id=101, program_id=501),
                created_by="owner@example.com",
            )
        )


def test_tenant_match_rule_raises_permission_error() -> None:
    with pytest.raises(PermissionError, match="Tenant isolation violation"):
        TenantIsolationRules.validate_tenant_match(1, 2, "applicant")