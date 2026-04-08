from __future__ import annotations

from uuid import uuid4

from tests.conftest import _auth_headers, client

from app.platform.ai import service as ai_service
from app.platform.context import service as context_service
from app.platform.education_graph import service as education_graph_service
from app.platform.events.publisher import EventPublisher
from app.platform.events.worker import OutboxEventWorker
from app.platform.tenant import service as tenant_service
from app.platform.uow import UnitOfWork


def _create_tenant(prefix: str = "graph") -> int:
    tenant = tenant_service.create_tenant(f"{prefix}-{uuid4().hex[:8]}", "Education Graph Tenant")
    return int(tenant["tenant_id"])


def test_skill_crud_and_taxonomy_storage(reset_shared_state) -> None:
    tenant_id = _create_tenant("skills")

    with UnitOfWork() as uow:
        skill_math = education_graph_service.create_skill(
            tenant_id=tenant_id,
            skill_key="linear_algebra",
            name="Linear Algebra",
            description="Vectors, matrices and transforms",
            category="Mathematics",
            level="intermediate",
            uow=uow,
        )
        skill_py = education_graph_service.create_skill(
            tenant_id=tenant_id,
            skill_key="python",
            name="Python",
            description="Python programming",
            category="Programming",
            level="advanced",
            uow=uow,
        )
        rows = education_graph_service.list_skills(tenant_id=tenant_id, uow=uow)

    assert skill_math["tenant_id"] == tenant_id
    assert skill_py["tenant_id"] == tenant_id
    assert {r["skill_key"] for r in rows} == {"linear_algebra", "python"}
    assert {r["category"] for r in rows} == {"Mathematics", "Programming"}


def test_course_skill_mapping_and_listing(reset_shared_state) -> None:
    tenant_id = _create_tenant("course-map")

    with UnitOfWork() as uow:
        python_skill = education_graph_service.create_skill(
            tenant_id=tenant_id,
            skill_key="python",
            name="Python",
            description="",
            category="Programming",
            level=None,
            uow=uow,
        )
        stats_skill = education_graph_service.create_skill(
            tenant_id=tenant_id,
            skill_key="statistics",
            name="Statistics",
            description="",
            category="Data Science",
            level=None,
            uow=uow,
        )

        education_graph_service.map_course_skill(
            tenant_id=tenant_id,
            course_id="course_ml_101",
            skill_id=int(python_skill["id"]),
            weight=1.5,
            uow=uow,
        )
        education_graph_service.map_course_skill(
            tenant_id=tenant_id,
            course_id="course_ml_101",
            skill_id=int(stats_skill["id"]),
            weight=2.0,
            uow=uow,
        )
        mappings = education_graph_service.list_course_skills(
            tenant_id=tenant_id,
            course_id="course_ml_101",
            uow=uow,
        )

    assert len(mappings) == 2
    assert {m["skill_key"] for m in mappings} == {"python", "statistics"}


def test_event_driven_skill_inference_via_outbox_worker(reset_shared_state) -> None:
    tenant_id = _create_tenant("inference")

    with UnitOfWork() as uow:
        python_skill = education_graph_service.create_skill(
            tenant_id=tenant_id,
            skill_key="python",
            name="Python",
            description="",
            category="Programming",
            level=None,
            uow=uow,
        )
        education_graph_service.map_course_skill(
            tenant_id=tenant_id,
            course_id="course_ml_101",
            skill_id=int(python_skill["id"]),
            weight=1.25,
            uow=uow,
        )

        # Context projection lookup for enrollment -> course path used by inference
        context_service.upsert_entity(
            tenant_id=tenant_id,
            entity_type="enrollment",
            entity_id="2001",
            data_json={"enrollment_id": "2001", "course_id": "course_ml_101"},
            conn=uow.conn,
        )

        publisher = EventPublisher(uow=uow)
        publisher.publish_event(
            tenant_id=tenant_id,
            event_type="grade.submitted",
            aggregate_type="grade_submission",
            aggregate_id="9001",
            payload_json={
                "enrollment_id": "2001",
                "student_profile_id": "stu-001",
                "grade_points": "88",
            },
        )

    worker = OutboxEventWorker()
    result = worker.run_once()
    assert result["succeeded"] >= 1

    with UnitOfWork() as uow:
        student_skills = education_graph_service.list_student_skills(
            tenant_id=tenant_id,
            student_id="stu-001",
            uow=uow,
        )

    assert len(student_skills) == 1
    assert student_skills[0]["skill_key"] == "python"
    assert float(student_skills[0]["proficiency_level"]) >= 1.25


def test_tenant_isolation_for_student_skill_reads(reset_shared_state) -> None:
    tenant_a = _create_tenant("iso-a")
    tenant_b = _create_tenant("iso-b")

    with UnitOfWork() as uow:
        skill_a = education_graph_service.create_skill(
            tenant_id=tenant_a,
            skill_key="ml_fundamentals",
            name="ML Fundamentals",
            description="",
            category="AI",
            level=None,
            uow=uow,
        )
        education_graph_service.map_course_skill(
            tenant_id=tenant_a,
            course_id="course_a",
            skill_id=int(skill_a["id"]),
            weight=1.0,
            uow=uow,
        )
        uow.education_graph_repository.upsert_student_skill(
            tenant_id=tenant_a,
            student_id="stu-a",
            skill_id=int(skill_a["id"]),
            proficiency_delta=1.0,
            source="manual",
            conn=uow.conn,
        )

    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"])

    rows_a = client.get(
        f"/api/v1/admin/student-skills?tenant_id={tenant_a}",
        headers={**platform_headers, "X-Tenant-ID": str(tenant_a)},
    )
    rows_b = client.get(
        f"/api/v1/admin/student-skills?tenant_id={tenant_b}",
        headers={**platform_headers, "X-Tenant-ID": str(tenant_b)},
    )

    assert rows_a.status_code == 200, rows_a.text
    assert rows_b.status_code == 200, rows_b.text
    assert len(rows_a.json()) == 1
    assert rows_b.json() == []


def test_admin_skill_and_course_skill_endpoints_enforce_tenant_guard(reset_shared_state) -> None:
    tenant_id = _create_tenant("api-guard")
    platform_headers = _auth_headers("platform.root@example.com", ["superadmin"])

    create_skill_resp = client.post(
        "/api/v1/admin/skills",
        headers={**platform_headers, "X-Tenant-ID": str(tenant_id)},
        json={
            "tenant_id": tenant_id,
            "skill_key": "linear_algebra",
            "name": "Linear Algebra",
            "description": "",
            "category": "Mathematics",
            "level": "intermediate",
        },
    )
    assert create_skill_resp.status_code == 201, create_skill_resp.text
    skill_id = int(create_skill_resp.json()["id"])

    map_resp = client.post(
        "/api/v1/admin/course-skills",
        headers={**platform_headers, "X-Tenant-ID": str(tenant_id)},
        json={
            "tenant_id": tenant_id,
            "course_id": "course_math_101",
            "skill_id": skill_id,
            "weight": 2.0,
        },
    )
    assert map_resp.status_code == 201, map_resp.text

    denied = client.get(
        f"/api/v1/admin/skills?tenant_id={tenant_id}",
        headers={**platform_headers, "X-Tenant-ID": str(tenant_id + 1)},
    )
    assert denied.status_code in {403, 404}


def test_ai_retrieval_student_skills_profile_uses_graph_service(reset_shared_state) -> None:
    tenant_id = _create_tenant("ai-skill")

    with UnitOfWork() as uow:
        skill = education_graph_service.create_skill(
            tenant_id=tenant_id,
            skill_key="python",
            name="Python",
            description="",
            category="Programming",
            level=None,
            uow=uow,
        )
        uow.education_graph_repository.upsert_student_skill(
            tenant_id=tenant_id,
            student_id="stu-ai-1",
            skill_id=int(skill["id"]),
            proficiency_delta=2.5,
            source="manual",
            conn=uow.conn,
        )

    answer = ai_service.answer_question(
        tenant_id=tenant_id,
        actor_id="admin@example.com",
        question="student skills profile for student stu-ai-1",
        context={"student_id": "stu-ai-1"},
    )

    assert "summary" in answer
    assert any(src.get("source_type") == "education_graph" for src in answer.get("sources", []))
    assert any("Python" in str(i.get("title", "")) for i in answer.get("insights", []))
