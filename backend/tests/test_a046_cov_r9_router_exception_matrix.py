from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.main import app
from app.modules.auth.token_service import create_access_token
from app.modules.integration_provider_readiness import API_PREFIX as IPR_PREFIX
from app.modules.integration_provider_readiness import permissions as ipr_permissions
from app.modules.integration_provider_readiness.dependencies import get_integration_provider_readiness_db
from app.modules.integration_provider_readiness import router as ipr_router
from app.modules.security_access_compliance import permissions as sac_permissions
from app.modules.security_access_compliance.dependencies import get_security_access_compliance_db
from app.modules.security_access_compliance import router as sac_router
from tests.conftest import client


def _headers_with_permissions(permission_list: list[str], tenant_id: int = 1) -> dict[str, str]:
    token = create_access_token(
        user_id=f"r9-router-{tenant_id}@example.com",
        roles=["admin"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=permission_list,
    )
    return {"Authorization": f"Bearer {token}", "X-Tenant-ID": str(tenant_id)}


IPR_HEADERS = _headers_with_permissions(list(ipr_permissions.ALL_PERMISSIONS))
SAC_HEADERS = _headers_with_permissions(sorted(sac_permissions.ALL_PERMISSIONS))
SAC_BASE = "/api/admin/security-access-compliance"


@pytest.fixture(autouse=True)
def _override_module_dbs():
    app.dependency_overrides[get_integration_provider_readiness_db] = lambda: MagicMock()
    app.dependency_overrides[get_security_access_compliance_db] = lambda: MagicMock()
    yield
    app.dependency_overrides.pop(get_integration_provider_readiness_db, None)
    app.dependency_overrides.pop(get_security_access_compliance_db, None)


def _raise_domain_validation(*_args, **_kwargs):
    raise DomainValidationError("r9-domain-validation")


def _raise_not_found(*_args, **_kwargs):
    raise TenantResourceNotFoundError("r9-not-found")


@pytest.mark.parametrize(
    ("method", "path", "service_fn", "payload"),
    [
        ("get", f"{IPR_PREFIX}/providers", "list_provider_registry", None),
        ("get", f"{IPR_PREFIX}/providers/1", "get_provider_registry", None),
        ("get", f"{IPR_PREFIX}/providers/by-type/erp", "list_provider_registry", None),
        ("post", f"{IPR_PREFIX}/providers", "create_provider_registry", {"status": "draft", "payload": {}}),
        ("put", f"{IPR_PREFIX}/providers/1", "update_provider_registry", {"status": "draft", "payload": {}}),
        ("get", f"{IPR_PREFIX}/providers/prov-1/profiles", "list_profiles", None),
        ("get", f"{IPR_PREFIX}/profiles/1", "get_profile", None),
        ("post", f"{IPR_PREFIX}/providers/prov-1/profiles", "create_provider_profile", {"status": "draft", "payload": {}}),
        ("put", f"{IPR_PREFIX}/profiles/1", "update_provider_profile", {"status": "draft", "payload": {}}),
        ("delete", f"{IPR_PREFIX}/profiles/1", "delete_provider_profile", None),
        ("get", f"{IPR_PREFIX}/providers/prov-1/capabilities", "list_capabilities", None),
        ("get", f"{IPR_PREFIX}/capabilities/1", "get_capability", None),
        ("post", f"{IPR_PREFIX}/providers/prov-1/capabilities", "upsert_capability_matrix", {"status": "draft", "payload": {}}),
        ("put", f"{IPR_PREFIX}/capabilities/1", "update_capability_matrix", {"status": "draft", "payload": {}}),
        ("get", f"{IPR_PREFIX}/providers/prov-1/assessments", "list_readiness_assessments", None),
        ("get", f"{IPR_PREFIX}/assessments/1", "get_readiness_assessment", None),
        ("post", f"{IPR_PREFIX}/providers/prov-1/assessments", "create_readiness_assessment", {"status": "draft", "payload": {}}),
        ("put", f"{IPR_PREFIX}/assessments/1", "update_readiness_assessment", {"status": "draft", "payload": {}}),
        ("get", f"{IPR_PREFIX}/providers/prov-1/evidence", "list_evidence", None),
        ("get", f"{IPR_PREFIX}/evidence/1", "get_evidence", None),
        ("get", f"{IPR_PREFIX}/providers/prov-1/evidence-links", "list_evidence_links", None),
        ("post", f"{IPR_PREFIX}/providers/prov-1/evidence", "collect_evidence", {"status": "draft", "payload": {}}),
        ("post", f"{IPR_PREFIX}/evidence/1/links", "link_evidence", {"status": "draft", "payload": {}}),
        ("put", f"{IPR_PREFIX}/evidence/1", "update_evidence", {"status": "draft", "payload": {}}),
        ("get", f"{IPR_PREFIX}/providers/prov-1/compliance-reviews", "list_compliance_reviews", None),
        ("get", f"{IPR_PREFIX}/providers/prov-1/security-reviews", "list_security_reviews", None),
        ("post", f"{IPR_PREFIX}/providers/prov-1/compliance-reviews", "review_compliance", {"status": "draft", "payload": {}}),
        ("put", f"{IPR_PREFIX}/compliance-reviews/1", "approve_compliance", {"status": "draft", "payload": {}}),
        ("put", f"{IPR_PREFIX}/security-reviews/1", "review_security", {"status": "draft", "payload": {}}),
        ("get", f"{IPR_PREFIX}/providers/prov-1/risks", "list_risks", None),
        ("get", f"{IPR_PREFIX}/providers/prov-1/exceptions", "list_exceptions", None),
        ("post", f"{IPR_PREFIX}/providers/prov-1/risks", "escalate_risk_exception", {"status": "draft", "payload": {}}),
        ("put", f"{IPR_PREFIX}/exceptions/1", "update_exception_case", {"status": "draft", "payload": {}}),
        ("get", f"{IPR_PREFIX}/providers/prov-1/audits", "list_audit_records", None),
        ("post", f"{IPR_PREFIX}/providers/prov-1/audits", "record_provider_audit_review", {"status": "draft", "payload": {}}),
        ("get", f"{IPR_PREFIX}/providers/prov-1/health", "generate_provider_health_visibility", None),
        ("get", f"{IPR_PREFIX}/health-snapshots", "list_health_snapshots", None),
        ("get", f"{IPR_PREFIX}/health-summary", "get_health_summary", None),
        ("get", f"{IPR_PREFIX}/providers/prov-1/plans", "list_integration_plans", None),
        ("get", f"{IPR_PREFIX}/roadmap", "get_roadmap_summary", None),
        ("post", f"{IPR_PREFIX}/providers/prov-1/plans", "plan_integration_roadmap", {"status": "draft", "payload": {}}),
        ("delete", f"{IPR_PREFIX}/plans/1", "delete_integration_plan", None),
        ("get", f"{IPR_PREFIX}/dashboards", "publish_dashboard_bundle", None),
        ("get", f"{IPR_PREFIX}/dashboards/overview", "get_dashboard_contract", None),
    ],
)
def test_ipr_router_maps_domain_validation_to_400(monkeypatch: pytest.MonkeyPatch, method: str, path: str, service_fn: str, payload: dict | None):
    monkeypatch.setattr(ipr_router.service, service_fn, _raise_domain_validation)
    request = getattr(client, method)
    response = request(path, headers=IPR_HEADERS, json=payload) if payload is not None else request(path, headers=IPR_HEADERS)
    assert response.status_code == 400
    assert "r9-domain-validation" in response.text


def test_ipr_router_maps_not_found_to_404(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(ipr_router.service, "get_provider_registry", _raise_not_found)
    response = client.get(f"{IPR_PREFIX}/providers/1", headers=IPR_HEADERS)
    assert response.status_code == 404


@pytest.mark.parametrize(
    ("method", "path", "service_fn", "payload"),
    [
        ("get", f"{SAC_BASE}/overview", "get_overview", None),
        ("get", f"{SAC_BASE}/readiness", "get_readiness", None),
        ("get", f"{SAC_BASE}/dashboard", "get_dashboard", None),
        ("get", f"{SAC_BASE}/limitations", "get_limitations", None),
        ("get", f"{SAC_BASE}/roles", "get_roles", None),
        ("get", f"{SAC_BASE}/permissions", "get_permissions", None),
        ("get", f"{SAC_BASE}/access-governance", "get_access_governance", None),
        ("get", f"{SAC_BASE}/rbac-evidence", "get_rbac_evidence", None),
        ("get", f"{SAC_BASE}/abac-evidence", "get_abac_evidence", None),
        ("get", f"{SAC_BASE}/sessions", "get_sessions", None),
        ("get", f"{SAC_BASE}/login-events", "get_login_events", None),
        ("get", f"{SAC_BASE}/mfa-readiness", "get_mfa_readiness", None),
        ("get", f"{SAC_BASE}/tenant-isolation", "get_tenant_isolation", None),
        ("get", f"{SAC_BASE}/incidents", "get_incidents", None),
        ("get", f"{SAC_BASE}/incident-review", "get_incident_review", None),
        ("get", f"{SAC_BASE}/remediation", "get_remediation", None),
        ("get", f"{SAC_BASE}/risks", "get_risks", None),
        ("get", f"{SAC_BASE}/compliance-controls", "get_compliance_controls", None),
        ("get", f"{SAC_BASE}/policy-controls", "get_policy_controls", None),
        ("get", f"{SAC_BASE}/audit-events", "get_audit_events", None),
        ("get", f"{SAC_BASE}/sensitive-actions", "get_sensitive_actions", None),
        ("get", f"{SAC_BASE}/data-protection", "get_data_protection", None),
        ("get", f"{SAC_BASE}/privacy-readiness", "get_privacy_readiness", None),
        ("get", f"{SAC_BASE}/exceptions", "get_exceptions", None),
        ("get", f"{SAC_BASE}/visitor-access", "get_visitor_access", None),
        ("get", f"{SAC_BASE}/bridges/hr", "get_bridge_hr", None),
        ("get", f"{SAC_BASE}/bridges/finance", "get_bridge_finance", None),
        ("get", f"{SAC_BASE}/bridges/documents", "get_bridge_documents", None),
        ("get", f"{SAC_BASE}/bridges/student-services", "get_bridge_student_services", None),
        ("get", f"{SAC_BASE}/metadata-contract", "get_metadata_contract", None),
        ("post", f"{SAC_BASE}/incidents/metadata", "create_incident_metadata", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/incident-review/metadata", "create_incident_review_metadata", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/remediation/metadata", "create_remediation_metadata", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/risks/metadata", "create_risk_metadata", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/compliance-controls/metadata", "create_compliance_control_metadata", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/policy-controls/metadata", "create_policy_control_metadata", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/audit-events/metadata", "create_audit_event_metadata", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/sensitive-actions/review", "create_sensitive_action_review", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/data-protection/evidence", "create_data_protection_evidence", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/privacy-readiness/evidence", "create_privacy_readiness_evidence", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/exceptions/metadata", "create_exception_metadata", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/visitor-access/metadata", "create_visitor_access_metadata", {"record_key": "r9", "metadata": {}}),
        ("post", f"{SAC_BASE}/bridges/hr", "create_bridge_hr", {"record_key": "r9", "bridge_key": "hr", "metadata": {}}),
        ("post", f"{SAC_BASE}/bridges/finance", "create_bridge_finance", {"record_key": "r9", "bridge_key": "finance", "metadata": {}}),
        ("post", f"{SAC_BASE}/bridges/documents", "create_bridge_documents", {"record_key": "r9", "bridge_key": "documents", "metadata": {}}),
        ("post", f"{SAC_BASE}/bridges/student-services", "create_bridge_student_services", {"record_key": "r9", "bridge_key": "student-services", "metadata": {}}),
        ("post", f"{SAC_BASE}/limitations", "create_limitation_record", {"record_key": "r9", "metadata": {}}),
    ],
)
def test_sac_router_maps_domain_validation_to_400(monkeypatch: pytest.MonkeyPatch, method: str, path: str, service_fn: str, payload: dict | None):
    monkeypatch.setattr(sac_router.service, service_fn, _raise_domain_validation)
    request = getattr(client, method)
    response = request(path, headers=SAC_HEADERS, json=payload) if payload is not None else request(path, headers=SAC_HEADERS)
    assert response.status_code == 400
    assert "r9-domain-validation" in response.text


def test_sac_router_maps_not_found_to_404(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sac_router.service, "get_overview", _raise_not_found)
    response = client.get(f"{SAC_BASE}/overview", headers=SAC_HEADERS)
    assert response.status_code == 404
