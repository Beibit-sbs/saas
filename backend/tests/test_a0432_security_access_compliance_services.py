from __future__ import annotations

import pytest

from app.modules.security_access_compliance import service


READ_METHODS = [
    "get_overview",
    "get_readiness",
    "get_dashboard",
    "get_limitations",
    "get_roles",
    "get_permissions",
    "get_access_governance",
    "get_rbac_evidence",
    "get_abac_evidence",
    "get_sessions",
    "get_login_events",
    "get_mfa_readiness",
    "get_tenant_isolation",
    "get_incidents",
    "get_incident_review",
    "get_remediation",
    "get_risks",
    "get_compliance_controls",
    "get_policy_controls",
    "get_audit_events",
    "get_sensitive_actions",
    "get_data_protection",
    "get_privacy_readiness",
    "get_exceptions",
    "get_visitor_access",
    "get_bridge_hr",
    "get_bridge_finance",
    "get_bridge_documents",
    "get_bridge_student_services",
    "get_metadata_contract",
    "get_safety_boundaries",
    "get_health",
]

WRITE_METHODS = [
    "create_incident_metadata",
    "create_incident_review_metadata",
    "create_remediation_metadata",
    "create_risk_metadata",
    "create_compliance_control_metadata",
    "create_policy_control_metadata",
    "create_audit_event_metadata",
    "create_sensitive_action_review",
    "create_data_protection_evidence",
    "create_privacy_readiness_evidence",
    "create_exception_metadata",
    "create_visitor_access_metadata",
    "create_bridge_hr",
    "create_bridge_finance",
    "create_bridge_documents",
    "create_bridge_student_services",
    "create_limitation_record",
]


@pytest.mark.parametrize("method_name", READ_METHODS)
def test_read_method_exists(method_name: str) -> None:
    assert hasattr(service, method_name)


@pytest.mark.parametrize("method_name", WRITE_METHODS)
def test_write_method_exists(method_name: str) -> None:
    assert hasattr(service, method_name)


def test_metadata_contract_matches_counts() -> None:
    response = service.get_metadata_contract(tenant_id=1)
    assert response.expected_table_count == 24
    assert response.expected_route_count == 47
    assert response.expected_permission_count == 44
    assert response.permission_namespace == "security_access_compliance.*"


def test_metadata_contract_safety_flags_are_fail_closed() -> None:
    response = service.get_metadata_contract(tenant_id=1)
    flags = response.safety_flags
    assert flags.fake_security_certification is False
    assert flags.fake_compliance_certification is False
    assert flags.legal_regulatory_compliance_claimed is False
    assert flags.soc_siem_replacement_claimed is False
    assert flags.fake_incident_resolution is False
    assert flags.fake_audit_proof is False
    assert flags.fake_penetration_test_result is False
    assert flags.fake_vulnerability_scan_result is False
    assert flags.fake_risk_score is False
    assert flags.hidden_user_risk_score_present is False
    assert flags.discriminatory_ranking_present is False
    assert flags.autonomous_enforcement_enabled is False
    assert flags.automatic_user_blocking_enabled is False
    assert flags.automatic_user_sanction_enabled is False
    assert flags.automatic_data_deletion_enabled is False
    assert flags.external_regulator_submission_enabled is False
    assert flags.production_security_claimed is False
    assert flags.human_review_required is True


@pytest.mark.parametrize(
    "marker",
    [
        "no fake security certification",
        "no fake compliance certification",
        "no fake legal/regulatory compliance claim",
        "no fake soc/siem claim",
        "no fake incident resolution",
        "no fake audit proof",
        "no fake penetration-test result",
        "no fake vulnerability-scan result",
        "no fake risk score",
        "no hidden user risk score",
        "no discriminatory ranking",
        "no automatic user blocking",
        "no automatic user sanction",
        "no automatic data deletion",
        "no autonomous enforcement",
        "no external regulator submission",
        "no production-ready security claim",
    ],
)
def test_safety_boundary_markers_present(marker: str) -> None:
    assert marker in service.get_safety_boundaries()
