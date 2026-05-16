"""
A-029.5 Provider Readiness L3 Deterministic Logic — Targeted Test Suite.

Boundary:
- deterministic readiness logic only
- NON_LIVE_READINESS only
- no live provider calls
- no credentials
- no external submissions
- no provider connected/sync claims
- no DB mutation
- no API route or frontend behavior
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from backend.app.modules.student_information_system_integration import service as sis_svc
from backend.app.modules.finance_erp_integration import service as finance_svc
from backend.app.modules.government_services_integration import service as gov_svc
from backend.app.modules.digital_signature_integration import service as sign_svc
from backend.app.modules.regulatory_reporting_integration import service as reg_svc
from backend.app.modules.identity_provider_integration import service as idp_svc
from backend.app.modules.email_gateway_integration import service as email_svc
from backend.app.modules.notification_gateway_integration import service as notif_svc
from backend.app.modules.payment_gateway_integration import service as payment_svc
from backend.app.modules.hr_payroll_integration import service as hr_svc
from backend.app.modules.learning_management_system_integration import service as lms_svc

ALLOWED_READINESS_STATUSES = {
    "PROFILE_COMPLETE_READY_FOR_REVIEW",
    "MISSING_CAPABILITY_MAPPING",
    "MISSING_SECURITY_REVIEW",
    "MISSING_LEGAL_BASIS",
    "MISSING_AUDIT_PLAN",
    "MISSING_ROLLBACK_PLAN",
    "BLOCKED_EXTERNAL_DEPENDENCY_UNAPPROVED",
    "BLOCKED_CREDENTIALS_NOT_ALLOWED",
    "BLOCKED_LIVE_CALLS_NOT_ALLOWED",
}

ALLOWED_SEVERITIES = {
    "CRITICAL_BLOCKER",
    "HIGH_BLOCKER",
    "MEDIUM_WARNING",
    "INFO_GAP",
}

ALLOWED_MISSING_EVIDENCE_CATEGORIES = {
    "CAPABILITY_MAPPING",
    "SECURITY_REVIEW",
    "LEGAL_BASIS",
    "DATA_PROTECTION",
    "AUDIT_PLAN",
    "ROLLBACK_PLAN",
    "OWNER_APPROVAL",
    "EXTERNAL_CONTRACT",
    "SANDBOX_POLICY",
    "MONITORING_PLAN",
}

FORBIDDEN_STATUS_WORDS = {
    "connected",
    "synced",
    "submitted",
    "successful",
    "available",
    "production",
}

MODULE_SPECS = [
    {
        "name": "student_information_system_integration",
        "svc": sis_svc,
        "l2": "get_student_information_system_provider_readiness_foundation",
        "l3": "evaluate_student_information_system_provider_readiness_l3",
        "blockers": [
            "student identity mapping",
            "registration mapping",
            "data protection review",
            "contract/legal basis",
            "credential allowed",
        ],
    },
    {
        "name": "finance_erp_integration",
        "svc": finance_svc,
        "l2": "get_finance_erp_provider_readiness_foundation",
        "l3": "evaluate_finance_erp_provider_readiness_l3",
        "blockers": [
            "account mapping",
            "reconciliation rules",
            "financial audit plan",
            "legal/procurement authorization",
            "credentials or postings",
        ],
    },
    {
        "name": "government_services_integration",
        "svc": gov_svc,
        "l2": "get_government_services_provider_readiness_foundation",
        "l3": "evaluate_government_services_provider_readiness_l3",
        "blockers": [
            "egov legal basis",
            "consent/data access boundary",
            "request mapping",
            "external approval",
            "query/submission",
        ],
    },
    {
        "name": "digital_signature_integration",
        "svc": sign_svc,
        "l2": "get_digital_signature_provider_readiness_foundation",
        "l3": "evaluate_digital_signature_provider_readiness_l3",
        "blockers": [
            "certificate validation policy",
            "signing authority model",
            "key management/security review",
            "non-repudiation audit plan",
            "signing/key storage",
        ],
    },
    {
        "name": "regulatory_reporting_integration",
        "svc": reg_svc,
        "l2": "get_regulatory_reporting_provider_readiness_foundation",
        "l3": "evaluate_regulatory_reporting_provider_readiness_l3",
        "blockers": [
            "report schema mapping",
            "evidence lineage",
            "submission approval workflow",
            "legal basis",
            "ministry submission",
        ],
    },
    {
        "name": "identity_provider_integration",
        "svc": idp_svc,
        "l2": "get_identity_provider_readiness_foundation",
        "l3": "evaluate_identity_provider_readiness_l3",
        "blockers": [
            "identity claim mapping",
            "role/group mapping",
            "sso protocol boundary",
            "provisioning policy",
            "ldap/ad bind",
        ],
    },
    {
        "name": "email_gateway_integration",
        "svc": email_svc,
        "l2": "get_email_gateway_provider_readiness_foundation",
        "l3": "evaluate_email_gateway_provider_readiness_l3",
        "blockers": [
            "sender identity policy",
            "template approval boundary",
            "consent/unsubscribe boundary",
            "delivery audit design",
            "email send",
        ],
    },
    {
        "name": "notification_gateway_integration",
        "svc": notif_svc,
        "l2": "get_notification_gateway_provider_readiness_foundation",
        "l3": "evaluate_notification_gateway_provider_readiness_l3",
        "blockers": [
            "consent mapping",
            "delivery retry policy",
            "template approval",
            "phone data protection review",
            "sms/push/whatsapp",
        ],
    },
    {
        "name": "payment_gateway_integration",
        "svc": payment_svc,
        "l2": "get_payment_gateway_provider_readiness_foundation",
        "l3": "evaluate_payment_gateway_provider_readiness_l3",
        "blockers": [
            "payment initiation policy",
            "pci/data-minimization review",
            "reconciliation model",
            "refund/capture boundary",
            "payment processing",
        ],
    },
    {
        "name": "hr_payroll_integration",
        "svc": hr_svc,
        "l2": "get_hr_payroll_provider_readiness_foundation",
        "l3": "evaluate_hr_payroll_provider_readiness_l3",
        "blockers": [
            "employee identity mapping",
            "payroll posting boundary",
            "compensation data protection review",
            "hr legal basis",
            "salary calculation",
        ],
    },
    {
        "name": "learning_management_system_integration",
        "svc": lms_svc,
        "l2": "get_learning_management_system_provider_readiness_foundation",
        "l3": "evaluate_learning_management_system_provider_readiness_l3",
        "blockers": [
            "course/user mapping",
            "grade import/export policy",
            "attendance sync boundary",
            "content publication boundary",
            "sync/publish/import/export",
        ],
    },
]


def _call_l2(spec: dict, tenant_id: int = 77) -> dict:
    return getattr(spec["svc"], spec["l2"])(tenant_id)


def _call_l3(spec: dict, tenant_id: int = 77) -> dict:
    return getattr(spec["svc"], spec["l3"])(tenant_id)


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_module_imports(spec):
    assert spec["svc"] is not None


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l2_exists(spec):
    assert hasattr(spec["svc"], spec["l2"])
    assert callable(getattr(spec["svc"], spec["l2"]))


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l3_exists(spec):
    assert hasattr(spec["svc"], spec["l3"])
    assert callable(getattr(spec["svc"], spec["l3"]))


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
@pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "t-1"])
def test_tenant_fail_closed(spec, invalid_tenant):
    with pytest.raises((ValueError, TypeError)):
        _call_l3(spec, invalid_tenant)


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_valid_tenant_accepted(spec):
    result = _call_l3(spec, 91)
    assert result["tenant_id"] == 91


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l3_preserves_l2_profile_fields(spec):
    l2 = _call_l2(spec)
    l3 = _call_l3(spec)
    assert l3["module"] == l2["module"]
    assert l3["uce_id"] == l2["uce_id"]
    assert l3["provider_type"] == l2["provider_type"]
    assert l3["provider_key"] == l2["provider_key"]


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l3_contract_fields(spec):
    result = _call_l3(spec)
    assert result["readiness_level"] == "L3_PROVIDER_READINESS_DETERMINISTIC_LOGIC"
    assert result["maturity_target"] == "L3"
    assert result["integration_mode"] == "NON_LIVE_READINESS"
    assert result["provider_profile_level"] == "L2_PROVIDER_READINESS_FOUNDATION"
    assert result["deterministic_logic_version"] == "A-029.5"


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_readiness_status_allowed_and_safe(spec):
    result = _call_l3(spec)
    status = result["readiness_status"]
    assert status in ALLOWED_READINESS_STATUSES
    lowered = status.lower()
    for word in FORBIDDEN_STATUS_WORDS:
        assert word not in lowered


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_readiness_reason_and_counts_present(spec):
    result = _call_l3(spec)
    assert isinstance(result["readiness_status_reason"], str)
    assert result["readiness_status_reason"]
    assert isinstance(result["blocker_count"], int)
    assert isinstance(result["warning_count"], int)
    assert isinstance(result["missing_evidence_count"], int)
    assert result["blocker_count"] >= 1


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_completeness_fields_present(spec):
    result = _call_l3(spec)
    assert result["security_completeness_status"] in {"INCOMPLETE", "COMPLETE"}
    assert result["legal_completeness_status"] in {"INCOMPLETE", "COMPLETE"}
    assert result["audit_completeness_status"] in {"INCOMPLETE", "COMPLETE"}
    assert result["rollback_completeness_status"] in {"INCOMPLETE", "COMPLETE"}
    assert result["capability_coverage_status"] in {"PARTIAL", "COMPLETE"}


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_go_live_and_evidence_collections_present(spec):
    result = _call_l3(spec)
    assert isinstance(result["go_live_blockers"], list)
    assert result["go_live_blockers"]
    assert isinstance(result["missing_evidence_by_category"], list)
    assert result["missing_evidence_by_category"]
    assert isinstance(result["readiness_recommendations"], list)
    assert result["readiness_recommendations"]
    assert isinstance(result["allowed_next_steps"], list)
    assert result["allowed_next_steps"]
    assert isinstance(result["forbidden_actions"], list)
    assert result["forbidden_actions"]


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_blocker_and_warning_schema(spec):
    result = _call_l3(spec)
    blockers = result["blocker_details"]
    warnings = result["warning_details"]
    assert len(blockers) == result["blocker_count"]
    assert len(warnings) == result["warning_count"]

    for item in blockers:
        assert item["severity"] in ALLOWED_SEVERITIES
        assert item["category"] in ALLOWED_MISSING_EVIDENCE_CATEGORIES
        assert isinstance(item["blocker"], str) and item["blocker"]

    for item in warnings:
        assert item["severity"] in ALLOWED_SEVERITIES
        assert item["category"] in ALLOWED_MISSING_EVIDENCE_CATEGORIES
        assert isinstance(item["warning"], str) and item["warning"]

    for category in result["missing_evidence_by_category"]:
        assert category in ALLOWED_MISSING_EVIDENCE_CATEGORIES


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_anti_live_flags(spec):
    result = _call_l3(spec)
    assert result["tenant_scoped"] is True
    assert result["read_only"] is True
    assert result["no_mutation"] is True
    assert result["no_provider_call"] is True
    assert result["no_credentials"] is True
    assert result["no_external_submission"] is True
    assert result["no_provider_connected_claim"] is True
    assert result["no_sync_claim"] is True
    assert result["no_l4_claim"] is True
    assert result["no_l5_claim"] is True
    assert result["no_l6_claim"] is True


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_deterministic_output_same_tenant(spec):
    one = _call_l3(spec, 123)
    two = _call_l3(spec, 123)
    assert one == two


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_candidate_specific_blockers_present(spec):
    result = _call_l3(spec)
    aggregate = " | ".join(result["go_live_blockers"]).lower()
    for phrase in spec["blockers"]:
        assert phrase.lower() in aggregate


def _source_file_paths() -> list[Path]:
    backend_root = Path(__file__).resolve().parents[1]
    return [
        backend_root / "app/modules/student_information_system_integration/service.py",
        backend_root / "app/modules/finance_erp_integration/service.py",
        backend_root / "app/modules/government_services_integration/service.py",
        backend_root / "app/modules/digital_signature_integration/service.py",
        backend_root / "app/modules/regulatory_reporting_integration/service.py",
        backend_root / "app/modules/identity_provider_integration/service.py",
        backend_root / "app/modules/email_gateway_integration/service.py",
        backend_root / "app/modules/notification_gateway_integration/service.py",
        backend_root / "app/modules/payment_gateway_integration/service.py",
        backend_root / "app/modules/hr_payroll_integration/service.py",
        backend_root / "app/modules/learning_management_system_integration/service.py",
    ]


@pytest.mark.parametrize("path", _source_file_paths(), ids=lambda p: str(p))
def test_no_provider_http_libraries(path: Path):
    text = path.read_text(encoding="utf-8")
    banned = [
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
    for marker in banned:
        assert marker not in text


@pytest.mark.parametrize("path", _source_file_paths(), ids=lambda p: str(p))
def test_no_secret_assignments(path: Path):
    text = path.read_text(encoding="utf-8")
    # Boundary strings are allowed, but explicit secret material assignments are not.
    bad_assignments = [
        r"password\s*=\s*['\"]",
        r"api_key\s*=\s*['\"]",
        r"client_secret\s*=\s*['\"]",
        r"private_key\s*=\s*['\"]",
        r"refresh_token\s*=\s*['\"]",
        r"access_token\s*=\s*['\"]",
    ]
    for pattern in bad_assignments:
        assert re.search(pattern, text) is None


@pytest.mark.parametrize("path", _source_file_paths()[:-1], ids=lambda p: str(p))
def test_no_db_mutation_patterns(path: Path):
    text = path.read_text(encoding="utf-8")
    banned = [".add(", ".delete(", ".commit(", "INSERT INTO", "UPDATE ", "DELETE FROM"]
    for marker in banned:
        assert marker not in text


def _read_tracker_if_available() -> str | None:
    for candidate in [
        Path("SBS_UB.md"),
        Path("../SBS_UB.md"),
        Path("../../SBS_UB.md"),
    ]:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    return None


def test_tracker_has_a0295_l3_metrics_anchor():
    tracker = _read_tracker_if_available()
    if tracker is None:
        pytest.skip("SBS_UB.md is not mounted in this Docker test run")
    assert "A0295_provider_l3_deterministic_logic_count = 11" in tracker
    assert "provider_l3_deterministic_logic_count = 11" in tracker


def test_tracker_foundation_and_boundary_metrics_unchanged():
    tracker = _read_tracker_if_available()
    if tracker is None:
        pytest.skip("SBS_UB.md is not mounted in this Docker test run")
    assert "provider_readiness_foundation_count = 11" in tracker
    assert "provider_live_call_count = 0" in tracker
    assert "provider_credentials_count = 0" in tracker
    assert "provider_external_submission_count = 0" in tracker
    assert "provider_connected_count = 0" in tracker
    assert "provider_sync_count = 0" in tracker


def test_tracker_l4_and_baseline_extension_unchanged():
    tracker = _read_tracker_if_available()
    if tracker is None:
        pytest.skip("SBS_UB.md is not mounted in this Docker test run")
    assert "expansion_L4_visibility_count = 40" in tracker
    assert "expansion_L4_api_route_count = 40" in tracker
    assert "expansion_L4_consolidated_summary_count = 1" in tracker
    assert "expansion_L4_consolidated_candidate_count = 40" in tracker
    assert "expansion_L3_logic_count = 50" in tracker
    assert "remaining_L2_only = 17" in tracker
    assert "remaining_L3_not_L4 = 10" in tracker
    assert "expansion_L2_foundation_count = 67" in tracker
    assert "expansion_runtime_implemented_count = 67" in tracker
    assert "L0=0" in tracker
    assert "L1=0" in tracker
    assert "L2=0" in tracker
    assert "L3=55" in tracker
    assert "L4=68" in tracker
    assert "L5=25" in tracker
    assert "L6=2" in tracker
    assert "extension_total_count=25" in tracker
    assert "baseline_impact = 0" in tracker
    assert "extension_impact = 0" in tracker


def test_no_route_or_frontend_behavior_in_scope():
    for spec in MODULE_SPECS:
        result = _call_l3(spec)
        assert result["readiness_level"].startswith("L3_")
        assert result["integration_mode"] == "NON_LIVE_READINESS"
        assert result["no_l4_claim"] is True
        assert result["no_l5_claim"] is True
        assert result["no_l6_claim"] is True
