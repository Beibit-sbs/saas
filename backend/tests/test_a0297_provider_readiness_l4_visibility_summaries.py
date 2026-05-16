"""
A-029.7 Provider Readiness L4 Read-Only Visibility Summaries — Targeted Test Suite.

Boundary:
- deterministic read-only visibility summaries only
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

from app.modules.student_information_system_integration import service as sis_svc
from app.modules.finance_erp_integration import service as finance_svc
from app.modules.government_services_integration import service as gov_svc
from app.modules.digital_signature_integration import service as sign_svc
from app.modules.regulatory_reporting_integration import service as reg_svc
from app.modules.identity_provider_integration import service as idp_svc
from app.modules.email_gateway_integration import service as email_svc
from app.modules.notification_gateway_integration import service as notif_svc
from app.modules.payment_gateway_integration import service as payment_svc
from app.modules.hr_payroll_integration import service as hr_svc
from app.modules.learning_management_system_integration import service as lms_svc

MODULE_SPECS = [
    {
        "name": "student_information_system_integration",
        "svc": sis_svc,
        "l3": "evaluate_student_information_system_provider_readiness_l3",
        "l4": "get_student_information_system_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no platonus calls",
            "no registration/grade import",
        ],
    },
    {
        "name": "finance_erp_integration",
        "svc": finance_svc,
        "l3": "evaluate_finance_erp_provider_readiness_l3",
        "l4": "get_finance_erp_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no posting",
            "no payment sync",
        ],
    },
    {
        "name": "government_services_integration",
        "svc": gov_svc,
        "l3": "evaluate_government_services_provider_readiness_l3",
        "l4": "get_government_services_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no eGov query/submission",
            "no public service request execution",
        ],
    },
    {
        "name": "digital_signature_integration",
        "svc": sign_svc,
        "l3": "evaluate_digital_signature_provider_readiness_l3",
        "l4": "get_digital_signature_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no signing",
            "no key storage",
        ],
    },
    {
        "name": "regulatory_reporting_integration",
        "svc": reg_svc,
        "l3": "evaluate_regulatory_reporting_provider_readiness_l3",
        "l4": "get_regulatory_reporting_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no ministry submission",
            "no official compliance certification claim",
        ],
    },
    {
        "name": "identity_provider_integration",
        "svc": idp_svc,
        "l3": "evaluate_identity_provider_readiness_l3",
        "l4": "get_identity_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no LDAP/AD bind",
            "no live login",
            "no token issuance",
            "no provisioning",
        ],
    },
    {
        "name": "email_gateway_integration",
        "svc": email_svc,
        "l3": "evaluate_email_gateway_provider_readiness_l3",
        "l4": "get_email_gateway_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no SMTP/API call",
            "no email send",
        ],
    },
    {
        "name": "notification_gateway_integration",
        "svc": notif_svc,
        "l3": "evaluate_notification_gateway_provider_readiness_l3",
        "l4": "get_notification_gateway_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no SMS/push/WhatsApp/Telegram send",
            "no delivery status claim",
        ],
    },
    {
        "name": "payment_gateway_integration",
        "svc": payment_svc,
        "l3": "evaluate_payment_gateway_provider_readiness_l3",
        "l4": "get_payment_gateway_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no payment initiation",
            "no capture/refund",
        ],
    },
    {
        "name": "hr_payroll_integration",
        "svc": hr_svc,
        "l3": "evaluate_hr_payroll_provider_readiness_l3",
        "l4": "get_hr_payroll_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no HR/Payroll data sync",
            "no attendance/leave writeback",
        ],
    },
    {
        "name": "learning_management_system_integration",
        "svc": lms_svc,
        "l3": "evaluate_learning_management_system_provider_readiness_l3",
        "l4": "get_learning_management_system_provider_l4_visibility_summary",
        "forbidden_phrases": [
            "no LMS roster sync",
            "no grade passback",
        ],
    },
]


REQUIRED_L4_FIELDS = {
    "tenant_id",
    "module",
    "uce_id",
    "provider_type",
    "provider_key",
    "readiness_level",
    "maturity_target",
    "visibility_source_level",
    "integration_mode",
    "provider_profile_level",
    "deterministic_logic_version",
    "visibility_version",
    "provider_connected",
    "live_calls_enabled",
    "credentials_configured",
    "external_submission_enabled",
    "sync_enabled",
    "readiness_status",
    "readiness_status_reason",
    "blocker_count",
    "warning_count",
    "missing_evidence_count",
    "visibility_summary",
    "go_live_blocker_summary",
    "missing_evidence_summary",
    "security_legal_audit_rollback_summary",
    "allowed_next_steps",
    "forbidden_actions",
    "evidence_refs",
    "go_live_blockers",
    "blocker_details",
    "warning_details",
    "missing_evidence_by_category",
    "tenant_scoped",
    "read_only",
    "no_mutation",
    "no_provider_call",
    "no_credentials",
    "no_external_submission",
    "no_provider_connected_claim",
    "no_sync_claim",
    "no_l5_claim",
    "no_l6_claim",
}


def _call_l3(spec: dict, tenant_id: int = 77) -> dict:
    return getattr(spec["svc"], spec["l3"])(tenant_id)


def _call_l4(spec: dict, tenant_id: int = 77) -> dict:
    return getattr(spec["svc"], spec["l4"])(tenant_id)


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_module_imports(spec):
    assert spec["svc"] is not None


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l4_exists(spec):
    assert hasattr(spec["svc"], spec["l4"])
    assert callable(getattr(spec["svc"], spec["l4"]))


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
@pytest.mark.parametrize("invalid_tenant", [None, 0, -1, "tenant-x"])
def test_tenant_fail_closed(spec, invalid_tenant):
    with pytest.raises((ValueError, TypeError)):
        _call_l4(spec, invalid_tenant)


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_valid_tenant_accepted(spec):
    result = _call_l4(spec, 91)
    assert result["tenant_id"] == 91


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l4_preserves_l3_profile_fields(spec):
    l3 = _call_l3(spec)
    l4 = _call_l4(spec)
    assert l4["module"] == l3["module"]
    assert l4["uce_id"] == l3["uce_id"]
    assert l4["provider_type"] == l3["provider_type"]
    assert l4["provider_key"] == l3["provider_key"]
    assert l4["readiness_status"] == l3["readiness_status"]
    assert l4["readiness_status_reason"] == l3["readiness_status_reason"]


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l4_contract_and_versions(spec):
    result = _call_l4(spec)
    assert REQUIRED_L4_FIELDS.issubset(result.keys())
    assert result["readiness_level"] == "L4_PROVIDER_READONLY_VISIBILITY"
    assert result["maturity_target"] == "L4"
    assert result["visibility_source_level"] == "L3_PROVIDER_READINESS_DETERMINISTIC_LOGIC"
    assert result["integration_mode"] == "NON_LIVE_READINESS"
    assert result["provider_profile_level"] == "L2_PROVIDER_READINESS_FOUNDATION"
    assert result["deterministic_logic_version"] == "A-029.5"
    assert result["visibility_version"] == "A-029.7"


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l4_non_live_flags_locked(spec):
    result = _call_l4(spec)
    assert result["provider_connected"] is False
    assert result["live_calls_enabled"] is False
    assert result["credentials_configured"] is False
    assert result["external_submission_enabled"] is False
    assert result["sync_enabled"] is False


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l4_anti_fake_and_read_only_flags(spec):
    result = _call_l4(spec)
    assert result["tenant_scoped"] is True
    assert result["read_only"] is True
    assert result["no_mutation"] is True
    assert result["no_provider_call"] is True
    assert result["no_credentials"] is True
    assert result["no_external_submission"] is True
    assert result["no_provider_connected_claim"] is True
    assert result["no_sync_claim"] is True
    assert result["no_l5_claim"] is True
    assert result["no_l6_claim"] is True


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l4_counts_match_l3(spec):
    l3 = _call_l3(spec)
    l4 = _call_l4(spec)
    assert l4["blocker_count"] == l3["blocker_count"]
    assert l4["warning_count"] == l3["warning_count"]
    assert l4["missing_evidence_count"] == l3["missing_evidence_count"]
    assert l4["go_live_blockers"] == l3["go_live_blockers"]
    assert l4["blocker_details"] == l3["blocker_details"]
    assert l4["warning_details"] == l3["warning_details"]
    assert l4["missing_evidence_by_category"] == l3["missing_evidence_by_category"]


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_visibility_text_fields_non_empty(spec):
    result = _call_l4(spec)
    assert isinstance(result["visibility_summary"], str)
    assert result["visibility_summary"]
    assert isinstance(result["go_live_blocker_summary"], str)
    assert result["go_live_blocker_summary"]
    assert isinstance(result["missing_evidence_summary"], str)
    assert result["missing_evidence_summary"]
    assert isinstance(result["security_legal_audit_rollback_summary"], str)
    assert result["security_legal_audit_rollback_summary"]


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_candidate_specific_forbidden_phrases_present(spec):
    result = _call_l4(spec)
    aggregate = " | ".join(result["forbidden_actions"]).lower()
    for phrase in spec["forbidden_phrases"]:
        assert phrase.lower() in aggregate


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l4_is_deterministic_same_tenant(spec):
    one = _call_l4(spec, 123)
    two = _call_l4(spec, 123)
    assert one == two


@pytest.mark.parametrize("spec", MODULE_SPECS, ids=[s["name"] for s in MODULE_SPECS])
def test_l4_evidence_refs_include_runtime(spec):
    result = _call_l4(spec)
    refs = result["evidence_refs"]
    assert isinstance(refs, list)
    assert "A-029.7-RUNTIME" in refs


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


@pytest.mark.parametrize("path", _source_file_paths(), ids=lambda p: str(p))
def test_no_db_mutation_patterns(path: Path):
    text = path.read_text(encoding="utf-8")
    banned = [".add(", ".delete(", ".commit(", "INSERT INTO", "UPDATE ", "DELETE FROM"]
    for marker in banned:
        assert marker not in text


def _read_text_if_available(name: str) -> str | None:
    for candidate in [
        Path(name),
        Path("../") / name,
        Path("../../") / name,
    ]:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    return None


def test_tracker_has_a0297_l4_metrics_anchor():
    tracker = _read_text_if_available("SBS_UB.md")
    if tracker is None:
        pytest.skip("SBS_UB.md is not mounted in this Docker test run")
    assert "A0297_provider_l4_visibility_count = 11" in tracker
    assert "provider_l4_visibility_count = 11" in tracker
    assert "provider_l4_api_route_count = 0" in tracker
    assert "PROVIDER_L4_API_ROUTES_DEFERRED_TO_A0298 = YES" in tracker


def test_tracker_provider_non_live_invariants_unchanged():
    tracker = _read_text_if_available("SBS_UB.md")
    if tracker is None:
        pytest.skip("SBS_UB.md is not mounted in this Docker test run")
    assert "provider_readiness_foundation_count = 11" in tracker
    assert "provider_l3_deterministic_logic_count = 11" in tracker
    assert "provider_live_call_count = 0" in tracker
    assert "provider_credentials_count = 0" in tracker
    assert "provider_external_submission_count = 0" in tracker
    assert "provider_connected_count = 0" in tracker
    assert "provider_sync_count = 0" in tracker


def test_tracker_ordinary_expansion_metrics_unchanged():
    tracker = _read_text_if_available("SBS_UB.md")
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


def test_runtime_report_has_a0297_result_anchor():
    report = _read_text_if_available(
        "A-029.7-RUNTIME-PROVIDER_READINESS_L4_VISIBILITY_SUMMARIES_REPORT.md"
    )
    if report is None:
        pytest.skip("A-029.7 runtime report not mounted in this Docker test run")
    assert "A-029.7-RUNTIME CLOSED" in report
    assert "provider_l4_api_route_count = 0" in report
    assert "PROVIDER_L4_API_ROUTES_DEFERRED_TO_A0298 = YES" in report
