"""
A-029.8-RUNTIME — Provider Readiness L4 Read-Only API Routes

Scope:
- 11 provider-readiness L4 summary routes
- GET only
- read-only
- tenant-safe
- RBAC protected
- NON_LIVE_READINESS only
- no live provider calls / credentials / sync / external submission
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.token_service import create_access_token
from tests.conftest import ADMIN_HEADERS


ROUTE_CONFIGS = [
    {
        "uce_id": "UCE-024",
        "candidate": "student_information_system_integration",
        "provider_type": "SIS",
        "provider_key": "PLATONUS_KZ",
        "module_path": "app.modules.student_information_system_integration.service",
        "l4_func": "get_student_information_system_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/student-information-system/summary",
    },
    {
        "uce_id": "UCE-025",
        "candidate": "finance_erp_integration",
        "provider_type": "FINANCE_ERP",
        "provider_key": "ONE_C_KZ",
        "module_path": "app.modules.finance_erp_integration.service",
        "l4_func": "get_finance_erp_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/finance-erp/summary",
    },
    {
        "uce_id": "UCE-030",
        "candidate": "government_services_integration",
        "provider_type": "GOVERNMENT_SERVICES",
        "provider_key": "EGOV_KZ",
        "module_path": "app.modules.government_services_integration.service",
        "l4_func": "get_government_services_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/government-services/summary",
    },
    {
        "uce_id": "UCE-109",
        "candidate": "digital_signature_integration",
        "provider_type": "DIGITAL_SIGNATURE",
        "provider_key": "EDS_KZ",
        "module_path": "app.modules.digital_signature_integration.service",
        "l4_func": "get_digital_signature_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/digital-signature/summary",
    },
    {
        "uce_id": "UCE-112",
        "candidate": "regulatory_reporting_integration",
        "provider_type": "REGULATORY_REPORTING",
        "provider_key": "MINISTRY_KZ",
        "module_path": "app.modules.regulatory_reporting_integration.service",
        "l4_func": "get_regulatory_reporting_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/regulatory-reporting/summary",
    },
    {
        "uce_id": "UCE-108",
        "candidate": "identity_provider_integration",
        "provider_type": "IDENTITY_PROVIDER",
        "provider_key": "IDP_SSO_KZ",
        "module_path": "app.modules.identity_provider_integration.service",
        "l4_func": "get_identity_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/identity-provider/summary",
    },
    {
        "uce_id": "UCE-027",
        "candidate": "email_gateway_integration",
        "provider_type": "EMAIL_GATEWAY",
        "provider_key": "EMAIL_GATEWAY_KZ",
        "module_path": "app.modules.email_gateway_integration.service",
        "l4_func": "get_email_gateway_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/email-gateway/summary",
    },
    {
        "uce_id": "UCE-028",
        "candidate": "notification_gateway_integration",
        "provider_type": "NOTIFICATION_SMS_GATEWAY",
        "provider_key": "SMS_GATEWAY_KZ",
        "module_path": "app.modules.notification_gateway_integration.service",
        "l4_func": "get_notification_gateway_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/notification-gateway/summary",
    },
    {
        "uce_id": "UCE-110",
        "candidate": "payment_gateway_integration",
        "provider_type": "PAYMENT_GATEWAY",
        "provider_key": "PAYMENT_GATEWAY_KZ",
        "module_path": "app.modules.payment_gateway_integration.service",
        "l4_func": "get_payment_gateway_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/payment-gateway/summary",
    },
    {
        "uce_id": "UCE-113",
        "candidate": "hr_payroll_integration",
        "provider_type": "HR_PAYROLL",
        "provider_key": "HR_PAYROLL_KZ",
        "module_path": "app.modules.hr_payroll_integration.service",
        "l4_func": "get_hr_payroll_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/hr-payroll/summary",
    },
    {
        "uce_id": "UCE-106",
        "candidate": "learning_management_system_integration",
        "provider_type": "LMS",
        "provider_key": "LMS_KZ",
        "module_path": "app.modules.learning_management_system_integration.service",
        "l4_func": "get_learning_management_system_provider_l4_visibility_summary",
        "route": "/api/admin/provider-readiness/l4/learning-management-system/summary",
    },
]

EXPECTED_ROUTE_PATHS = [cfg["route"] for cfg in ROUTE_CONFIGS]

EXPECTED_CONTRACT = {
    "readiness_level": "L4_PROVIDER_READONLY_VISIBILITY",
    "maturity_target": "L4",
    "visibility_source_level": "L3_PROVIDER_READINESS_DETERMINISTIC_LOGIC",
    "integration_mode": "NON_LIVE_READINESS",
    "provider_profile_level": "L2_PROVIDER_READINESS_FOUNDATION",
    "deterministic_logic_version": "A-029.5",
    "visibility_version": "A-029.7",
}

NO_LIVE_STATUSES = {
    "CONNECTED",
    "SYNCED",
    "LIVE",
    "SUCCESSFUL_INTEGRATION",
    "PROVIDER_AVAILABLE",
    "CREDENTIAL_VALID",
    "SUBMITTED",
    "SIGNED",
    "POSTED",
    "DELIVERED",
    "SENT",
    "PAID",
    "REFUNDED",
    "RECONCILED",
    "PRODUCTION_READY",
}


def _load_module(cfg: dict[str, object]) -> object:
    return importlib.import_module(str(cfg["module_path"]))


def _call_service_summary(cfg: dict[str, object], tenant_id: int = 1) -> dict:
    module = _load_module(cfg)
    func = getattr(module, str(cfg["l4_func"]))
    return func(tenant_id=tenant_id)


def _headers_with_permission(permission: str = "admin.expansion.read", tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a0298-admin-tenant-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[permission],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _headers_without_permission(tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"a0298-student-tenant-{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=[],
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_text_if_available(name: str) -> str | None:
    path = _repo_root() / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def _changed_route_file_paths() -> list[Path]:
    root = _repo_root()
    return [
        root / "backend/app/modules/provider_readiness/router.py",
        root / "backend/app/main.py",
    ]


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


def test_a0298_route_module_imports() -> None:
    module = importlib.import_module("app.modules.provider_readiness.router")
    assert hasattr(module, "router")


def test_a0298_route_count_is_exactly_11() -> None:
    assert len(ROUTE_CONFIGS) == 11


def test_a0298_all_11_routes_registered() -> None:
    paths = app.openapi()["paths"]
    for path in EXPECTED_ROUTE_PATHS:
        assert path in paths


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0298_each_route_is_get_only(cfg: dict[str, object]) -> None:
    path_item = app.openapi()["paths"][str(cfg["route"])]
    assert set(path_item.keys()) == {"get"}


def test_a0298_no_mutating_provider_routes_exist() -> None:
    paths = app.openapi()["paths"]
    for route in EXPECTED_ROUTE_PATHS:
        methods = set(paths[route].keys())
        assert "post" not in methods
        assert "put" not in methods
        assert "patch" not in methods
        assert "delete" not in methods


def test_a0298_permission_dependency_present_in_router_source() -> None:
    path = _repo_root() / "backend/app/modules/provider_readiness/router.py"
    text = path.read_text(encoding="utf-8")
    assert 'permission_dependency("admin.expansion.read")' in text


def test_a0298_tenant_dependency_fail_closed_pattern_present() -> None:
    path = _repo_root() / "backend/app/modules/provider_readiness/router.py"
    text = path.read_text(encoding="utf-8")
    assert "Depends(get_current_tenant)" in text


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0298_unauthenticated_request_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]))
    assert response.status_code == 401


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0298_missing_permission_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_without_permission())
    assert response.status_code == 403


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0298_valid_permission_accepted(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
@pytest.mark.parametrize("bad_header", ["0", "-1", "not-an-int"])
def test_a0298_invalid_tenant_rejected(
    test_client: TestClient,
    cfg: dict[str, object],
    bad_header: str,
) -> None:
    headers = _headers_with_permission()
    headers["X-Tenant-ID"] = bad_header
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code in {400, 403, 422}


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0298_cross_tenant_override_rejected(test_client: TestClient, cfg: dict[str, object]) -> None:
    headers = _headers_with_permission(tenant_id=1)
    headers["X-Tenant-ID"] = "2"
    response = test_client.get(str(cfg["route"]), headers=headers)
    assert response.status_code == 403


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0298_route_calls_correct_service_function(test_client: TestClient, cfg: dict[str, object]) -> None:
    response = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 200, response.text
    assert response.json() == _call_service_summary(cfg, tenant_id=1)


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0298_contract_fields(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()

    for key, value in EXPECTED_CONTRACT.items():
        assert payload[key] == value

    assert payload["provider_connected"] is False
    assert payload["live_calls_enabled"] is False
    assert payload["credentials_configured"] is False
    assert payload["external_submission_enabled"] is False
    assert payload["sync_enabled"] is False
    assert payload["no_provider_call"] is True
    assert payload["no_credentials"] is True
    assert payload["no_external_submission"] is True
    assert payload["no_provider_connected_claim"] is True
    assert payload["no_sync_claim"] is True
    assert payload["no_l5_claim"] is True
    assert payload["no_l6_claim"] is True


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0298_no_live_connected_synced_status_words(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["provider_connected"] is False
    assert payload["live_calls_enabled"] is False
    assert payload["external_submission_enabled"] is False
    assert payload["sync_enabled"] is False
    assert str(payload["readiness_status"]).upper() not in NO_LIVE_STATUSES


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0298_provider_type_and_key_are_correct(test_client: TestClient, cfg: dict[str, object]) -> None:
    payload = test_client.get(str(cfg["route"]), headers=_headers_with_permission()).json()
    assert payload["provider_type"] == str(cfg["provider_type"])
    assert payload["provider_key"] == str(cfg["provider_key"])


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
def test_a0298_route_response_is_deterministic(test_client: TestClient, cfg: dict[str, object]) -> None:
    first = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    second = test_client.get(str(cfg["route"]), headers=_headers_with_permission())
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


@pytest.mark.parametrize("cfg", ROUTE_CONFIGS, ids=[cfg["candidate"] for cfg in ROUTE_CONFIGS])
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_a0298_non_get_methods_not_allowed(
    test_client: TestClient,
    cfg: dict[str, object],
    method: str,
) -> None:
    response = getattr(test_client, method)(str(cfg["route"]), headers=_headers_with_permission())
    assert response.status_code == 405


def test_a0298_admin_headers_fixture_still_accepts_routes() -> None:
    for cfg in ROUTE_CONFIGS:
        response = TestClient(app).get(str(cfg["route"]), headers=ADMIN_HEADERS)
        assert response.status_code == 200, response.text


def test_a0298_route_path_naming_matches_spec_table() -> None:
    spec_report = _read_text_if_available("A-029.8-SPEC-PROVIDER_READINESS_L4_API_ROUTES_REPORT.md")
    if spec_report is None:
        pytest.skip("A-029.8 SPEC report not available")

    for route in EXPECTED_ROUTE_PATHS:
        assert route in spec_report


@pytest.mark.parametrize("path", _changed_route_file_paths(), ids=lambda p: str(p))
def test_a0298_no_provider_http_libraries(path: Path) -> None:
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


@pytest.mark.parametrize("path", _changed_route_file_paths(), ids=lambda p: str(p))
def test_a0298_no_credential_or_secret_assignments(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    bad_assignments = [
        r"password\s*=\s*['\"]",
        r"secret\s*=\s*['\"]",
        r"api_key\s*=\s*['\"]",
        r"token\s*=\s*['\"]",
        r"client_secret\s*=\s*['\"]",
        r"private_key\s*=\s*['\"]",
    ]
    for pattern in bad_assignments:
        assert re.search(pattern, text) is None


@pytest.mark.parametrize("path", _changed_route_file_paths(), ids=lambda p: str(p))
def test_a0298_no_db_mutation_patterns(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    banned = [".add(", ".delete(", ".commit(", "INSERT INTO", "UPDATE ", "DELETE FROM"]
    for marker in banned:
        assert marker not in text


@pytest.mark.parametrize("path", _changed_route_file_paths(), ids=lambda p: str(p))
def test_a0298_no_frontend_behavior(path: Path) -> None:
    text = path.read_text(encoding="utf-8").lower()
    banned = ["react", "vue", "svelte", "document.", "window.", "<div", "frontend"]
    for marker in banned:
        assert marker not in text


@pytest.mark.parametrize("path", _changed_route_file_paths(), ids=lambda p: str(p))
def test_a0298_no_brain_or_autonomy_behavior(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    banned = [
        "EXECUTE_BRAIN",
        "CALL_MODEL",
        "PROCESS_SIGNAL",
        "AUTONOMOUS_ACTION",
        "AUTO_APPROVE",
        "AUTO_REJECT",
        "AUTO_SYNC",
        "AUTO_SEND",
        "AUTO_SUBMIT",
    ]
    for marker in banned:
        assert marker not in text


def test_a0298_tracker_metrics_anchor() -> None:
    tracker = _read_text_if_available("SBS_UB.md")
    if tracker is None:
        pytest.skip("SBS_UB.md is not mounted in this Docker test run")
    assert "A0298_provider_l4_api_route_count = 11" in tracker
    assert "provider_l4_api_route_count = 11" in tracker
    assert "provider_l4_visibility_count = 11" in tracker
    assert "provider_l3_deterministic_logic_count = 11" in tracker
    assert "provider_readiness_foundation_count = 11" in tracker
    assert "provider_live_call_count = 0" in tracker
    assert "provider_credentials_count = 0" in tracker
    assert "provider_external_submission_count = 0" in tracker
    assert "provider_connected_count = 0" in tracker
    assert "provider_sync_count = 0" in tracker


def test_a0298_tracker_ordinary_expansion_metrics_unchanged() -> None:
    tracker = _read_text_if_available("SBS_UB.md")
    if tracker is None:
        pytest.skip("SBS_UB.md is not mounted in this Docker test run")
    assert "expansion_L4_visibility_count = 40" in tracker
    assert "expansion_L4_api_route_count = 40" in tracker
    assert "expansion_L4_consolidated_summary_count = 1" in tracker
    assert "expansion_L4_consolidated_candidate_count = 40" in tracker
    assert "expansion_L3_logic_count = 50" in tracker
    assert "remaining_L3_not_L4 = 10" in tracker
    assert "remaining_L2_only = 17" in tracker


def test_a0298_tracker_baseline_metrics_unchanged() -> None:
    tracker = _read_text_if_available("SBS_UB.md")
    if tracker is None:
        pytest.skip("SBS_UB.md is not mounted in this Docker test run")
    assert "L0=0" in tracker
    assert "L1=0" in tracker
    assert "L2=0" in tracker
    assert "L3=55" in tracker
    assert "L4=68" in tracker
    assert "L5=25" in tracker
    assert "L6=2" in tracker
    assert "maturity_arithmetic_check=PASS" in tracker


def test_a0298_tracker_extension_metrics_unchanged() -> None:
    tracker = _read_text_if_available("SBS_UB.md")
    if tracker is None:
        pytest.skip("SBS_UB.md is not mounted in this Docker test run")
    assert "extension_total_count = 25" in tracker
    assert "total_tracked_modules = 175" in tracker
    assert "baseline_impact = 0" in tracker
    assert "extension_impact = 0" in tracker


def test_a0298_runtime_report_anchor_if_present() -> None:
    report = _read_text_if_available("A-029.8-RUNTIME-PROVIDER_READINESS_L4_API_ROUTES_REPORT.md")
    if report is None:
        pytest.skip("A-029.8 runtime report not present yet")
    assert "A-029.8-RUNTIME CLOSED" in report
    assert "A0298_provider_l4_api_route_count = 11" in report
    assert "provider_l4_api_route_count = 11" in report
