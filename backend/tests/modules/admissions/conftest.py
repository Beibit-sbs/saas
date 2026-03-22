import asyncio
from collections.abc import Callable
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.modules.admissions.models import (
    ApplicantModel,
    ApplicationDecisionModel,
    ApplicationDocumentModel,
    ApplicationModel,
    ApplicationStageHistoryModel,
)
from app.modules.admissions.schemas import (
    ApplicationConclusionType,
    ApplicationStage,
    DocumentStatus,
)
from app.modules.admissions import service as admissions_service


class ScalarListResult:
    def __init__(self, items: list[object]):
        self._items = items

    def all(self) -> list[object]:
        return list(self._items)


class ExecuteResult:
    def __init__(
        self,
        *,
        scalar_one_or_none: object | None = None,
        scalar: object | None = None,
        scalars: list[object] | None = None,
    ):
        self._scalar_one_or_none = scalar_one_or_none
        self._scalar = scalar
        self._scalars = scalars or []

    def scalar_one_or_none(self) -> object | None:
        return self._scalar_one_or_none

    def scalar(self) -> object | None:
        return self._scalar

    def scalars(self) -> ScalarListResult:
        return ScalarListResult(self._scalars)


@pytest.fixture
def run_async() -> Callable:
    return asyncio.run


@pytest.fixture
def db_session() -> MagicMock:
    session = MagicMock(spec=Session)

    def fake_refresh(instance: object) -> None:
        now = datetime(2026, 3, 22, 12, 0, 0, tzinfo=timezone.utc)
        if getattr(instance, "id", None) is None:
            defaults = {
                "ApplicantModel": 101,
                "ApplicationModel": 201,
                "ApplicationDocumentModel": 301,
                "ApplicationStageHistoryModel": 401,
                "ApplicationDecisionModel": 501,
            }
            instance.id = defaults.get(instance.__class__.__name__, 1)
        if hasattr(instance, "created_at") and getattr(instance, "created_at", None) is None:
            instance.created_at = now
        if hasattr(instance, "updated_at") and getattr(instance, "updated_at", None) is None:
            instance.updated_at = now
        if hasattr(instance, "version") and getattr(instance, "version", None) is None:
            instance.version = 1
        if hasattr(instance, "decided_at") and getattr(instance, "decided_at", None) is None:
            instance.decided_at = now

    session.refresh.side_effect = fake_refresh
    return session


@pytest.fixture
def audit_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    calls: list[dict] = []

    def fake_log_admin_action(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(admissions_service, "log_admin_action", fake_log_admin_action)
    return calls


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 3, 22, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def applicant_factory(now: datetime):
    def factory(**overrides) -> ApplicantModel:
        return ApplicantModel(
            id=overrides.get("id", 101),
            tenant_id=overrides.get("tenant_id", 1),
            email=overrides.get("email", "student@example.com"),
            first_name=overrides.get("first_name", "Ada"),
            last_name=overrides.get("last_name", "Lovelace"),
            phone=overrides.get("phone", "+10000000000"),
            program_id=overrides.get("program_id", 501),
            application_year=overrides.get("application_year", 2026),
            status=overrides.get("status", "active"),
            external_id=overrides.get("external_id", "sis-101"),
            metadata_json=overrides.get("metadata_json", {"citizenship": "US"}),
            created_by=overrides.get("created_by", "owner@example.com"),
            created_at=overrides.get("created_at", now),
            updated_at=overrides.get("updated_at", now),
        )

    return factory


@pytest.fixture
def application_factory(now: datetime):
    def factory(**overrides) -> ApplicationModel:
        return ApplicationModel(
            id=overrides.get("id", 201),
            tenant_id=overrides.get("tenant_id", 1),
            applicant_id=overrides.get("applicant_id", 101),
            program_id=overrides.get("program_id", 501),
            stage=overrides.get("stage", ApplicationStage.NEW.value),
            conclusion_type=overrides.get("conclusion_type"),
            received_at=overrides.get("received_at"),
            decision_at=overrides.get("decision_at"),
            version=overrides.get("version", 1),
            metadata_json=overrides.get("metadata_json", {}),
            created_by=overrides.get("created_by", "owner@example.com"),
            created_at=overrides.get("created_at", now),
            updated_at=overrides.get("updated_at", now),
        )

    return factory


@pytest.fixture
def document_factory(now: datetime):
    def factory(**overrides) -> ApplicationDocumentModel:
        return ApplicationDocumentModel(
            id=overrides.get("id", 301),
            tenant_id=overrides.get("tenant_id", 1),
            application_id=overrides.get("application_id", 201),
            document_type=overrides.get("document_type", "transcript"),
            document_key=overrides.get("document_key", "s3://tenant-1/app-201/transcript.pdf"),
            file_name=overrides.get("file_name", "transcript.pdf"),
            file_size_bytes=overrides.get("file_size_bytes", 4096),
            mime_type=overrides.get("mime_type", "application/pdf"),
            status=overrides.get("status", DocumentStatus.RECEIVED.value),
            metadata_json=overrides.get("metadata_json", {}),
            created_by=overrides.get("created_by", "owner@example.com"),
            created_at=overrides.get("created_at", now),
            verified_at=overrides.get("verified_at"),
            verified_by=overrides.get("verified_by"),
        )

    return factory


@pytest.fixture
def stage_history_factory(now: datetime):
    def factory(**overrides) -> ApplicationStageHistoryModel:
        return ApplicationStageHistoryModel(
            id=overrides.get("id", 401),
            tenant_id=overrides.get("tenant_id", 1),
            application_id=overrides.get("application_id", 201),
            from_stage=overrides.get("from_stage", ApplicationStage.NEW.value),
            to_stage=overrides.get("to_stage", ApplicationStage.RECEIVED.value),
            reason=overrides.get("reason", "submission received"),
            actor_id=overrides.get("actor_id", "reviewer@example.com"),
            action_type=overrides.get("action_type", "manual"),
            metadata_json=overrides.get("metadata_json", {}),
            created_at=overrides.get("created_at", now),
        )

    return factory


@pytest.fixture
def decision_factory(now: datetime):
    def factory(**overrides) -> ApplicationDecisionModel:
        return ApplicationDecisionModel(
            id=overrides.get("id", 501),
            tenant_id=overrides.get("tenant_id", 1),
            application_id=overrides.get("application_id", 201),
            decision_type=overrides.get("decision_type", ApplicationConclusionType.ACCEPTED.value),
            decision_rationale=overrides.get("decision_rationale", "Strong portfolio"),
            decided_by_id=overrides.get("decided_by_id", "dean@example.com"),
            decided_at=overrides.get("decided_at", now),
            conditions_json=overrides.get("conditions_json", {}),
            version=overrides.get("version", 1),
            created_at=overrides.get("created_at", now),
            updated_at=overrides.get("updated_at", now),
        )

    return factory