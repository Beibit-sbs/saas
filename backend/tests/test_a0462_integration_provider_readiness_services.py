from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.modules.integration_provider_readiness import EXPECTED_PROVIDER_COUNT, WORKFLOW_NAMES
from app.modules.integration_provider_readiness import models, service


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    models.Base.metadata.create_all(bind=engine, tables=[model.__table__ for model in models.ALL_MODELS])
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
        models.Base.metadata.drop_all(bind=engine, tables=[model.__table__ for model in models.ALL_MODELS])


class TestServiceFoundation:
    def test_provider_catalog_bootstraps(self, db_session: Session) -> None:
        payload = service.list_provider_registry(db_session, 1)
        assert payload["total"] == EXPECTED_PROVIDER_COUNT

    def test_health_summary_is_readiness_only(self, db_session: Session) -> None:
        summary = service.get_health_summary(db_session, 1)
        assert summary["readiness_only"] is True
        assert summary["provider_connected"] is False
        assert summary["live_provider_calls"] is False
        assert summary["external_submission"] is False

    def test_publish_dashboard_bundle_count(self, db_session: Session) -> None:
        payload = service.publish_dashboard_bundle(db_session, 1)
        assert payload["total"] == 6

    def test_roadmap_summary_count(self, db_session: Session) -> None:
        payload = service.get_roadmap_summary(db_session, 1)
        assert payload["total"] == 1


@pytest.mark.parametrize("workflow_name", WORKFLOW_NAMES)
def test_workflow_names_locked(workflow_name: str) -> None:
    assert workflow_name.endswith("Workflow")


class TestWorkflowMutations:
    def test_create_profile(self, db_session: Session) -> None:
        service.list_provider_registry(db_session, 1)
        result = service.create_provider_profile(db_session, 1, "UCE-024", "owner@example.com", {"profile": "v1"})
        assert result["record_type"] == "provider_profile"
        assert result["provider_connected"] is False

    def test_upsert_capability(self, db_session: Session) -> None:
        result = service.upsert_capability_matrix(db_session, 1, "UCE-024", "owner@example.com", {"capability": "readiness"})
        assert result["record_type"] == "provider_capability"

    def test_create_assessment(self, db_session: Session) -> None:
        result = service.create_readiness_assessment(db_session, 1, "UCE-024", "owner@example.com", {"score": 7})
        assert result["record_type"] == "provider_assessment"

    def test_collect_evidence(self, db_session: Session) -> None:
        result = service.collect_evidence(db_session, 1, "UCE-024", "owner@example.com", {"evidence": "doc"})
        assert result["record_type"] == "provider_evidence"

    def test_review_compliance(self, db_session: Session) -> None:
        result = service.review_compliance(db_session, 1, "UCE-024", "owner@example.com", {"decision": "pending"})
        assert result["record_type"] == "provider_compliance_review"

    def test_review_security(self, db_session: Session) -> None:
        result = service.review_security(db_session, 1, 9001, "owner@example.com", {"provider_id": "UCE-024", "decision": "reviewed"})
        assert result["record_type"] == "provider_security_review"

    def test_escalate_risk(self, db_session: Session) -> None:
        result = service.escalate_risk_exception(db_session, 1, "UCE-024", "owner@example.com", {"severity": "high"})
        assert result["record_type"] == "provider_risk"

    def test_update_exception(self, db_session: Session) -> None:
        result = service.update_exception_case(db_session, 1, 8001, "owner@example.com", {"provider_id": "UCE-024", "action": "tracked"})
        assert result["record_type"] == "provider_exception"

    def test_append_audit(self, db_session: Session) -> None:
        result = service.record_provider_audit_review(db_session, 1, "UCE-024", "owner@example.com", {"finding": "ok"})
        assert result["record_type"] == "provider_audit"

    def test_generate_health_visibility(self, db_session: Session) -> None:
        result = service.generate_provider_health_visibility(db_session, 1, "UCE-024", "owner@example.com")
        assert result["total"] >= 1

    def test_plan_integration(self, db_session: Session) -> None:
        result = service.plan_integration_roadmap(db_session, 1, "UCE-024", "owner@example.com", {"phase": "L5"})
        assert result["record_type"] == "provider_integration_plan"


@pytest.mark.parametrize(
    "call",
    [
        lambda db: service.list_provider_registry(db, 1),
        lambda db: service.list_health_snapshots(db, 1),
        lambda db: service.publish_dashboard_bundle(db, 1),
        lambda db: service.get_health_summary(db, 1),
    ],
)
def test_anti_fake_across_service_outputs(db_session: Session, call) -> None:
    result = call(db_session)
    text = str(result)
    assert "provider_connected': True" not in text
    assert "live_provider_calls': True" not in text
    assert "external_submission': True" not in text
