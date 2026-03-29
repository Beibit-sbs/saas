"""Tests for Semantic Context Layer v1."""
from __future__ import annotations

from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, INTERNAL_HEADERS, client

from app.platform.context import service as context_service
from app.platform.context.repository import ContextRepository
from app.platform.context.service import ContextService
from app.platform.context.service import context_service as _ctx_svc_instance
from app.platform.events.handlers.context_projection_handler import ContextProjectionHandler
from app.platform.events.schemas import OutboxEventRead
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _create_tenant(prefix: str = "ctx") -> int:
    tenant = tenant_service.create_tenant(
        f"{prefix}-{uuid4().hex[:8]}",
        f"{prefix.title()} Tenant",
    )
    return int(tenant["tenant_id"])


def _make_event(
    *,
    tenant_id: int,
    event_type: str,
    payload: dict | None = None,
    event_id: int = 1,
) -> OutboxEventRead:
    return OutboxEventRead(
        id=event_id,
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type=event_type.split(".")[0],
        aggregate_id=str(event_id),
        payload_json=payload or {},
        status="pending",
        retry_count=0,
        available_at="2026-01-01T00:00:00+00:00",
        created_at="2026-01-01T00:00:00+00:00",
    )


# ------------------------------------------------------------------ #
#  1. Create student context entity                                    #
# ------------------------------------------------------------------ #

def test_upsert_entity_creates_student_context(reset_shared_state) -> None:
    tenant_id = _create_tenant()

    entity = context_service.upsert_entity(
        tenant_id=tenant_id,
        entity_type="student",
        entity_id="stu-001",
        data_json={"name": "Alice", "program_id": "prog-1"},
    )

    assert entity["tenant_id"] == tenant_id
    assert entity["entity_type"] == "student"
    assert entity["entity_id"] == "stu-001"
    assert entity["data_json"]["name"] == "Alice"
    assert entity["id"] > 0


def test_upsert_entity_updates_on_duplicate(reset_shared_state) -> None:
    tenant_id = _create_tenant()

    context_service.upsert_entity(
        tenant_id=tenant_id,
        entity_type="student",
        entity_id="stu-001",
        data_json={"name": "Alice"},
    )
    updated = context_service.upsert_entity(
        tenant_id=tenant_id,
        entity_type="student",
        entity_id="stu-001",
        data_json={"name": "Alice Updated", "gpa": 3.8},
    )

    assert updated["data_json"]["name"] == "Alice Updated"
    assert updated["data_json"]["gpa"] == 3.8
    # Same entity id — no duplicate created
    repo = _ctx_svc_instance._repository
    assert sum(
        1 for k in repo._entities if k[0] == tenant_id and k[1] == "student"
    ) == 1


# ------------------------------------------------------------------ #
#  2. Project events into context relations                            #
# ------------------------------------------------------------------ #

def test_project_student_created_event(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    handler = ContextProjectionHandler()

    event = _make_event(
        tenant_id=tenant_id,
        event_type="student.created",
        payload={"id": "42", "name": "Bob", "program_id": "prog-99"},
    )

    with UnitOfWork() as uow:
        result = handler.handle(event, uow=uow)

    assert result["status"] == "processed"
    assert result["event_type"] == "student.created"

    # Student entity was created
    student = _ctx_svc_instance._repository.get_entity(
        tenant_id=tenant_id, entity_type="student", entity_id="42"
    )
    assert student is not None
    assert student["data_json"]["name"] == "Bob"

    # student → program relation was created
    rels = _ctx_svc_instance._repository.get_relations_by_source(
        tenant_id=tenant_id,
        source_entity_type="student",
        source_entity_id="42",
        relation_type="enrolled_in",
    )
    assert len(rels) == 1
    assert rels[0]["target_entity_type"] == "program"
    assert rels[0]["target_entity_id"] == "prog-99"


def test_project_enrollment_created_event(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    handler = ContextProjectionHandler()

    event = _make_event(
        tenant_id=tenant_id,
        event_type="enrollment.created",
        payload={"id": "enr-10", "student_id": "stu-5", "course_id": "crs-3"},
    )

    with UnitOfWork() as uow:
        handler.handle(event, uow=uow)

    # Enrollment entity exists
    enr = _ctx_svc_instance._repository.get_entity(
        tenant_id=tenant_id, entity_type="enrollment", entity_id="enr-10"
    )
    assert enr is not None

    # student → enrollment relation
    rels_enr = _ctx_svc_instance._repository.get_relations_by_source(
        tenant_id=tenant_id,
        source_entity_type="student",
        source_entity_id="stu-5",
        relation_type="has_enrollment",
    )
    assert len(rels_enr) == 1
    assert rels_enr[0]["target_entity_id"] == "enr-10"

    # enrollment → course relation
    rels_course = _ctx_svc_instance._repository.get_relations_by_source(
        tenant_id=tenant_id,
        source_entity_type="enrollment",
        source_entity_id="enr-10",
        relation_type="for_course",
    )
    assert len(rels_course) == 1
    assert rels_course[0]["target_entity_id"] == "crs-3"


def test_project_grade_submitted_event(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    handler = ContextProjectionHandler()

    event = _make_event(
        tenant_id=tenant_id,
        event_type="grade.submitted",
        payload={"id": "grd-77", "student_id": "stu-5", "grade_value": 92},
    )

    with UnitOfWork() as uow:
        handler.handle(event, uow=uow)

    grade = _ctx_svc_instance._repository.get_entity(
        tenant_id=tenant_id, entity_type="grade", entity_id="grd-77"
    )
    assert grade is not None

    rels = _ctx_svc_instance._repository.get_relations_by_source(
        tenant_id=tenant_id,
        source_entity_type="student",
        source_entity_id="stu-5",
        relation_type="has_grade",
    )
    assert len(rels) == 1
    assert rels[0]["target_entity_id"] == "grd-77"


def test_project_advisor_assigned_event(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    handler = ContextProjectionHandler()

    event = _make_event(
        tenant_id=tenant_id,
        event_type="advisor.assigned",
        payload={"student_id": "stu-5", "advisor_id": "adv-1"},
    )

    with UnitOfWork() as uow:
        handler.handle(event, uow=uow)

    advisor = _ctx_svc_instance._repository.get_entity(
        tenant_id=tenant_id, entity_type="advisor", entity_id="adv-1"
    )
    assert advisor is not None

    rels = _ctx_svc_instance._repository.get_relations_by_source(
        tenant_id=tenant_id,
        source_entity_type="student",
        source_entity_id="stu-5",
        relation_type="advised_by",
    )
    assert len(rels) == 1
    assert rels[0]["target_entity_id"] == "adv-1"


def test_project_course_created_event(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    handler = ContextProjectionHandler()

    event = _make_event(
        tenant_id=tenant_id,
        event_type="course.created",
        payload={"id": "crs-99", "title": "Advanced AI", "department_id": "dept-3"},
    )

    with UnitOfWork() as uow:
        handler.handle(event, uow=uow)

    course = _ctx_svc_instance._repository.get_entity(
        tenant_id=tenant_id, entity_type="course", entity_id="crs-99"
    )
    assert course is not None
    assert course["data_json"]["title"] == "Advanced AI"

    dept = _ctx_svc_instance._repository.get_entity(
        tenant_id=tenant_id, entity_type="department", entity_id="dept-3"
    )
    assert dept is not None


def test_unknown_event_type_is_ignored(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    handler = ContextProjectionHandler()

    event = _make_event(
        tenant_id=tenant_id,
        event_type="some.unknown.event",
        payload={"id": "x"},
    )

    with UnitOfWork() as uow:
        result = handler.handle(event, uow=uow)

    assert result["status"] == "processed"
    # No entities created
    assert len(_ctx_svc_instance._repository._entities) == 0


# ------------------------------------------------------------------ #
#  3. Query student profile                                            #
# ------------------------------------------------------------------ #

def test_build_student_profile_returns_full_profile(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    repo = ContextRepository()
    svc = ContextService(repository=repo)

    # Build context manually
    repo.upsert_entity(tenant_id=tenant_id, entity_type="student", entity_id="s1",
                       data_json={"name": "Carol"})
    repo.upsert_entity(tenant_id=tenant_id, entity_type="program", entity_id="p1",
                       data_json={"name": "CS"})
    repo.upsert_entity(tenant_id=tenant_id, entity_type="advisor", entity_id="a1",
                       data_json={"name": "Dr. Smith"})
    repo.upsert_entity(tenant_id=tenant_id, entity_type="enrollment", entity_id="e1",
                       data_json={"course_id": "c1"})
    repo.upsert_entity(tenant_id=tenant_id, entity_type="grade", entity_id="g1",
                       data_json={"value": 95})
    repo.upsert_entity(tenant_id=tenant_id, entity_type="department", entity_id="d1",
                       data_json={"name": "Computer Science"})

    repo.upsert_relation(tenant_id=tenant_id,
                         source_entity_type="student", source_entity_id="s1",
                         relation_type="enrolled_in",
                         target_entity_type="program", target_entity_id="p1")
    repo.upsert_relation(tenant_id=tenant_id,
                         source_entity_type="student", source_entity_id="s1",
                         relation_type="advised_by",
                         target_entity_type="advisor", target_entity_id="a1")
    repo.upsert_relation(tenant_id=tenant_id,
                         source_entity_type="student", source_entity_id="s1",
                         relation_type="has_enrollment",
                         target_entity_type="enrollment", target_entity_id="e1")
    repo.upsert_relation(tenant_id=tenant_id,
                         source_entity_type="student", source_entity_id="s1",
                         relation_type="has_grade",
                         target_entity_type="grade", target_entity_id="g1")
    repo.upsert_relation(tenant_id=tenant_id,
                         source_entity_type="department", source_entity_id="d1",
                         relation_type="has_student",
                         target_entity_type="student", target_entity_id="s1")

    profile = svc.build_student_profile(student_id="s1", tenant_id=tenant_id)

    assert profile["student"] is not None
    assert profile["student"]["data_json"]["name"] == "Carol"
    assert profile["program"] is not None
    assert profile["program"]["data_json"]["name"] == "CS"
    assert profile["advisor"] is not None
    assert profile["advisor"]["data_json"]["name"] == "Dr. Smith"
    assert len(profile["enrollments"]) == 1
    assert len(profile["grades"]) == 1
    assert profile["grades"][0]["data_json"]["value"] == 95
    assert profile["department"] is not None
    assert profile["department"]["data_json"]["name"] == "Computer Science"
    assert isinstance(profile["automation_flags"], dict)


def test_build_student_profile_missing_student_returns_none_fields(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    repo = ContextRepository()
    svc = ContextService(repository=repo)

    profile = svc.build_student_profile(student_id="nonexistent", tenant_id=tenant_id)

    assert profile["student"] is None
    assert profile["program"] is None
    assert profile["advisor"] is None
    assert profile["enrollments"] == []
    assert profile["grades"] == []
    assert profile["department"] is None


# ------------------------------------------------------------------ #
#  4. Tenant isolation                                                 #
# ------------------------------------------------------------------ #

def test_tenant_isolation_entities(reset_shared_state) -> None:
    tenant_a = _create_tenant("ctx-a")
    tenant_b = _create_tenant("ctx-b")

    context_service.upsert_entity(
        tenant_id=tenant_a,
        entity_type="student",
        entity_id="s1",
        data_json={"name": "Alice"},
    )

    # Tenant B cannot see tenant A's entity
    entity_b = _ctx_svc_instance._repository.get_entity(
        tenant_id=tenant_b, entity_type="student", entity_id="s1"
    )
    assert entity_b is None

    entity_a = _ctx_svc_instance._repository.get_entity(
        tenant_id=tenant_a, entity_type="student", entity_id="s1"
    )
    assert entity_a is not None


def test_tenant_isolation_relations(reset_shared_state) -> None:
    tenant_a = _create_tenant("ctx-c")
    tenant_b = _create_tenant("ctx-d")

    context_service.upsert_relation(
        tenant_id=tenant_a,
        source_entity_type="student", source_entity_id="s1",
        relation_type="enrolled_in",
        target_entity_type="program", target_entity_id="p1",
    )

    rels_b = _ctx_svc_instance._repository.get_relations_by_source(
        tenant_id=tenant_b,
        source_entity_type="student",
        source_entity_id="s1",
        relation_type="enrolled_in",
    )
    assert len(rels_b) == 0

    rels_a = _ctx_svc_instance._repository.get_relations_by_source(
        tenant_id=tenant_a,
        source_entity_type="student",
        source_entity_id="s1",
        relation_type="enrolled_in",
    )
    assert len(rels_a) == 1


# ------------------------------------------------------------------ #
#  5. Relation integrity                                               #
# ------------------------------------------------------------------ #

def test_upsert_relation_is_idempotent(reset_shared_state) -> None:
    tenant_id = _create_tenant()

    for _ in range(3):
        rel = context_service.upsert_relation(
            tenant_id=tenant_id,
            source_entity_type="student",
            source_entity_id="s1",
            relation_type="enrolled_in",
            target_entity_type="program",
            target_entity_id="p1",
            metadata_json={"term": "2026-spring"},
        )

    rels = _ctx_svc_instance._repository.get_relations_by_source(
        tenant_id=tenant_id,
        source_entity_type="student",
        source_entity_id="s1",
        relation_type="enrolled_in",
    )
    # Only ONE relation should exist (upsert semantics)
    assert len(rels) == 1
    assert rels[0]["metadata_json"]["term"] == "2026-spring"


def test_get_relations_by_target(reset_shared_state) -> None:
    tenant_id = _create_tenant()

    context_service.upsert_relation(
        tenant_id=tenant_id,
        source_entity_type="department",
        source_entity_id="dept-1",
        relation_type="has_student",
        target_entity_type="student",
        target_entity_id="s1",
    )
    context_service.upsert_relation(
        tenant_id=tenant_id,
        source_entity_type="department",
        source_entity_id="dept-1",
        relation_type="has_student",
        target_entity_type="student",
        target_entity_id="s2",
    )

    dept_rels = _ctx_svc_instance._repository.get_relations_by_target(
        tenant_id=tenant_id,
        target_entity_type="student",
        target_entity_id="s1",
        relation_type="has_student",
    )
    assert len(dept_rels) == 1
    assert dept_rels[0]["source_entity_id"] == "dept-1"


def test_repository_high_level_queries(reset_shared_state) -> None:
    tenant_id = _create_tenant()
    repo = ContextRepository()

    repo.upsert_entity(tenant_id=tenant_id, entity_type="student", entity_id="s1",
                       data_json={"name": "Dave"})
    repo.upsert_entity(tenant_id=tenant_id, entity_type="student", entity_id="s2",
                       data_json={"name": "Eve"})
    repo.upsert_entity(tenant_id=tenant_id, entity_type="program", entity_id="p1",
                       data_json={"name": "Math"})
    repo.upsert_relation(tenant_id=tenant_id,
                         source_entity_type="student", source_entity_id="s1",
                         relation_type="enrolled_in",
                         target_entity_type="program", target_entity_id="p1")
    repo.upsert_relation(tenant_id=tenant_id,
                         source_entity_type="student", source_entity_id="s2",
                         relation_type="enrolled_in",
                         target_entity_type="program", target_entity_id="p1")

    students = repo.get_program_students(tenant_id=tenant_id, program_id="p1")
    assert len(students) == 2
    names = {s["data_json"]["name"] for s in students}
    assert names == {"Dave", "Eve"}


# ------------------------------------------------------------------ #
#  6. API endpoints                                                    #
# ------------------------------------------------------------------ #

def test_admin_context_student_endpoint_returns_profile(reset_shared_state) -> None:
    tenant_id = _create_tenant()

    context_service.upsert_entity(
        tenant_id=tenant_id,
        entity_type="student",
        entity_id="api-stu-1",
        data_json={"name": "Frank"},
    )

    resp = client.get(
        f"/api/v1/admin/platform/context/student/api-stu-1?tenant_id={tenant_id}",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["student"] is not None
    assert body["student"]["data_json"]["name"] == "Frank"
    assert "enrollments" in body
    assert "grades" in body
    assert "automation_flags" in body


def test_internal_context_student_endpoint_returns_profile(reset_shared_state) -> None:
    tenant_id = _create_tenant()

    context_service.upsert_entity(
        tenant_id=tenant_id,
        entity_type="student",
        entity_id="int-stu-1",
        data_json={"name": "Grace"},
    )

    resp = client.get(
        f"/api/v1/internal/context/student/int-stu-1?tenant_id={tenant_id}",
        headers=INTERNAL_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["student"]["data_json"]["name"] == "Grace"
