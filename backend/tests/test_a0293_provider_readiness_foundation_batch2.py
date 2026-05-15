"""
A-029.3 Provider Readiness Foundation Batch 2 — Targeted Test Suite.

Tests for deterministic, NON_LIVE_READINESS provider readiness foundation
functions for 5 deferred provider gateway modules.

Boundary:
- No live calls
- No credentials
- No external submissions
- No provider connected claims
- No sync claims
- No DB mutation
- No API route behavior
"""

from __future__ import annotations

import ast
import os
import pytest

# ---------------------------------------------------------------------------
# Module import helpers
# ---------------------------------------------------------------------------

from backend.app.modules.email_gateway_integration import service as email_svc
from backend.app.modules.notification_gateway_integration import service as notif_svc
from backend.app.modules.payment_gateway_integration import service as payment_svc
from backend.app.modules.hr_payroll_integration import service as hr_svc
from backend.app.modules.learning_management_system_integration import service as lms_svc


# ---------------------------------------------------------------------------
# Group 1: Module imports
# ---------------------------------------------------------------------------

class TestModuleImports:
    def test_email_gateway_module_importable(self):
        assert email_svc is not None

    def test_notification_gateway_module_importable(self):
        assert notif_svc is not None

    def test_payment_gateway_module_importable(self):
        assert payment_svc is not None

    def test_hr_payroll_module_importable(self):
        assert hr_svc is not None

    def test_lms_module_importable(self):
        assert lms_svc is not None


# ---------------------------------------------------------------------------
# Group 2: Provider readiness function exists
# ---------------------------------------------------------------------------

class TestProviderReadinessFunctionExists:
    def test_email_gateway_readiness_function_exists(self):
        assert hasattr(email_svc, "get_email_gateway_provider_readiness_foundation")
        assert callable(email_svc.get_email_gateway_provider_readiness_foundation)

    def test_notification_gateway_readiness_function_exists(self):
        assert hasattr(notif_svc, "get_notification_gateway_provider_readiness_foundation")
        assert callable(notif_svc.get_notification_gateway_provider_readiness_foundation)

    def test_payment_gateway_readiness_function_exists(self):
        assert hasattr(payment_svc, "get_payment_gateway_provider_readiness_foundation")
        assert callable(payment_svc.get_payment_gateway_provider_readiness_foundation)

    def test_hr_payroll_readiness_function_exists(self):
        assert hasattr(hr_svc, "get_hr_payroll_provider_readiness_foundation")
        assert callable(hr_svc.get_hr_payroll_provider_readiness_foundation)

    def test_lms_readiness_function_exists(self):
        assert hasattr(lms_svc, "get_learning_management_system_provider_readiness_foundation")
        assert callable(lms_svc.get_learning_management_system_provider_readiness_foundation)


# ---------------------------------------------------------------------------
# Group 3: Tenant fail-closed — invalid inputs rejected
# ---------------------------------------------------------------------------

READINESS_FUNCS = {
    "email": email_svc.get_email_gateway_provider_readiness_foundation,
    "notification": notif_svc.get_notification_gateway_provider_readiness_foundation,
    "payment": payment_svc.get_payment_gateway_provider_readiness_foundation,
    "hr_payroll": hr_svc.get_hr_payroll_provider_readiness_foundation,
    "lms": lms_svc.get_learning_management_system_provider_readiness_foundation,
}


class TestTenantFailClosed:
    @pytest.mark.parametrize("module_name,fn", list(READINESS_FUNCS.items()))
    def test_rejects_none_tenant(self, module_name, fn):
        with pytest.raises((ValueError, TypeError)):
            fn(None)

    @pytest.mark.parametrize("module_name,fn", list(READINESS_FUNCS.items()))
    def test_rejects_zero_tenant(self, module_name, fn):
        with pytest.raises((ValueError, TypeError)):
            fn(0)

    @pytest.mark.parametrize("module_name,fn", list(READINESS_FUNCS.items()))
    def test_rejects_negative_tenant(self, module_name, fn):
        with pytest.raises((ValueError, TypeError)):
            fn(-1)

    @pytest.mark.parametrize("module_name,fn", list(READINESS_FUNCS.items()))
    def test_rejects_string_tenant(self, module_name, fn):
        with pytest.raises((ValueError, TypeError)):
            fn("tenant1")

    @pytest.mark.parametrize("module_name,fn", list(READINESS_FUNCS.items()))
    def test_rejects_float_tenant(self, module_name, fn):
        with pytest.raises((ValueError, TypeError)):
            fn(1.5)


# ---------------------------------------------------------------------------
# Group 4: Valid tenant accepted
# ---------------------------------------------------------------------------

class TestValidTenantAccepted:
    @pytest.mark.parametrize("module_name,fn", list(READINESS_FUNCS.items()))
    def test_accepts_valid_tenant(self, module_name, fn):
        result = fn(42)
        assert isinstance(result, dict)
        assert result["tenant_id"] == 42


# ---------------------------------------------------------------------------
# Helper: get result for each module
# ---------------------------------------------------------------------------

TENANT_ID = 99

def _results():
    return {
        "email": email_svc.get_email_gateway_provider_readiness_foundation(TENANT_ID),
        "notification": notif_svc.get_notification_gateway_provider_readiness_foundation(TENANT_ID),
        "payment": payment_svc.get_payment_gateway_provider_readiness_foundation(TENANT_ID),
        "hr_payroll": hr_svc.get_hr_payroll_provider_readiness_foundation(TENANT_ID),
        "lms": lms_svc.get_learning_management_system_provider_readiness_foundation(TENANT_ID),
    }

RESULTS = _results()


# ---------------------------------------------------------------------------
# Group 5–6: Common provider readiness fields
# ---------------------------------------------------------------------------

class TestCommonFields:
    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_tenant_id_present(self, module_name, result):
        assert "tenant_id" in result
        assert result["tenant_id"] == TENANT_ID

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_module_present(self, module_name, result):
        assert "module" in result

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_uce_id_present(self, module_name, result):
        assert "uce_id" in result

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_provider_type_present(self, module_name, result):
        assert "provider_type" in result
        assert isinstance(result["provider_type"], str)
        assert len(result["provider_type"]) > 0

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_provider_key_present(self, module_name, result):
        assert "provider_key" in result
        assert isinstance(result["provider_key"], str)
        assert len(result["provider_key"]) > 0

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_provider_label_present(self, module_name, result):
        assert "provider_label" in result
        assert isinstance(result["provider_label"], str)
        assert len(result["provider_label"]) > 0

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_country_profile_present(self, module_name, result):
        assert "country_profile" in result
        assert result["country_profile"] == "KZ"

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_future_gcc_placeholder_present(self, module_name, result):
        assert "future_gcc_placeholder" in result
        assert isinstance(result["future_gcc_placeholder"], str)
        assert len(result["future_gcc_placeholder"]) > 0


# ---------------------------------------------------------------------------
# Group 11–20: Readiness level and integration mode
# ---------------------------------------------------------------------------

class TestReadinessLevelAndMode:
    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_readiness_level_correct(self, module_name, result):
        assert result["readiness_level"] == "L2_PROVIDER_READINESS_FOUNDATION"

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_maturity_target_correct(self, module_name, result):
        assert result["maturity_target"] == "L2"

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_integration_mode_correct(self, module_name, result):
        assert result["integration_mode"] == "NON_LIVE_READINESS"

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_live_calls_disabled(self, module_name, result):
        assert result["live_calls_enabled"] is False

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_credentials_not_configured(self, module_name, result):
        assert result["credentials_configured"] is False

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_credential_reference_none(self, module_name, result):
        assert result["credential_reference"] is None

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_external_submission_disabled(self, module_name, result):
        assert result["external_submission_enabled"] is False

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_provider_not_connected(self, module_name, result):
        assert result["provider_connected"] is False

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_provider_status_claim_correct(self, module_name, result):
        assert result["provider_status_claim"] == "NOT_CONNECTED_NON_LIVE_PROFILE_ONLY"

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_sync_disabled(self, module_name, result):
        assert result["sync_enabled"] is False


# ---------------------------------------------------------------------------
# Group 21–27: Evidence and requirements
# ---------------------------------------------------------------------------

class TestEvidenceAndRequirements:
    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_capability_matrix_present(self, module_name, result):
        assert "capability_matrix" in result
        cm = result["capability_matrix"]
        assert isinstance(cm, dict)
        assert "required_capabilities" in cm
        assert len(cm["required_capabilities"]) > 0

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_required_evidence_present(self, module_name, result):
        assert "required_evidence" in result
        assert isinstance(result["required_evidence"], list)
        assert len(result["required_evidence"]) > 0

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_missing_configuration_evidence_present(self, module_name, result):
        assert "missing_configuration_evidence" in result
        assert isinstance(result["missing_configuration_evidence"], list)
        assert len(result["missing_configuration_evidence"]) > 0

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_security_review_required_present(self, module_name, result):
        assert "security_review_required" in result
        assert result["security_review_required"] is True

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_legal_basis_required_present(self, module_name, result):
        assert "legal_basis_required" in result
        assert result["legal_basis_required"] is True

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_audit_required_true(self, module_name, result):
        assert result["audit_required"] is True

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_rollback_required_before_live(self, module_name, result):
        assert result["rollback_required_before_live"] is True


# ---------------------------------------------------------------------------
# Group 28–35: Anti-fake flags
# ---------------------------------------------------------------------------

class TestAntiFakeFlags:
    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_no_provider_call(self, module_name, result):
        assert result["no_provider_call"] is True

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_no_credentials(self, module_name, result):
        assert result["no_credentials"] is True

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_no_external_submission(self, module_name, result):
        assert result["no_external_submission"] is True

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_no_fake_integration_status(self, module_name, result):
        assert result["no_fake_integration_status"] is True

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_no_sync_claim(self, module_name, result):
        assert result["no_sync_claim"] is True

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_no_l4_claim(self, module_name, result):
        assert result["no_l4_claim"] is True

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_no_l5_claim(self, module_name, result):
        assert result["no_l5_claim"] is True

    @pytest.mark.parametrize("module_name,result", list(RESULTS.items()))
    def test_no_l6_claim(self, module_name, result):
        assert result["no_l6_claim"] is True


# ---------------------------------------------------------------------------
# Group 36–38: Candidate-specific values
# ---------------------------------------------------------------------------

class TestCandidateSpecificValues:
    def test_email_provider_key(self):
        r = RESULTS["email"]
        assert r["provider_key"] == "EMAIL_GATEWAY_KZ"

    def test_email_future_gcc(self):
        r = RESULTS["email"]
        assert r["future_gcc_placeholder"] == "SA_EMAIL_PROVIDER"

    def test_email_provider_type(self):
        r = RESULTS["email"]
        assert r["provider_type"] == "EMAIL_GATEWAY"

    def test_email_forbidden_actions_present(self):
        r = RESULTS["email"]
        assert "forbidden_actions" in r
        fa = r["forbidden_actions"]
        assert any("email" in f.lower() or "smtp" in f.lower() for f in fa)

    def test_notification_provider_key(self):
        r = RESULTS["notification"]
        assert r["provider_key"] == "SMS_GATEWAY_KZ"

    def test_notification_future_gcc(self):
        r = RESULTS["notification"]
        assert r["future_gcc_placeholder"] == "SA_SMS_PROVIDER"

    def test_notification_provider_type(self):
        r = RESULTS["notification"]
        assert r["provider_type"] == "NOTIFICATION_SMS_GATEWAY"

    def test_notification_forbidden_actions_present(self):
        r = RESULTS["notification"]
        assert "forbidden_actions" in r
        fa = r["forbidden_actions"]
        assert any("sms" in f.lower() or "dispatch" in f.lower() for f in fa)

    def test_payment_provider_key(self):
        r = RESULTS["payment"]
        assert r["provider_key"] == "PAYMENT_GATEWAY_KZ"

    def test_payment_future_gcc(self):
        r = RESULTS["payment"]
        assert r["future_gcc_placeholder"] == "SA_PAYMENT_PROVIDER"

    def test_payment_provider_type(self):
        r = RESULTS["payment"]
        assert r["provider_type"] == "PAYMENT_GATEWAY"

    def test_payment_forbidden_actions_present(self):
        r = RESULTS["payment"]
        assert "forbidden_actions" in r
        fa = r["forbidden_actions"]
        assert any("payment" in f.lower() or "card" in f.lower() or "gateway" in f.lower() for f in fa)

    def test_hr_payroll_provider_key(self):
        r = RESULTS["hr_payroll"]
        assert r["provider_key"] == "HR_PAYROLL_KZ"

    def test_hr_payroll_future_gcc(self):
        r = RESULTS["hr_payroll"]
        assert r["future_gcc_placeholder"] == "SA_HR_PAYROLL_PROVIDER"

    def test_hr_payroll_provider_type(self):
        r = RESULTS["hr_payroll"]
        assert r["provider_type"] == "HR_PAYROLL"

    def test_hr_payroll_forbidden_actions_present(self):
        r = RESULTS["hr_payroll"]
        assert "forbidden_actions" in r
        fa = r["forbidden_actions"]
        assert any("payroll" in f.lower() or "salary" in f.lower() or "employee" in f.lower() for f in fa)

    def test_lms_provider_key(self):
        r = RESULTS["lms"]
        assert r["provider_key"] == "LMS_KZ"

    def test_lms_future_gcc(self):
        r = RESULTS["lms"]
        assert r["future_gcc_placeholder"] == "SA_LMS_PROVIDER"

    def test_lms_provider_type(self):
        r = RESULTS["lms"]
        assert r["provider_type"] == "LMS"

    def test_lms_forbidden_actions_present(self):
        r = RESULTS["lms"]
        assert "forbidden_actions" in r
        fa = r["forbidden_actions"]
        assert any("lms" in f.lower() or "course" in f.lower() or "grade" in f.lower() for f in fa)


# ---------------------------------------------------------------------------
# Group 39: Deterministic output
# ---------------------------------------------------------------------------

class TestDeterministicOutput:
    @pytest.mark.parametrize("module_name,fn", list(READINESS_FUNCS.items()))
    def test_deterministic_same_tenant(self, module_name, fn):
        r1 = fn(7)
        r2 = fn(7)
        assert r1 == r2

    @pytest.mark.parametrize("module_name,fn", list(READINESS_FUNCS.items()))
    def test_different_tenants_differ(self, module_name, fn):
        r1 = fn(1)
        r2 = fn(2)
        assert r1["tenant_id"] != r2["tenant_id"]


# ---------------------------------------------------------------------------
# Group 40–42: Source file scanning via AST
# ---------------------------------------------------------------------------

SELECTED_SERVICE_FILES = [
    "backend/app/modules/email_gateway_integration/service.py",
    "backend/app/modules/notification_gateway_integration/service.py",
    "backend/app/modules/payment_gateway_integration/service.py",
    "backend/app/modules/hr_payroll_integration/service.py",
    "backend/app/modules/learning_management_system_integration/service.py",
]

FORBIDDEN_IMPORTS = {
    "requests", "httpx", "aiohttp", "urllib", "socket", "subprocess",
    "ldap3", "smtplib", "boto3", "zeep", "suds", "grpc", "openai", "anthropic",
}

FORBIDDEN_CREDENTIAL_PATTERNS = {
    "password", "secret", "api_key", "token", "credential",
    "client_secret", "private_key", "certificate", "refresh_token", "access_token",
}

FORBIDDEN_MUTATION_CALLS = {"session.add", "session.delete", "session.commit"}


def _load_ast(rel_path: str) -> ast.Module:
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_path = os.path.join(workspace_root, rel_path)
    with open(abs_path, "r") as f:
        return ast.parse(f.read())


def _get_imports(tree: ast.Module) -> set[str]:
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


class TestNoExternalHTTPLibraries:
    @pytest.mark.parametrize("rel_path", SELECTED_SERVICE_FILES)
    def test_no_forbidden_http_imports(self, rel_path):
        tree = _load_ast(rel_path)
        imports = _get_imports(tree)
        forbidden_found = imports & FORBIDDEN_IMPORTS
        assert not forbidden_found, f"{rel_path}: forbidden imports found: {forbidden_found}"


class TestNoCredentialsInServiceFiles:
    @pytest.mark.parametrize("rel_path", SELECTED_SERVICE_FILES)
    def test_no_credential_patterns_in_source(self, rel_path):
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        abs_path = os.path.join(workspace_root, rel_path)
        with open(abs_path, "r") as f:
            source = f.read().lower()
        # Allow known-safe patterns that appear in boundary/forbidden_actions descriptions
        # Check for actual credential assignment patterns by scanning AST assignments
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name_lower = target.id.lower()
                        # Flag only variable assignments that are credential names
                        if any(cp in name_lower for cp in {"password", "api_key", "client_secret", "private_key", "refresh_token", "access_token"}):
                            pytest.fail(f"{rel_path}: credential variable assignment found: {target.id}")


class TestNoDBMutationInServiceFiles:
    @pytest.mark.parametrize("rel_path", SELECTED_SERVICE_FILES)
    def test_no_db_mutation_calls(self, rel_path):
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        abs_path = os.path.join(workspace_root, rel_path)
        with open(abs_path, "r") as f:
            source = f.read()
        # Scan for session.add( / session.delete( / session.commit(
        import re
        pattern = re.compile(r"\bsession\.(add|delete|commit)\s*\(")
        matches = pattern.findall(source)
        assert not matches, f"{rel_path}: DB mutation calls found: {matches}"


class TestNoAPIRouteBehavior:
    @pytest.mark.parametrize("rel_path", SELECTED_SERVICE_FILES)
    def test_no_router_decorator(self, rel_path):
        tree = _load_ast(rel_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Attribute):
                        if decorator.attr in {"get", "post", "put", "delete", "patch"}:
                            pytest.fail(f"{rel_path}: API route decorator found on {node.name}")


# ---------------------------------------------------------------------------
# Group 44–53: Tracker metric invariants
# ---------------------------------------------------------------------------

TRACKER_PATH = "SBS_UB.md"


def _tracker_lines() -> list[str]:
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_path = os.path.join(workspace_root, TRACKER_PATH)
    if not os.path.exists(abs_path):
        return []
    with open(abs_path, "r") as f:
        return f.readlines()


def _find_in_tracker(pattern: str) -> list[str]:
    import re
    lines = _tracker_lines()
    if not lines:
        return []
    return [l.strip() for l in lines if re.search(pattern, l)]


def _skip_if_no_tracker():
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    abs_path = os.path.join(workspace_root, TRACKER_PATH)
    if not os.path.exists(abs_path):
        pytest.skip("SBS_UB.md not available in this Docker mount context")


class TestTrackerMetricInvariants:
    def test_baseline_l3_55_preserved(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"L3=55")
        assert matches, "L3=55 not found in tracker"

    def test_baseline_l4_68_preserved(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"L4=68")
        assert matches, "L4=68 not found in tracker"

    def test_expansion_l4_visibility_count_40(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"expansion_L4_visibility_count\s*=\s*40")
        assert matches, "expansion_L4_visibility_count = 40 not found"

    def test_expansion_l4_api_route_count_40(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"expansion_L4_api_route_count\s*=\s*40")
        assert matches, "expansion_L4_api_route_count = 40 not found"

    def test_expansion_l4_consolidated_summary_count_1(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"expansion_L4_consolidated_summary_count\s*=\s*1")
        assert matches, "expansion_L4_consolidated_summary_count = 1 not found"

    def test_expansion_l4_consolidated_candidate_count_40(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"expansion_L4_consolidated_candidate_count\s*=\s*40")
        assert matches, "expansion_L4_consolidated_candidate_count = 40 not found"

    def test_expansion_l3_logic_count_50(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"expansion_L3_logic_count\s*=\s*50")
        assert matches, "expansion_L3_logic_count = 50 not found"

    def test_a0293_provider_readiness_count_5(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"A0293_provider_readiness_foundation_count\s*=\s*5")
        assert matches, "A0293_provider_readiness_foundation_count = 5 not found"

    def test_provider_readiness_foundation_count_11(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"provider_readiness_foundation_count\s*=\s*11")
        assert matches, "provider_readiness_foundation_count = 11 not found"

    def test_provider_live_call_count_0(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"provider_live_call_count\s*=\s*0")
        assert matches, "provider_live_call_count = 0 not found"

    def test_provider_credentials_count_0(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"provider_credentials_count\s*=\s*0")
        assert matches, "provider_credentials_count = 0 not found"

    def test_provider_external_submission_count_0(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"provider_external_submission_count\s*=\s*0")
        assert matches, "provider_external_submission_count = 0 not found"

    def test_provider_connected_count_0(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"provider_connected_count\s*=\s*0")
        assert matches, "provider_connected_count = 0 not found"

    def test_provider_sync_count_0(self):
        _skip_if_no_tracker()
        matches = _find_in_tracker(r"provider_sync_count\s*=\s*0")
        assert matches, "provider_sync_count = 0 not found"


# ---------------------------------------------------------------------------
# Group 54: A-029.2 batch 1 integrity preserved
# ---------------------------------------------------------------------------

class TestA0292Batch1Preserved:
    def test_sis_readiness_function_still_importable(self):
        from backend.app.modules.student_information_system_integration import service as sis_svc
        assert hasattr(sis_svc, "get_student_information_system_provider_readiness_foundation")

    def test_finance_erp_readiness_function_still_importable(self):
        from backend.app.modules.finance_erp_integration import service as fin_svc
        assert hasattr(fin_svc, "get_finance_erp_provider_readiness_foundation")

    def test_government_services_readiness_function_still_importable(self):
        from backend.app.modules.government_services_integration import service as gov_svc
        assert hasattr(gov_svc, "get_government_services_provider_readiness_foundation")

    def test_digital_signature_readiness_function_still_importable(self):
        from backend.app.modules.digital_signature_integration import service as dsig_svc
        assert hasattr(dsig_svc, "get_digital_signature_provider_readiness_foundation")

    def test_regulatory_reporting_readiness_function_still_importable(self):
        from backend.app.modules.regulatory_reporting_integration import service as reg_svc
        assert hasattr(reg_svc, "get_regulatory_reporting_provider_readiness_foundation")

    def test_identity_provider_readiness_function_still_importable(self):
        from backend.app.modules.identity_provider_integration import service as idp_svc
        assert hasattr(idp_svc, "get_identity_provider_readiness_foundation")
