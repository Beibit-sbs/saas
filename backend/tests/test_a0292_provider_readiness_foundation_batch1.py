"""A-029.2 targeted tests for provider readiness foundation batch 1."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
TRACKER_FILE = ROOT_DIR.parent / "SBS_UB.md"

INTEGRATIONS = [
    {
        "module": "student_information_system_integration",
        "uce_id": "UCE-024",
        "provider_type": "SIS",
        "provider_key": "PLATONUS_KZ",
        "provider_label": "Platonus Kazakhstan SIS readiness profile",
        "future_gcc_placeholder": "SA_SIS_PROVIDER",
        "function": "get_student_information_system_provider_readiness_foundation",
        "forbidden_text": [
            "no Platonus API calls",
            "no student record sync",
            "no registration mutation",
            "no grade import",
            "no transcript mutation",
            "no live credential check",
        ],
    },
    {
        "module": "finance_erp_integration",
        "uce_id": "UCE-025",
        "provider_type": "FINANCE_ERP",
        "provider_key": "ONE_C_KZ",
        "provider_label": "1C Kazakhstan finance ERP readiness profile",
        "future_gcc_placeholder": "SA_ERP_PROVIDER",
        "function": "get_finance_erp_provider_readiness_foundation",
        "forbidden_text": [
            "no 1C API calls",
            "no invoice/payment sync",
            "no accounting mutation",
            "no financial posting",
            "no credential validation",
            "no provider availability claim",
        ],
    },
    {
        "module": "government_services_integration",
        "uce_id": "UCE-030",
        "provider_type": "GOVERNMENT_SERVICES",
        "provider_key": "EGOV_KZ",
        "provider_label": "eGov Kazakhstan government services readiness profile",
        "future_gcc_placeholder": "SA_GOVERNMENT_SERVICES_PROVIDER",
        "function": "get_government_services_provider_readiness_foundation",
        "forbidden_text": [
            "no eGov calls",
            "no citizen/student data query",
            "no document status claim",
            "no external submission",
            "no credential validation",
        ],
    },
    {
        "module": "digital_signature_integration",
        "uce_id": "UCE-109",
        "provider_type": "DIGITAL_SIGNATURE",
        "provider_key": "EDS_KZ",
        "provider_label": "Kazakhstan digital signature readiness profile",
        "future_gcc_placeholder": "SA_DIGITAL_SIGNATURE_PROVIDER",
        "function": "get_digital_signature_provider_readiness_foundation",
        "forbidden_text": [
            "no signing",
            "no certificate validation",
            "no key storage",
            "no document submission",
            "no cryptographic operation",
            "no live credential check",
        ],
    },
    {
        "module": "regulatory_reporting_integration",
        "uce_id": "UCE-112",
        "provider_type": "REGULATORY_REPORTING",
        "provider_key": "MINISTRY_KZ",
        "provider_label": "Kazakhstan ministry regulatory reporting readiness profile",
        "future_gcc_placeholder": "SA_REGULATORY_REPORTING_PROVIDER",
        "function": "get_regulatory_reporting_provider_readiness_foundation",
        "forbidden_text": [
            "no ministry submission",
            "no report upload",
            "no compliance status claim",
            "no external API call",
            "no official certification claim",
        ],
    },
    {
        "module": "identity_provider_integration",
        "uce_id": "UCE-108",
        "provider_type": "IDENTITY_PROVIDER",
        "provider_key": "IDP_SSO_KZ",
        "provider_label": "Kazakhstan identity provider / SSO readiness profile",
        "future_gcc_placeholder": "SA_IDENTITY_PROVIDER",
        "function": "get_identity_provider_readiness_foundation",
        "forbidden_text": [
            "no live login",
            "no LDAP/AD bind",
            "no token issuance",
            "no user provisioning",
            "no password handling",
            "no credential validation",
        ],
    },
]

COMMON_FIELDS = {
    "tenant_id",
    "module",
    "uce_id",
    "provider_type",
    "provider_key",
    "provider_label",
    "country_profile",
    "future_gcc_placeholder",
    "readiness_level",
    "maturity_target",
    "integration_mode",
    "live_calls_enabled",
    "credentials_configured",
    "credential_reference",
    "external_submission_enabled",
    "provider_connected",
    "provider_status_claim",
    "sync_enabled",
    "readiness_summary",
    "capability_matrix",
    "required_evidence",
    "missing_configuration_evidence",
    "data_categories",
    "pii_risk_level",
    "legal_basis_required",
    "security_review_required",
    "owner_role",
    "approval_required_before_live",
    "security_requirements",
    "legal_requirements",
    "audit_requirements",
    "rollback_requirements",
    "audit_required",
    "rollback_required_before_live",
    "allowed_actions",
    "forbidden_actions",
    "tenant_scoped",
    "read_only",
    "no_mutation",
    "no_provider_call",
    "no_credentials",
    "no_external_submission",
    "no_fake_integration_status",
    "no_sync_claim",
    "no_l4_claim",
    "no_l5_claim",
    "no_l6_claim",
}


def load_service(module_name: str):
    return importlib.import_module(f"app.modules.{module_name}.service")


def read_tracker_text_or_skip() -> str:
    if not TRACKER_FILE.exists():
        pytest.skip("SBS_UB.md is not mounted in this Docker test context")
    return TRACKER_FILE.read_text(encoding="utf-8")


def foundation_for(entry: dict, tenant_id: int = 7):
    service_module = load_service(entry["module"])
    return getattr(service_module, entry["function"])(tenant_id)


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_selected_module_imports(entry):
    assert load_service(entry["module"]) is not None


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_provider_readiness_function_exists(entry):
    service_module = load_service(entry["module"])
    assert callable(getattr(service_module, entry["function"], None))


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_tenant_fail_closed_none_zero_negative_and_non_int(entry):
    service_module = load_service(entry["module"])
    with pytest.raises(ValueError):
        service_module.validate_tenant_id(None)
    with pytest.raises(ValueError):
        service_module.validate_tenant_id(0)
    with pytest.raises(ValueError):
        service_module.validate_tenant_id(-1)
    with pytest.raises(TypeError):
        service_module.validate_tenant_id("1")


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_valid_tenant_accepted(entry):
    service_module = load_service(entry["module"])
    assert service_module.validate_tenant_id(1) == 1


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_output_has_common_fields(entry):
    payload = foundation_for(entry, tenant_id=11)
    assert COMMON_FIELDS.issubset(payload.keys())


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_provider_identity_and_mode_fields(entry):
    payload = foundation_for(entry)
    assert payload["module"] == entry["module"]
    assert payload["uce_id"] == entry["uce_id"]
    assert payload["provider_type"] == entry["provider_type"]
    assert payload["provider_key"] == entry["provider_key"]
    assert payload["provider_label"] == entry["provider_label"]
    assert payload["country_profile"] == "KZ"
    assert payload["future_gcc_placeholder"] == entry["future_gcc_placeholder"]
    assert payload["readiness_level"] == "L2_PROVIDER_READINESS_FOUNDATION"
    assert payload["maturity_target"] == "L2"
    assert payload["integration_mode"] == "NON_LIVE_READINESS"


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_non_live_flags(entry):
    payload = foundation_for(entry)
    assert payload["live_calls_enabled"] is False
    assert payload["credentials_configured"] is False
    assert payload["credential_reference"] is None
    assert payload["external_submission_enabled"] is False
    assert payload["provider_connected"] is False
    assert payload["provider_status_claim"] == "NOT_CONNECTED_NON_LIVE_PROFILE_ONLY"
    assert payload["sync_enabled"] is False


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_required_collections_and_governance_fields_present(entry):
    payload = foundation_for(entry)
    assert isinstance(payload["capability_matrix"], dict)
    assert isinstance(payload["capability_matrix"].get("required_capabilities"), list)
    assert isinstance(payload["capability_matrix"].get("optional_capabilities"), list)
    assert payload["capability_matrix"]["required_capabilities"]
    assert isinstance(payload["required_evidence"], list)
    assert payload["required_evidence"]
    assert isinstance(payload["missing_configuration_evidence"], list)
    assert payload["missing_configuration_evidence"]
    assert isinstance(payload["security_requirements"], list)
    assert isinstance(payload["legal_requirements"], list)
    assert isinstance(payload["audit_requirements"], list)
    assert isinstance(payload["rollback_requirements"], list)
    assert payload["security_requirements"]
    assert payload["legal_requirements"]
    assert payload["audit_requirements"]
    assert payload["rollback_requirements"]
    assert payload["security_review_required"] is True
    assert payload["legal_basis_required"] is True
    assert payload["audit_required"] is True
    assert payload["rollback_required_before_live"] is True


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_anti_fake_flags(entry):
    payload = foundation_for(entry)
    assert payload["tenant_scoped"] is True
    assert payload["read_only"] is True
    assert payload["no_mutation"] is True
    assert payload["no_provider_call"] is True
    assert payload["no_credentials"] is True
    assert payload["no_external_submission"] is True
    assert payload["no_fake_integration_status"] is True
    assert payload["no_sync_claim"] is True
    assert payload["no_l4_claim"] is True
    assert payload["no_l5_claim"] is True
    assert payload["no_l6_claim"] is True


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_candidate_specific_forbidden_actions(entry):
    payload = foundation_for(entry)
    forbidden = payload["forbidden_actions"]
    assert isinstance(forbidden, list)
    for expected_item in entry["forbidden_text"]:
        assert expected_item in forbidden


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_deterministic_output_for_same_tenant(entry):
    left = foundation_for(entry, tenant_id=23)
    right = foundation_for(entry, tenant_id=23)
    assert left == right


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_no_external_http_libraries_in_selected_files(entry):
    service_path = ROOT_DIR / "app" / "modules" / entry["module"] / "service.py"
    text = service_path.read_text(encoding="utf-8")
    forbidden_tokens = [
        "requests.get",
        "requests.post",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "subprocess",
        "ldap3",
        "smtplib",
        "boto3",
        "zeep",
        "suds",
        "grpc",
        "openai",
        "anthropic",
    ]
    for token in forbidden_tokens:
        assert token not in text


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_no_credential_or_secret_assignments_in_selected_files(entry):
    service_path = ROOT_DIR / "app" / "modules" / entry["module"] / "service.py"
    text = service_path.read_text(encoding="utf-8").lower()
    blocked_patterns = [
        "api_key =",
        "client_secret =",
        "private_key =",
        "refresh_token =",
        "access_token =",
        "password =",
    ]
    for pattern in blocked_patterns:
        assert pattern not in text


@pytest.mark.parametrize("entry", INTEGRATIONS)
def test_no_db_mutation_or_route_behavior_in_selected_files(entry):
    service_path = ROOT_DIR / "app" / "modules" / entry["module"] / "service.py"
    text = service_path.read_text(encoding="utf-8")
    forbidden_tokens = [
        ".add(",
        ".delete(",
        ".commit(",
        "INSERT INTO",
        "UPDATE ",
        "DELETE FROM",
        "@router.",
        "APIRouter",
    ]
    for token in forbidden_tokens:
        assert token not in text


def test_tracker_baseline_extension_and_ordinary_l4_unchanged():
    tracker_text = read_tracker_text_or_skip()
    assert "L0=0" in tracker_text
    assert "L1=0" in tracker_text
    assert "L2=0" in tracker_text
    assert "L3=55" in tracker_text
    assert "L4=68" in tracker_text
    assert "L5=25" in tracker_text
    assert "L6=2" in tracker_text
    assert "maturity_arithmetic_check=PASS" in tracker_text
    assert "extension_total_count=25" in tracker_text
    assert "expansion_L4_visibility_count = 40" in tracker_text
    assert "expansion_L4_api_route_count = 40" in tracker_text
    assert "expansion_L4_consolidated_summary_count = 1" in tracker_text
    assert "expansion_L4_consolidated_candidate_count = 40" in tracker_text


def test_tracker_provider_readiness_metrics_present():
    tracker_text = read_tracker_text_or_skip()
    assert "provider_live_call_count = 0" in tracker_text
    assert "provider_credentials_count = 0" in tracker_text
    assert "provider_external_submission_count = 0" in tracker_text
    assert "provider_connected_count = 0" in tracker_text
    assert "provider_sync_count = 0" in tracker_text
