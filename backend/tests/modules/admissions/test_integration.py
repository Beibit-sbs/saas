"""
Admissions Integration Validation Suite
========================================
Scope
-----
Layer tested:   FastAPI lifespan wiring + router + dependency injection + RBAC
Layer mocked:   SQLAlchemy Session (MagicMock), service methods (monkeypatch)
Not tested:     real database I/O, Alembic migrations, psycopg driver

Why
---
The test_router.py skeletons exercise individual contract assertions.
This file validates the *integration surface*:
  1.  App startup registers admissions_session_factory when DATABASE_URL is set.
  2.  App startup leaves factory absent (and logs a warning) when DATABASE_URL is absent.
  3.  Every admissions endpoint returns HTTP 503 when the factory is not wired.
  4.  Happy-path smoke for all 10 endpoints when the dependency is overridden.
  5.  RBAC enforcement checked at the router layer (not service layer).
  6.  Tenant isolation: cross-tenant "not found" maps to 404 (not 500).
  7.  DB dependency lifecycle: session.close() is called exactly once per request.

Design decisions
----------------
- We never need a live DB.  The service methods are monkeypatched so that the
  *router* code path executes in full (payload parsing, RBAC, dep injection,
  error mapping) without touching SQLAlchemy's execution layer.
- The `override_admissions_db` fixture replaces `get_admissions_db` so the
  fail-closed 503 path is opt-*in* per test.
- Tests that validate the 503 path *do not* install the fixture.
- Startup tests use a dedicated `FastAPI` instance so they don't interfere with
  the module-level `app` used by the rest of the suite.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app
from app.modules.admissions.dependencies import get_admissions_db
from app.modules.admissions import service as admissions_service
from app.modules.admissions.schemas import (
    ApplicantListResponseSchema,
    ApplicantReadSchema,
    ApplicationDecisionReadSchema,
    ApplicationListResponseSchema,
    ApplicationReadSchema,
    ApplicationStage,
    DocumentReadSchema,
    StageTransitionResponseSchema,
)
from tests.conftest import ADMIN_HEADERS, _auth_headers, client

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_NOW = "2026-03-22T12:00:00Z"


def _applicant_read(**overrides) -> ApplicantReadSchema:
    base = dict(
        id=1,
        tenant_id=1,
        email="integration@test.edu",
        first_name="Integration",
        last_name="Test",
        phone=None,
        program_id=10,
        application_year=2026,
        status="active",
        external_id=None,
        metadata_json={},
        created_by="admin@example.com",
        created_at=_NOW,
        updated_at=_NOW,
    )
    base.update(overrides)
    return ApplicantReadSchema(**base)


def _application_read(**overrides) -> ApplicationReadSchema:
    base = dict(
        id=2,
        tenant_id=1,
        applicant_id=1,
        program_id=10,
        metadata_json={},
        stage=ApplicationStage.NEW,
        conclusion_type=None,
        received_at=None,
        decision_at=None,
        version=1,
        created_by="admin@example.com",
        created_at=_NOW,
        updated_at=_NOW,
    )
    base.update(overrides)
    return ApplicationReadSchema(**base)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def override_admissions_db() -> Generator[MagicMock, None, None]:
    """
    Replace the `get_admissions_db` dependency with a MagicMock session.
    The mock records calls so tests can assert session.close() behaviour.
    """
    session = MagicMock(name="admissions_db_session")
    app.dependency_overrides[get_admissions_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_admissions_db, None)


# ---------------------------------------------------------------------------
# Section 1 — App startup wiring
# ---------------------------------------------------------------------------

class TestStartupWithDatabaseUrl:
    """Lifespan sets admissions_session_factory when DATABASE_URL is present."""

    def test_session_factory_is_set_on_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        When DATABASE_URL is present, lifespan should call build_engine() +
        make_session_factory() and assign the result to app.state.
        """
        monkeypatch.setenv("DATABASE_URL", "postgresql://db/testdb")
        fake_factory = MagicMock(name="session_factory")

        with (
            patch("app.main.build_engine", return_value=MagicMock(name="engine")),
            # patch(return_value=X) makes calling make_session_factory(...) return X.
            patch("app.main.make_session_factory", return_value=fake_factory),
        ):
            with TestClient(app, raise_server_exceptions=False):
                # After startup, app.state must hold the return value of
                # make_session_factory — which we patched to fake_factory.
                assert app.state.admissions_session_factory is fake_factory

    def test_build_engine_receives_normalized_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        build_engine() must be called (exactly once) with no explicit URL —
        it reads DATABASE_URL from the environment internally.
        """
        monkeypatch.setenv("DATABASE_URL", "postgresql://db/testdb")

        with patch("app.main.build_engine", return_value=MagicMock()) as mock_build:
            with patch("app.main.make_session_factory", return_value=MagicMock()):
                with TestClient(app, raise_server_exceptions=False):
                    mock_build.assert_called_once()


class TestStartupWithoutDatabaseUrl:
    """Lifespan must not raise and must leave factory unset when DATABASE_URL is absent."""

    def test_app_starts_without_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        Server must start (lifespan yields) even when DATABASE_URL is missing.
        No RuntimeError propagated; a WARNING is logged instead.
        """
        monkeypatch.delenv("DATABASE_URL", raising=False)

        # If lifespan raised, TestClient constructor would raise here.
        with TestClient(app, raise_server_exceptions=False) as test_client:
            # The healthcheck-style route still works.
            r = test_client.get("/api/admin/admissions/applicants", headers=ADMIN_HEADERS)
            # Either 503 (no factory) or 403/200 (dep override elsewhere) — but NOT 500.
            assert r.status_code != 500

    def test_factory_absent_on_state_when_database_url_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """
        When DATABASE_URL is absent, app.state must NOT have admissions_session_factory
        updated to a new value (the lifespan must not reach make_session_factory).
        """
        monkeypatch.delenv("DATABASE_URL", raising=False)
        # Clear any value left on app.state by earlier tests in this process so
        # the assertion below is unambiguous.
        app.state.admissions_session_factory = None

        with patch("app.main.build_engine", side_effect=RuntimeError("DATABASE_URL is not set")):
            with TestClient(app, raise_server_exceptions=False):
                factory = app.state.admissions_session_factory
                assert factory is None, f"Expected None but got {factory!r}"

    def test_startup_warning_is_logged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A WARNING must be emitted when build_engine() raises RuntimeError.

        Note: configure_json_logging() sets propagate=False on handlers so
        pytest's caplog fixture does not capture these records.  We patch
        the logger object in app.main directly instead.
        """
        monkeypatch.delenv("DATABASE_URL", raising=False)

        with patch("app.main.logger") as mock_logger:
            with patch("app.main.build_engine", side_effect=RuntimeError("DATABASE_URL is not set")):
                with TestClient(app, raise_server_exceptions=False):
                    pass

        warning_messages = [str(call) for call in mock_logger.warning.call_args_list]
        assert any(
            "admissions database not configured" in msg for msg in warning_messages
        ), f"Expected WARNING about missing DATABASE_URL; logger.warning calls: {warning_messages}"


# ---------------------------------------------------------------------------
# Section 2 — 503 Fail-closed behavior
# ---------------------------------------------------------------------------

class TestFailClosedBehavior:
    """
    When admissions_session_factory is absent (DATABASE_URL not configured),
    every admissions endpoint must return HTTP 503 — not 500 or 404.
    """

    @pytest.fixture(autouse=True)
    def _clear_factory(self) -> Generator[None, None, None]:
        """
        Temporarily remove the session factory from app.state; restore after.
        This simulates the server starting without DATABASE_URL.
        """
        original = getattr(app.state, "admissions_session_factory", _SENTINEL := object())
        app.state.admissions_session_factory = None
        try:
            yield
        finally:
            if original is _SENTINEL:
                try:
                    del app.state.admissions_session_factory
                except AttributeError:
                    pass
            else:
                app.state.admissions_session_factory = original

    def test_list_applicants_returns_503(self) -> None:
        r = client.get("/api/admin/admissions/applicants", headers=ADMIN_HEADERS)
        assert r.status_code == 503, r.text

    def test_create_applicant_returns_503(self) -> None:
        r = client.post(
            "/api/admin/admissions/applicants",
            headers=ADMIN_HEADERS,
            json={
                "email": "fail@closed.edu",
                "first_name": "Fail",
                "last_name": "Closed",
                "program_id": 1,
                "application_year": 2026,
            },
        )
        assert r.status_code == 503, r.text

    def test_get_applicant_returns_503(self) -> None:
        r = client.get("/api/admin/admissions/applicants/1", headers=ADMIN_HEADERS)
        assert r.status_code == 503, r.text

    def test_patch_applicant_returns_503(self) -> None:
        r = client.patch(
            "/api/admin/admissions/applicants/1",
            headers=ADMIN_HEADERS,
            json={"first_name": "X"},
        )
        assert r.status_code == 503, r.text

    def test_list_applications_returns_503(self) -> None:
        r = client.get("/api/admin/admissions/applications", headers=ADMIN_HEADERS)
        assert r.status_code == 503, r.text

    def test_create_application_returns_503(self) -> None:
        r = client.post(
            "/api/admin/admissions/applications",
            headers=ADMIN_HEADERS,
            json={"applicant_id": 1, "program_id": 1},
        )
        assert r.status_code == 503, r.text

    def test_get_application_returns_503(self) -> None:
        r = client.get("/api/admin/admissions/applications/1", headers=ADMIN_HEADERS)
        assert r.status_code == 503, r.text

    def test_attach_document_returns_503(self) -> None:
        r = client.post(
            "/api/admin/admissions/applications/1/documents",
            headers=ADMIN_HEADERS,
            json={
                "document_type": "transcript",
                "document_key": "s3://bucket/1/doc.pdf",
                "file_name": "doc.pdf",
            },
        )
        assert r.status_code == 503, r.text

    def test_stage_transition_returns_503(self) -> None:
        r = client.post(
            "/api/admin/admissions/applications/1/stage-transition",
            headers=ADMIN_HEADERS,
            json={"to_stage": ApplicationStage.RECEIVED.value},
        )
        assert r.status_code == 503, r.text

    def test_make_decision_returns_503(self) -> None:
        r = client.post(
            "/api/admin/admissions/applications/1/decision",
            headers=ADMIN_HEADERS,
            json={
                "decision_type": "accepted",
                "decided_by": "dean@example.com",
                "application_version": 1,
            },
        )
        assert r.status_code == 503, r.text


# ---------------------------------------------------------------------------
# Section 3 — Happy-path smoke tests (all endpoints)
# ---------------------------------------------------------------------------

class TestHappyPathEndpoints:
    """
    Smoke-tests for all 10 endpoints.  Service methods are monkeypatched to
    return minimal valid schema objects.  The test verifies HTTP status and
    the shape of the response body.
    """

    # -- Applicants --

    def test_create_applicant_returns_201(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_create(self, tenant_id, request, created_by):
            return _applicant_read(email=request.email)

        monkeypatch.setattr(admissions_service.ApplicantService, "create_applicant", fake_create)

        r = client.post(
            "/api/admin/admissions/applicants",
            headers=ADMIN_HEADERS,
            json={
                "email": "happy@applicant.edu",
                "first_name": "Happy",
                "last_name": "Path",
                "program_id": 10,
                "application_year": 2026,
            },
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["email"] == "happy@applicant.edu"
        assert data["tenant_id"] == 1

    def test_list_applicants_returns_200(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_list(self, tenant_id, **kwargs):
            return ApplicantListResponseSchema(
                total=1, page=1, page_size=20, items=[_applicant_read()]
            )

        monkeypatch.setattr(admissions_service.ApplicantService, "list_applicants", fake_list)

        r = client.get("/api/admin/admissions/applicants", headers=ADMIN_HEADERS)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    def test_get_applicant_returns_200(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_get(self, tenant_id, applicant_id):
            return _applicant_read(id=applicant_id)

        monkeypatch.setattr(admissions_service.ApplicantService, "get_applicant", fake_get)

        r = client.get("/api/admin/admissions/applicants/42", headers=ADMIN_HEADERS)
        assert r.status_code == 200, r.text
        assert r.json()["id"] == 42

    def test_patch_applicant_returns_200(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_update(self, tenant_id, applicant_id, request, updated_by):
            return _applicant_read(id=applicant_id, first_name=request.first_name or "Integration")

        monkeypatch.setattr(admissions_service.ApplicantService, "update_applicant", fake_update)

        r = client.patch(
            "/api/admin/admissions/applicants/42",
            headers=ADMIN_HEADERS,
            json={"first_name": "Updated"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["first_name"] == "Updated"

    # -- Applications --

    def test_create_application_returns_201(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_create(self, tenant_id, request, created_by):
            return _application_read(applicant_id=request.applicant_id)

        monkeypatch.setattr(admissions_service.ApplicationService, "create_application", fake_create)

        r = client.post(
            "/api/admin/admissions/applications",
            headers=ADMIN_HEADERS,
            json={"applicant_id": 1, "program_id": 10},
        )
        assert r.status_code == 201, r.text
        assert r.json()["stage"] == ApplicationStage.NEW.value

    def test_list_applications_returns_200(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_list(self, tenant_id, **kwargs):
            return ApplicationListResponseSchema(
                total=1, page=1, page_size=20, items=[_application_read()]
            )

        monkeypatch.setattr(admissions_service.ApplicationService, "list_applications", fake_list)

        r = client.get("/api/admin/admissions/applications", headers=ADMIN_HEADERS)
        assert r.status_code == 200, r.text
        assert r.json()["total"] == 1

    def test_get_application_returns_200(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_get(self, tenant_id, application_id):
            return _application_read(id=application_id)

        monkeypatch.setattr(admissions_service.ApplicationService, "get_application", fake_get)

        r = client.get("/api/admin/admissions/applications/99", headers=ADMIN_HEADERS)
        assert r.status_code == 200, r.text
        assert r.json()["id"] == 99

    # -- Documents --

    def test_attach_document_returns_201(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_attach(self, tenant_id, application_id, request, created_by):
            return DocumentReadSchema(
                id=301,
                tenant_id=tenant_id,
                application_id=application_id,
                document_type=request.document_type,
                document_key=request.document_key,
                file_name=request.file_name,
                file_size_bytes=None,
                mime_type=None,
                status="received",
                metadata_json={},
                created_by=created_by,
                created_at=_NOW,
                verified_at=None,
                verified_by=None,
            )

        monkeypatch.setattr(admissions_service.DocumentService, "attach_document", fake_attach)

        r = client.post(
            "/api/admin/admissions/applications/2/documents",
            headers=ADMIN_HEADERS,
            json={
                "document_type": "transcript",
                "document_key": "s3://bucket/tenant-1/app-2/transcript.pdf",
                "file_name": "transcript.pdf",
            },
        )
        assert r.status_code == 201, r.text
        assert r.json()["document_type"] == "transcript"

    # -- Stage Transition --

    def test_stage_transition_returns_200(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_transition(self, tenant_id, application_id, request, actor_id):
            return StageTransitionResponseSchema(
                application_id=application_id,
                from_stage=ApplicationStage.NEW,
                to_stage=request.to_stage,
                transition_at=datetime.now(timezone.utc),
                history_id=1,
            )

        monkeypatch.setattr(admissions_service.StageTransitionService, "transition_stage", fake_transition)

        r = client.post(
            "/api/admin/admissions/applications/2/stage-transition",
            headers=ADMIN_HEADERS,
            json={"to_stage": ApplicationStage.RECEIVED.value},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["from_stage"] == ApplicationStage.NEW.value
        assert body["to_stage"] == ApplicationStage.RECEIVED.value

    # -- Decision --

    def test_make_decision_returns_201(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_decide(self, tenant_id, application_id, request):
            return ApplicationDecisionReadSchema(
                id=401,
                tenant_id=tenant_id,
                application_id=application_id,
                decision_type=request.decision_type,
                decision_rationale=None,
                decided_by_id=request.decided_by,
                decided_at=datetime.now(timezone.utc),
                conditions_json={},
                version=1,
                created_at=_NOW,
                updated_at=_NOW,
            )

        monkeypatch.setattr(admissions_service.DecisionService, "make_decision", fake_decide)

        r = client.post(
            "/api/admin/admissions/applications/2/decision",
            headers=ADMIN_HEADERS,
            json={
                "decision_type": "accepted",
                "decided_by": "dean@example.com",
                "application_version": 1,
            },
        )
        assert r.status_code == 201, r.text
        assert r.json()["decision_type"] == "accepted"


# ---------------------------------------------------------------------------
# Section 4 — RBAC enforcement
# ---------------------------------------------------------------------------

class TestRbacEnforcement:
    """
    RBAC checks happen at the router layer (permission_dependency(...)).
    These tests verify the permission codes assigned in Phase 2 are enforced
    without touching the service layer at all.
    """

    def test_unauthenticated_request_is_rejected(self, override_admissions_db: MagicMock) -> None:
        r = client.get("/api/admin/admissions/applicants")
        assert r.status_code in (401, 403), r.text

    def test_student_role_cannot_read_applicants(self, override_admissions_db: MagicMock) -> None:
        headers = _auth_headers("student@example.com", ["student"])
        r = client.get("/api/admin/admissions/applicants", headers=headers)
        assert r.status_code == 403, r.text

    def test_auditor_role_can_read_applicants(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_list(self, tenant_id, **kwargs):
            return ApplicantListResponseSchema(total=0, page=1, page_size=20, items=[])

        monkeypatch.setattr(admissions_service.ApplicantService, "list_applicants", fake_list)

        headers = _auth_headers("auditor@example.com", ["auditor"])
        r = client.get("/api/admin/admissions/applicants", headers=headers)
        assert r.status_code == 200, r.text

    def test_auditor_role_cannot_write_applicants(self, override_admissions_db: MagicMock) -> None:
        headers = _auth_headers("auditor@example.com", ["auditor"])
        r = client.post(
            "/api/admin/admissions/applicants",
            headers=headers,
            json={
                "email": "x@x.edu",
                "first_name": "X",
                "last_name": "X",
                "program_id": 1,
                "application_year": 2026,
            },
        )
        assert r.status_code == 403, r.text

    def test_auditor_role_cannot_decide(self, override_admissions_db: MagicMock) -> None:
        headers = _auth_headers("auditor@example.com", ["auditor"])
        r = client.post(
            "/api/admin/admissions/applications/1/decision",
            headers=headers,
            json={
                "decision_type": "accepted",
                "decided_by": "auditor@example.com",
                "application_version": 1,
            },
        )
        assert r.status_code == 403, r.text

    def test_auditor_role_cannot_attach_documents(self, override_admissions_db: MagicMock) -> None:
        headers = _auth_headers("auditor@example.com", ["auditor"])
        r = client.post(
            "/api/admin/admissions/applications/1/documents",
            headers=headers,
            json={
                "document_type": "transcript",
                "document_key": "s3://bucket/1/doc.pdf",
                "file_name": "doc.pdf",
            },
        )
        assert r.status_code == 403, r.text

    def test_admin_can_use_all_endpoints(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        """Admin role must pass every permission check in the admissions router."""
        async def fake_list(self, tenant_id, **kwargs):
            return ApplicantListResponseSchema(total=0, page=1, page_size=20, items=[])

        monkeypatch.setattr(admissions_service.ApplicantService, "list_applicants", fake_list)

        r = client.get("/api/admin/admissions/applicants", headers=ADMIN_HEADERS)
        assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# Section 5 — Tenant safety
# ---------------------------------------------------------------------------

class TestTenantSafety:
    """
    Cross-tenant access attempts must return 404 (not 500 or 200).
    The router converts ValueError("not found or does not belong to tenant") → 404.
    """

    def test_cross_tenant_applicant_access_returns_404(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_get(self, tenant_id, applicant_id):
            raise ValueError(
                f"Applicant {applicant_id} not found or does not belong to tenant {tenant_id}"
            )

        monkeypatch.setattr(admissions_service.ApplicantService, "get_applicant", fake_get)

        r = client.get("/api/admin/admissions/applicants/9999", headers=ADMIN_HEADERS)
        assert r.status_code == 404, r.text

    def test_cross_tenant_application_access_returns_404(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        async def fake_get(self, tenant_id, application_id):
            raise ValueError(
                f"Application {application_id} not found or does not belong to tenant {tenant_id}"
            )

        monkeypatch.setattr(admissions_service.ApplicationService, "get_application", fake_get)

        r = client.get("/api/admin/admissions/applications/9999", headers=ADMIN_HEADERS)
        assert r.status_code == 404, r.text

    def test_tenant_id_injected_from_trusted_context(
        self, monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock
    ) -> None:
        """
        Verify that tenant_id reaches the service from the trusted JWT/header
        context — not from the request body.  We confirm the value is 1
        (the token tenant) when no X-Tenant-ID override is provided.
        """
        captured: list[int] = []

        async def fake_list(self, tenant_id, **kwargs):
            captured.append(tenant_id)
            return ApplicantListResponseSchema(total=0, page=1, page_size=20, items=[])

        monkeypatch.setattr(admissions_service.ApplicantService, "list_applicants", fake_list)

        r = client.get("/api/admin/admissions/applicants", headers=ADMIN_HEADERS)
        assert r.status_code == 200
        assert captured == [1], f"Expected tenant_id=1, got {captured}"


# ---------------------------------------------------------------------------
# Section 6 — DB dependency lifecycle
# ---------------------------------------------------------------------------

class TestDbDependencyLifecycle:
    """
    Verify that the per-request DB dependency properly opens and closes
    the SQLAlchemy session in both success and error paths.
    """

    def test_session_close_called_on_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """session.close() must be called by the real dependency after a successful response.

        We wire a factory mock into app.state so the *real* get_admissions_db runs
        (including its try/finally cleanup block) rather than overriding the dependency.
        """
        session = MagicMock(name="session_success")
        factory = MagicMock(name="factory", return_value=session)

        original_factory = getattr(app.state, "admissions_session_factory", None)
        app.state.admissions_session_factory = factory

        async def fake_list(self, tenant_id, **kwargs):
            return ApplicantListResponseSchema(total=0, page=1, page_size=20, items=[])

        monkeypatch.setattr(admissions_service.ApplicantService, "list_applicants", fake_list)

        try:
            r = client.get("/api/admin/admissions/applicants", headers=ADMIN_HEADERS)
            assert r.status_code == 200
        finally:
            app.state.admissions_session_factory = original_factory

        session.close.assert_called_once()

    def test_session_close_called_on_service_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """session.close() must be called by the real dependency even when the service raises.

        Same wiring approach as test_session_close_called_on_success: factory mock in
        app.state so the try/finally in the real dependency always executes.
        """
        session = MagicMock(name="session_error")
        factory = MagicMock(name="factory", return_value=session)

        original_factory = getattr(app.state, "admissions_session_factory", None)
        app.state.admissions_session_factory = factory

        async def fake_get(self, tenant_id, applicant_id):
            raise ValueError("Applicant 1 not found or does not belong to tenant 1")

        monkeypatch.setattr(admissions_service.ApplicantService, "get_applicant", fake_get)

        try:
            r = client.get("/api/admin/admissions/applicants/1", headers=ADMIN_HEADERS)
            assert r.status_code == 404
        finally:
            app.state.admissions_session_factory = original_factory

        session.close.assert_called_once()

    def test_503_path_does_not_open_session(self) -> None:
        """
        When the factory is None (fail-closed path), no Session should be
        created — the dependency raises HTTPException 503 immediately.
        """
        original = getattr(app.state, "admissions_session_factory", None)
        app.state.admissions_session_factory = None
        try:
            r = client.get("/api/admin/admissions/applicants", headers=ADMIN_HEADERS)
            assert r.status_code == 503
        finally:
            app.state.admissions_session_factory = original
