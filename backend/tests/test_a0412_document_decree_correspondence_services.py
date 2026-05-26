from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.modules.document_decree_correspondence import permissions, service


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_metadata_contract_counts() -> None:
    db = _db()
    contract = service.get_metadata_contract(db, 1)
    assert contract.route_count == 53
    assert contract.table_count == 26
    assert contract.permission_count == 50
    assert len(contract.permissions) == 50


def test_health_counts() -> None:
    db = _db()
    health = service.get_health(db, 1)
    assert health["route_count"] == 53
    assert health["table_count"] == 26
    assert health["permission_count"] == 50


def test_roles_non_empty() -> None:
    db = _db()
    payload = service.get_roles(db, 1)
    assert payload["roles"]


@pytest.mark.parametrize(
    "name",
    [
        "get_overview",
        "get_readiness",
        "get_limitations",
        "get_safety_boundaries",
        "get_dashboard",
        "get_documents",
        "get_document_intake",
        "get_document_routing",
        "get_rector_resolutions",
        "get_decrees",
        "get_decree_drafts",
        "get_incoming_correspondence",
        "get_outgoing_correspondence",
        "get_templates",
        "get_committee_decisions",
        "get_assignments",
        "get_execution_control",
        "get_sla_deadlines",
        "get_evidence",
        "get_attachments",
        "get_audit_events",
        "get_archive",
        "get_signature_readiness",
        "get_delivery_readiness",
        "get_bridge_executive",
        "get_bridge_assignments",
        "get_health",
        "get_roles",
        "get_permissions",
        "get_metadata_contract",
    ],
)
def test_required_read_methods_exist(name: str) -> None:
    assert hasattr(service, name)


@pytest.mark.parametrize(
    "name",
    [
        "create_document_intake_record",
        "create_document_registration_metadata",
        "create_document_routing_metadata",
        "create_rector_resolution_metadata",
        "create_decree_registry_metadata",
        "create_decree_draft_metadata",
        "create_incoming_correspondence_metadata",
        "create_outgoing_correspondence_metadata",
        "create_template_metadata",
        "create_committee_decision_bridge_metadata",
        "create_assignment_bridge_metadata",
        "create_execution_control_metadata",
        "create_sla_deadline_metadata",
        "create_evidence_item",
        "create_attachment_metadata",
        "create_audit_event",
        "create_archive_readiness_metadata",
        "create_retention_metadata",
        "create_signature_readiness_evidence",
        "create_delivery_readiness_evidence",
        "create_bridge_record",
        "create_limitation_record",
    ],
)
def test_required_create_methods_exist(name: str) -> None:
    assert hasattr(service, name)


@pytest.mark.parametrize(
    "value",
    [
        permissions.OVERVIEW_READ,
        permissions.READINESS_READ,
        permissions.LIMITATIONS_READ,
        permissions.DASHBOARD_READ,
        permissions.DOCUMENTS_READ,
        permissions.DOCUMENT_INTAKE_READ,
        permissions.DOCUMENT_INTAKE_MANAGE,
        permissions.DOCUMENT_REGISTRATION_MANAGE,
        permissions.DOCUMENT_ROUTING_READ,
        permissions.DOCUMENT_ROUTING_MANAGE,
        permissions.RECTOR_RESOLUTIONS_READ,
        permissions.RECTOR_RESOLUTIONS_METADATA,
        permissions.DECREES_READ,
        permissions.DECREES_METADATA,
        permissions.DECREE_DRAFTS_READ,
        permissions.DECREE_DRAFTS_MANAGE,
        permissions.INCOMING_CORRESPONDENCE_READ,
        permissions.INCOMING_CORRESPONDENCE_MANAGE,
        permissions.OUTGOING_CORRESPONDENCE_READ,
        permissions.OUTGOING_CORRESPONDENCE_MANAGE,
        permissions.TEMPLATES_READ,
        permissions.TEMPLATES_METADATA,
        permissions.COMMITTEE_DECISIONS_READ,
        permissions.COMMITTEE_DECISIONS_BRIDGE,
        permissions.ASSIGNMENTS_READ,
        permissions.ASSIGNMENTS_BRIDGE,
        permissions.EXECUTION_CONTROL_READ,
        permissions.EXECUTION_CONTROL_METADATA,
        permissions.SLA_DEADLINES_READ,
        permissions.SLA_DEADLINES_METADATA,
        permissions.EVIDENCE_READ,
        permissions.EVIDENCE_WRITE,
        permissions.ATTACHMENTS_READ,
        permissions.ATTACHMENTS_METADATA,
        permissions.AUDIT_READ,
        permissions.AUDIT_WRITE,
        permissions.ARCHIVE_READ,
        permissions.ARCHIVE_READINESS,
        permissions.RETENTION_READ,
        permissions.RETENTION_METADATA,
        permissions.SIGNATURE_READINESS_READ,
        permissions.SIGNATURE_READINESS_EVIDENCE,
        permissions.DELIVERY_READINESS_READ,
        permissions.DELIVERY_READINESS_EVIDENCE,
        permissions.BRIDGES_EXECUTIVE_READ,
        permissions.BRIDGES_EXECUTIVE_WRITE,
        permissions.BRIDGES_ASSIGNMENTS_READ,
        permissions.BRIDGES_ASSIGNMENTS_WRITE,
        permissions.ROLES_READ,
        permissions.METADATA_READ,
    ],
)
def test_permissions_are_under_namespace(value: str) -> None:
    assert value.startswith("document_decree_correspondence.")
