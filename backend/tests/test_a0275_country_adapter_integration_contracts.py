"""A-027.5 targeted tests for country-adapter-ready integration contracts."""

from __future__ import annotations

import importlib
import inspect

import pytest

INTEGRATIONS = [
    {
        "module": "student_information_system_integration",
        "original_uce_id": "UCE-024",
        "original_candidate_name": "platonus_integration",
        "kz_profile": "PLATONUS_KZ",
        "sa_placeholder": "SA_SIS_PROVIDER",
    },
    {
        "module": "finance_erp_integration",
        "original_uce_id": "UCE-025",
        "original_candidate_name": "one_c_integration",
        "kz_profile": "ONE_C_KZ",
        "sa_placeholder": "SA_ERP_PROVIDER",
    },
    {
        "module": "government_services_integration",
        "original_uce_id": "UCE-030",
        "original_candidate_name": "egov_integration",
        "kz_profile": "EGOV_KZ",
        "sa_placeholder": "SA_GOVERNMENT_SERVICES_PROVIDER",
    },
    {
        "module": "regulatory_reporting_integration",
        "original_uce_id": "UCE-112",
        "original_candidate_name": "ministry_reporting_integration",
        "kz_profile": "MINISTRY_KZ",
        "sa_placeholder": "SA_REGULATORY_REPORTING_PROVIDER",
    },
    {
        "module": "digital_signature_integration",
        "original_uce_id": "UCE-109",
        "original_candidate_name": "eds_signature_integration",
        "kz_profile": "EDS_KZ",
        "sa_placeholder": "SA_DIGITAL_SIGNATURE_PROVIDER",
    },
    {
        "module": "payment_gateway_integration",
        "original_uce_id": "UCE-110",
        "original_candidate_name": "payment_gateway_integration",
        "kz_profile": "PAYMENT_GATEWAY_KZ",
        "sa_placeholder": "SA_PAYMENT_PROVIDER",
    },
    {
        "module": "notification_gateway_integration",
        "original_uce_id": "UCE-028",
        "original_candidate_name": "sms_gateway_integration",
        "kz_profile": "SMS_GATEWAY_KZ",
        "sa_placeholder": "SA_SMS_PROVIDER",
    },
    {
        "module": "email_gateway_integration",
        "original_uce_id": "UCE-027",
        "original_candidate_name": "email_gateway_integration",
        "kz_profile": "EMAIL_GATEWAY_KZ",
        "sa_placeholder": "SA_EMAIL_PROVIDER",
    },
    {
        "module": "learning_management_system_integration",
        "original_uce_id": "UCE-106",
        "original_candidate_name": "lms_integration",
        "kz_profile": "LMS_KZ",
        "sa_placeholder": "SA_LMS_PROVIDER",
    },
    {
        "module": "identity_provider_integration",
        "original_uce_id": "UCE-108",
        "original_candidate_name": "idp_sso_integration",
        "kz_profile": "IDP_SSO_KZ",
        "sa_placeholder": "SA_IDENTITY_PROVIDER",
    },
    {
        "module": "hr_payroll_integration",
        "original_uce_id": "UCE-113",
        "original_candidate_name": "hr_payroll_system_integration",
        "kz_profile": "HR_PAYROLL_KZ",
        "sa_placeholder": "SA_HR_PAYROLL_PROVIDER",
    },
]


def load_service(module_name: str):
    return importlib.import_module(f"app.modules.{module_name}.service")


def load_package(module_name: str):
    return importlib.import_module(f"app.modules.{module_name}")


def contract_for(module_name: str, tenant_id: int = 1):
    service_module = load_service(module_name)
    func = getattr(service_module, f"get_{module_name}_integration_contract")
    return func(tenant_id)


# 1. Import validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_import_service_module(entry):
    assert load_service(entry["module"]) is not None


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_import_package_module(entry):
    assert load_package(entry["module"]) is not None


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_foundation_function_exists_and_callable(entry):
    service_module = load_service(entry["module"])
    func = getattr(service_module, f"get_{entry['module']}_integration_contract", None)
    assert callable(func)


# 2. Package metadata validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_package_metadata_constants(entry):
    package_module = load_package(entry["module"])
    assert package_module.MODULE_NAME == entry["module"]
    assert package_module.ORIGINAL_UCE_ID == entry["original_uce_id"]
    assert package_module.ORIGINAL_CANDIDATE_NAME == entry["original_candidate_name"]
    assert package_module.TARGET_LEVEL == "L2"
    assert package_module.CONTRACT_VERSION == "A-027.5"
    assert package_module.COUNTRY_ADAPTER_READY is True
    assert package_module.LIVE_PROVIDER_CALLS_ALLOWED is False


# 3. Tenant fail-closed validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_tenant_none_rejected(entry):
    service_module = load_service(entry["module"])
    with pytest.raises(ValueError):
        service_module.validate_tenant_id(None)


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_tenant_zero_rejected(entry):
    service_module = load_service(entry["module"])
    with pytest.raises(ValueError):
        service_module.validate_tenant_id(0)


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_tenant_negative_rejected(entry):
    service_module = load_service(entry["module"])
    with pytest.raises(ValueError):
        service_module.validate_tenant_id(-1)


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_tenant_positive_accepted(entry):
    service_module = load_service(entry["module"])
    assert service_module.validate_tenant_id(1) == 1


# 4. Integration contract output validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_contract_output_shape(entry):
    contract = contract_for(entry["module"], tenant_id=1)
    assert isinstance(contract, dict)
    assert contract["tenant_id"] == 1
    assert contract["module"] == entry["module"]
    assert contract["original_uce_id"] == entry["original_uce_id"]
    assert contract["original_candidate_name"] == entry["original_candidate_name"]
    assert contract["maturity_level"] == "L2"
    assert contract["expansion_layer"] == "university_completeness"
    assert contract["contract_status"] == "CONTRACT_READY"
    assert contract["country_adapter_ready"] is True
    assert contract["live_provider_call_allowed"] is False
    assert contract["credentials_required_for_contract"] is False
    assert contract["tenant_scoped"] is True
    assert contract["deterministic"] is True


# 5. Provider profile validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_provider_profile_metadata(entry):
    contract = contract_for(entry["module"])
    assert contract["provider_profiles"]
    assert contract["default_country_code"] == "KZ"
    assert contract["default_provider_profile"] == entry["kz_profile"]
    assert contract["future_provider_profile_placeholders"]
    assert entry["sa_placeholder"] in contract["future_provider_profile_placeholders"]
    assert "KZ" in contract["supported_country_codes"]
    assert "SA" in contract["future_supported_country_codes"]


# 6. Credential boundary validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_credential_boundary(entry):
    contract = contract_for(entry["module"])
    boundary = contract["credential_boundary"]
    assert isinstance(boundary, dict)
    assert contract["credentials_required_for_contract"] is False
    assert boundary["credentials_required_for_contract"] is False
    assert boundary["credential_material_allowed"] is False
    assert boundary["credential_values_exposed"] is False
    assert boundary["production_credential_usage"] is False
    payload_text = str(contract).lower()
    assert "api_key" not in payload_text
    assert "password" not in payload_text
    assert "token=" not in payload_text
    assert contract["safety_flags"]["no_credential_use"] is True
    assert contract["safety_flags"]["no_secret_storage"] is True


# 7. Provider boundary / no-live-call validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_provider_boundary_and_no_live_call(entry):
    contract = contract_for(entry["module"])
    provider_boundary = contract["provider_boundary"]
    assert isinstance(provider_boundary, dict)
    assert contract["live_provider_call_allowed"] is False
    assert provider_boundary["live_provider_call_allowed"] is False
    assert provider_boundary["provider_io_allowed"] is False
    assert provider_boundary["provider_data_access_allowed"] is False
    assert provider_boundary["provider_success_claim_allowed"] is False
    forbidden = contract["forbidden_actions"]
    assert any(action.startswith("LIVE_") for action in forbidden)
    assert contract["safety_flags"]["no_provider_call"] is True
    assert contract["safety_flags"]["no_live_integration_claim"] is True
    assert contract["safety_flags"]["no_fake_success"] is True


# 8. Failure mode validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_failure_modes(entry):
    contract = contract_for(entry["module"])
    modes = contract["expected_failure_modes"]
    assert modes
    mode_text = "|".join(modes).lower()
    assert "unavailable" in mode_text
    assert (
        "credential" in mode_text
        or "key_boundary_not_configured" in mode_text
        or "consent_missing" in mode_text
        or "sender_domain_not_verified" in mode_text
        or "role_mapping_not_approved" in mode_text
        or "salary_boundary_not_approved" in mode_text
        or "grade_boundary_not_approved" in mode_text
        or "approval_missing" in mode_text
    )
    assert (
        "mapping" in mode_text
        or "missing" in mode_text
        or "not_approved" in mode_text
        or "template" in mode_text
        or "not_verified" in mode_text
        or "not_authorized" in mode_text
        or "not_configured" in mode_text
    )


# 9. Allowed/forbidden action validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_allowed_forbidden_actions(entry):
    contract = contract_for(entry["module"])
    allowed = contract["allowed_actions"]
    forbidden = contract["forbidden_actions"]
    assert allowed
    assert forbidden
    assert any(action.startswith("LIVE_") for action in forbidden)
    blocked_prefixes = (
        "AUTO_SYNC",
        "AUTO_SUBMIT",
        "AUTO_SIGN",
        "AUTO_SEND",
        "AUTO_PROVISION",
        "AUTO_CHARGE",
        "AUTO_REFUND",
        "AUTO_RECONCILE",
        "AUTO_VERIFY",
        "AUTO_MUTATE",
    )
    assert any(action.startswith(blocked_prefixes) for action in forbidden)


# 10. Country-adapter boundary validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_country_adapter_boundary(entry):
    contract = contract_for(entry["module"])
    assert contract["country_adapter_ready"] is True
    assert contract["safety_flags"]["no_country_hardcode_in_core"] is True
    assert entry["kz_profile"] in contract["provider_profiles"]
    assert entry["sa_placeholder"] in contract["future_provider_profile_placeholders"]
    non_generic_tokens = ["platonus", "one_c", "egov", "ministry", "eds", "idp_sso"]
    if entry["module"] in {
        "student_information_system_integration",
        "finance_erp_integration",
        "government_services_integration",
        "regulatory_reporting_integration",
        "digital_signature_integration",
        "identity_provider_integration",
        "learning_management_system_integration",
        "notification_gateway_integration",
        "hr_payroll_integration",
    }:
        assert not any(token in entry["module"] for token in non_generic_tokens)


# 11. Safety flags validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_safety_flags(entry):
    flags = contract_for(entry["module"])["safety_flags"]
    assert flags["no_api_claim"] is True
    assert flags["no_frontend_claim"] is True
    assert flags["no_live_integration_claim"] is True
    assert flags["no_provider_call"] is True
    assert flags["no_credential_use"] is True
    assert flags["no_secret_storage"] is True
    assert flags["no_fake_success"] is True
    assert flags["no_external_side_effects"] is True
    assert flags["no_kpi_claim"] is True
    assert flags["no_brain_claim"] is True
    assert flags["no_autonomous_execution"] is True
    assert flags["no_country_hardcode_in_core"] is True
    assert flags["country_adapter_ready"] is True
    assert flags["no_l3_claim"] is True
    assert flags["no_l4_claim"] is True
    assert flags["no_l5_claim"] is True
    assert flags["no_l6_claim"] is True


# 12. Determinism validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_determinism(entry):
    module_name = entry["module"]
    one = contract_for(module_name, tenant_id=1)
    two = contract_for(module_name, tenant_id=1)
    assert one == two


# 13. Anti-inflation validation
@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_no_forbidden_runtime_patterns(entry):
    service_module = load_service(entry["module"])
    source_text = inspect.getsource(service_module)
    forbidden_tokens = [
        "APIRouter",
        "@router",
        "@app.get",
        "@app.post",
        "publish_event",
        "execute_brain",
        "brain_execute",
        "requests.post",
        "httpx",
        "aiohttp",
        "openai",
        "llm",
    ]
    for token in forbidden_tokens:
        assert token not in source_text


def test_a0275_batch_size_is_11():
    assert len(INTEGRATIONS) == 11
