from __future__ import annotations

import re
from typing import Any

from app.modules.integrations.service import get_runtime_value
from app.platform.analytics import service as analytics_service
from app.platform.automation import service as automation_service
from app.platform.context import service as context_service
from app.platform.education_graph import service as education_graph_service
from app.platform.kpi import service as kpi_service


def _card_value(dashboard: dict[str, Any], metric_key: str) -> int:
    for card in list(dashboard.get("cards") or []):
        if str(card.get("metric_key")) == metric_key:
            return int(card.get("value") or 0)
    return 0


def retrieve_kpi_overview(*, tenant_id: int, question: str, uow: Any) -> dict[str, Any]:
    dashboard = kpi_service.get_rector_dashboard(tenant_id=tenant_id, uow=uow)

    lower_q = question.lower()
    if "enrollment" in lower_q:
        metric_key = "total_enrollments"
        title = "Enrollments Created"
    elif "grade" in lower_q:
        metric_key = "total_grades_submitted"
        title = "Grades Submitted"
    else:
        metric_key = "total_students"
        title = "Current Students"

    value = _card_value(dashboard, metric_key)

    insights = [
        {
            "title": title,
            "value": str(value),
            "explanation": f"Derived from KPI dashboard metric '{metric_key}'.",
        }
    ]
    return {
        "summary": f"{title}: {value}.",
        "insights": insights,
        "sources": [
            {"source_type": "kpi", "reference": f"dashboard:{metric_key}"},
        ],
        "warnings": [],
    }


def retrieve_latest_kpi_summary(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    dashboard = kpi_service.get_rector_dashboard(tenant_id=tenant_id, uow=uow)
    cards = list(dashboard.get("cards") or [])

    insights = [
        {
            "title": str(card.get("title") or card.get("metric_key") or "metric"),
            "value": str(card.get("value") or 0),
            "explanation": "Latest KPI dashboard snapshot.",
        }
        for card in cards[:6]
    ]

    return {
        "summary": "Latest KPI summary loaded.",
        "insights": insights,
        "sources": [{"source_type": "kpi", "reference": "dashboard:latest"}],
        "warnings": [],
    }


def retrieve_automation_health(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    executions = automation_service.list_executions(tenant_id=tenant_id, uow=uow, limit=200)
    failed = [item for item in executions if str(item.status).lower() == "failed"]

    failed_by_rule: dict[int, int] = {}
    for item in failed:
        failed_by_rule[int(item.rule_id)] = failed_by_rule.get(int(item.rule_id), 0) + 1

    insights = [
        {
            "title": "Failed Automation Executions",
            "value": str(len(failed)),
            "explanation": "Executions with status='failed' in tenant scope.",
        }
    ]

    if failed_by_rule:
        top_rule_id, top_count = sorted(failed_by_rule.items(), key=lambda pair: pair[1], reverse=True)[0]
        insights.append(
            {
                "title": "Most Failing Rule",
                "value": f"rule_id={top_rule_id}",
                "explanation": f"Observed failures: {top_count}.",
            }
        )

    return {
        "summary": "Automation health checked.",
        "insights": insights,
        "sources": [{"source_type": "automation", "reference": "executions:last_200"}],
        "warnings": [] if failed else ["no_automation_failures_detected"],
    }


def retrieve_platform_health(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    latest_kpis = analytics_service.get_latest_tenant_kpis(tenant_id=tenant_id, uow=uow) or {}
    failed_jobs = uow.job_repository.list_for_tenant(tenant_id, status="failed", limit=500, conn=uow.conn)
    notifications = uow.notification_repository.list_for_tenant(tenant_id, limit=500, conn=uow.conn)
    failed_notifications = [
        item for item in notifications if str(item.get("status") or "").lower() == "failed"
    ]

    return {
        "summary": "Platform operational health summary generated.",
        "insights": [
            {
                "title": "Failed Jobs",
                "value": str(len(failed_jobs)),
                "explanation": "Tenant jobs with status='failed'.",
            },
            {
                "title": "Failed Notifications",
                "value": str(len(failed_notifications)),
                "explanation": "Tenant notifications with status='failed'.",
            },
        ],
        "sources": [
            {"source_type": "analytics", "reference": "jobs:status=failed"},
            {"source_type": "analytics", "reference": "notifications:status=failed"},
            {"source_type": "analytics", "reference": f"kpi_snapshot:{latest_kpis.get('snapshot_date') or 'latest'}"},
        ],
        "warnings": [],
    }


def retrieve_student_context(*, tenant_id: int, student_id: str, uow: Any) -> dict[str, Any]:
    profile = context_service.build_student_profile(student_id=student_id, tenant_id=tenant_id, conn=uow.conn)
    student = profile.get("student") or {}

    student_name = str((student.get("data_json") or {}).get("name") or student.get("entity_id") or student_id)
    return {
        "summary": f"Student context loaded for {student_name}.",
        "insights": [
            {
                "title": "Program",
                "value": str((profile.get("program") or {}).get("entity_id") or "n/a"),
                "explanation": "Program relation from semantic context layer.",
            },
            {
                "title": "Advisor",
                "value": str((profile.get("advisor") or {}).get("entity_id") or "n/a"),
                "explanation": "Advisor relation from semantic context layer.",
            },
            {
                "title": "Enrollments",
                "value": str(len(profile.get("enrollments") or [])),
                "explanation": "Linked enrollment entities.",
            },
            {
                "title": "Grades",
                "value": str(len(profile.get("grades") or [])),
                "explanation": "Linked grade entities.",
            },
        ],
        "sources": [
            {"source_type": "context", "reference": f"student_profile:{student_id}"},
        ],
        "warnings": [] if student else ["student_not_found"],
        "profile": profile,
    }


def retrieve_faculty_context(*, tenant_id: int, faculty_id: str, uow: Any) -> dict[str, Any]:
    profile = context_service.build_faculty_profile(faculty_id=faculty_id, tenant_id=tenant_id, conn=uow.conn)
    faculty = profile.get("faculty") or {}

    faculty_name = str((faculty.get("data_json") or {}).get("name") or faculty.get("entity_id") or faculty_id)
    return {
        "summary": f"Faculty context loaded for {faculty_name}.",
        "insights": [
            {
                "title": "Advised Students",
                "value": str(len(profile.get("advised_students") or [])),
                "explanation": "Students currently linked via advised_by relation.",
            },
            {
                "title": "Advised Programs",
                "value": str(len(profile.get("advised_programs") or [])),
                "explanation": "Distinct programs represented by advised students.",
            },
            {
                "title": "Departments",
                "value": str(len(profile.get("departments") or [])),
                "explanation": "Distinct departments of advised students.",
            },
        ],
        "sources": [
            {"source_type": "context", "reference": f"faculty_profile:{faculty_id}"},
        ],
        "warnings": [] if faculty else ["faculty_not_found"],
        "profile": profile,
    }


def retrieve_academic_risk(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    at_risk: list[str] = []
    severe_at_risk: list[str] = []
    risk_threshold = int(
        get_runtime_value(
            "academic.risk_grade_threshold",
            "ACADEMIC_RISK_GRADE_THRESHOLD",
            "60",
            tenant_id=tenant_id,
        )
    )
    severe_risk_threshold = int(
        get_runtime_value(
            "academic.severe_risk_grade_threshold",
            "ACADEMIC_SEVERE_RISK_GRADE_THRESHOLD",
            "50",
            tenant_id=tenant_id,
        )
    )

    if uow.conn is not None:
        with uow.conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT r.source_entity_id
                FROM app_platform_context_relations r
                JOIN app_platform_context_entities g
                  ON g.tenant_id = r.tenant_id
                 AND g.entity_type = r.target_entity_type
                 AND g.entity_id = r.target_entity_id
                WHERE r.tenant_id = %s
                  AND r.relation_type = 'has_grade'
                                    AND COALESCE((g.data_json ->> 'grade_value')::numeric, 0) < %s
                ORDER BY r.source_entity_id
                """,
                                (tenant_id, risk_threshold),
            )
            at_risk = [str(row[0]) for row in cur.fetchall()]

            cur.execute(
                """
                SELECT DISTINCT r.source_entity_id
                FROM app_platform_context_relations r
                JOIN app_platform_context_entities g
                  ON g.tenant_id = r.tenant_id
                 AND g.entity_type = r.target_entity_type
                 AND g.entity_id = r.target_entity_id
                WHERE r.tenant_id = %s
                  AND r.relation_type = 'has_grade'
                                    AND COALESCE((g.data_json ->> 'grade_value')::numeric, 0) < %s
                ORDER BY r.source_entity_id
                """,
                                (tenant_id, severe_risk_threshold),
            )
            severe_at_risk = [str(row[0]) for row in cur.fetchall()]
    else:
        # In-memory fallback for tests: inspect context repository state.
        repo = uow.context_repository
        for rel in repo._relations.values():  # noqa: SLF001
            if int(rel.get("tenant_id", 0)) != int(tenant_id):
                continue
            if str(rel.get("relation_type")) != "has_grade":
                continue
            grade_entity = repo.get_entity(  # noqa: SLF001
                tenant_id=tenant_id,
                entity_type=str(rel.get("target_entity_type") or "grade"),
                entity_id=str(rel.get("target_entity_id") or ""),
                conn=uow.conn,
            )
            grade_value = (grade_entity or {}).get("data_json", {}).get("grade_value")
            try:
                if float(grade_value) < risk_threshold:
                    at_risk.append(str(rel.get("source_entity_id")))
                if float(grade_value) < severe_risk_threshold:
                    severe_at_risk.append(str(rel.get("source_entity_id")))
            except (TypeError, ValueError):
                continue
        at_risk = sorted(set(at_risk))
        severe_at_risk = sorted(set(severe_at_risk))

    at_risk_count = len(at_risk)
    severe_at_risk_count = len(severe_at_risk)
    if severe_at_risk_count > 0:
        risk_severity = "high"
    elif at_risk_count > 0:
        risk_severity = "medium"
    else:
        risk_severity = "low"

    return {
        "summary": f"Identified {at_risk_count} student(s) at academic risk.",
        "insights": [
            {
                "title": "At-Risk Students",
                "value": str(at_risk_count),
                "explanation": f"Students linked to grades below {risk_threshold} in semantic context.",
            },
            {
                "title": "High Expulsion Risk Students",
                "value": str(severe_at_risk_count),
                "explanation": (
                    f"Students linked to grades below {severe_risk_threshold} in semantic context."
                ),
            },
            {
                "title": "Student IDs",
                "value": ", ".join(at_risk[:10]) if at_risk else "none",
                "explanation": "First up to 10 matching student IDs.",
            },
        ],
        "sources": [
            {
                "source_type": "context",
                "reference": f"relations:has_grade + grades<{risk_threshold}",
            },
        ],
        "warnings": (
            ["expulsion_risk_detected"]
            if severe_at_risk_count > 0
            else ([] if at_risk_count > 0 else ["no_academic_risk_detected"])
        ),
        "at_risk_count": at_risk_count,
        "severe_at_risk_count": severe_at_risk_count,
        "at_risk_student_ids": at_risk,
        "severe_at_risk_student_ids": severe_at_risk,
        "risk_severity": risk_severity,
    }


def retrieve_student_skills_profile(
    *,
    tenant_id: int,
    question: str,
    context: dict[str, Any] | None,
    uow: Any,
) -> dict[str, Any]:
    student_id = extract_student_id(question, context)
    if not student_id:
        return {
            "summary": "Student id is required for student skills profile queries.",
            "insights": [],
            "sources": [],
            "warnings": ["missing_student_id"],
        }

    skills = education_graph_service.list_student_skills(
        tenant_id=tenant_id,
        student_id=student_id,
        uow=uow,
    )
    top = skills[:8]
    insights = [
        {
            "title": str(item.get("skill_name") or item.get("skill_key") or "skill"),
            "value": f"{float(item.get('proficiency_level') or 0):.2f}",
            "explanation": f"Source: {item.get('source', 'unknown')}",
        }
        for item in top
    ]

    return {
        "summary": f"Loaded {len(skills)} inferred skill edge(s) for student {student_id}.",
        "insights": insights,
        "sources": [{"source_type": "education_graph", "reference": f"student_skills:{student_id}"}],
        "warnings": [] if skills else ["no_student_skills_found"],
    }


def retrieve_missing_skills_for_program(
    *,
    tenant_id: int,
    question: str,
    context: dict[str, Any] | None,
    uow: Any,
) -> dict[str, Any]:
    student_id = extract_student_id(question, context)
    if not student_id:
        return {
            "summary": "Student id is required for missing skills queries.",
            "insights": [],
            "sources": [],
            "warnings": ["missing_student_id"],
        }

    student_skills = education_graph_service.list_student_skills(
        tenant_id=tenant_id,
        student_id=student_id,
        uow=uow,
    )
    current_keys = {str(item.get("skill_key") or "") for item in student_skills}

    course_skills = education_graph_service.list_course_skills(
        tenant_id=tenant_id,
        course_id=None,
        uow=uow,
    )
    universe = sorted({str(item.get("skill_key") or "") for item in course_skills if str(item.get("skill_key") or "")})
    missing = [key for key in universe if key not in current_keys]

    return {
        "summary": f"Identified {len(missing)} missing skill(s) for student {student_id} based on mapped course graph.",
        "insights": [
            {
                "title": "Missing Skills",
                "value": ", ".join(missing[:10]) if missing else "none",
                "explanation": "Derived from Course -> Skill mappings not present in student skill edges.",
            }
        ],
        "sources": [{"source_type": "education_graph", "reference": "course_skills:all"}],
        "warnings": [] if missing else ["no_missing_skills_detected"],
    }


def retrieve_recommended_courses(
    *,
    tenant_id: int,
    question: str,
    context: dict[str, Any] | None,
    uow: Any,
) -> dict[str, Any]:
    student_id = extract_student_id(question, context)
    if not student_id:
        return {
            "summary": "Student id is required for recommended course queries.",
            "insights": [],
            "sources": [],
            "warnings": ["missing_student_id"],
        }

    student_skills = education_graph_service.list_student_skills(
        tenant_id=tenant_id,
        student_id=student_id,
        uow=uow,
    )
    owned = {str(item.get("skill_key") or "") for item in student_skills}
    edges = education_graph_service.list_course_skills(tenant_id=tenant_id, course_id=None, uow=uow)

    course_to_missing: dict[str, set[str]] = {}
    for edge in edges:
        course_id = str(edge.get("course_id") or "")
        skill_key = str(edge.get("skill_key") or "")
        if not course_id or not skill_key:
            continue
        if skill_key in owned:
            continue
        course_to_missing.setdefault(course_id, set()).add(skill_key)

    ranked = sorted(course_to_missing.items(), key=lambda item: len(item[1]), reverse=True)
    insights = [
        {
            "title": f"Course {course_id}",
            "value": ", ".join(sorted(missing_skills)[:6]),
            "explanation": f"Covers {len(missing_skills)} currently missing skill(s).",
        }
        for course_id, missing_skills in ranked[:5]
    ]

    return {
        "summary": f"Generated {len(insights)} recommended course candidate(s) for student {student_id}.",
        "insights": insights,
        "sources": [{"source_type": "education_graph", "reference": "course_skill_mappings"}],
        "warnings": [] if insights else ["no_recommendations_available"],
    }


def extract_student_id(question: str, context: dict[str, Any] | None = None) -> str | None:
    if isinstance(context, dict):
        from_context = str(context.get("student_id") or "").strip()
        if from_context:
            return from_context

    m = re.search(r"student\s+([a-zA-Z0-9_-]+)", question, flags=re.IGNORECASE)
    if m:
        return str(m.group(1)).strip()

    m = re.search(r"студент\s+([a-zA-Z0-9_-]+)", question, flags=re.IGNORECASE)
    if m:
        return str(m.group(1)).strip()

    m = re.search(r"оқушы\s+([a-zA-Z0-9_-]+)", question, flags=re.IGNORECASE)
    if m:
        return str(m.group(1)).strip()

    return None


def extract_faculty_id(question: str, context: dict[str, Any] | None = None) -> str | None:
    if isinstance(context, dict):
        from_context = str(
            context.get("faculty_id") or context.get("advisor_id") or context.get("teacher_id") or ""
        ).strip()
        if from_context:
            return from_context

    patterns = [
        r"faculty\s+([a-zA-Z0-9_-]+)",
        r"advisor\s+([a-zA-Z0-9_-]+)",
        r"teacher\s+([a-zA-Z0-9_-]+)",
        r"преподавател[ьяюе]\s+([a-zA-Z0-9_-]+)",
        r"куратор[ауое]?\s+([a-zA-Z0-9_-]+)",
        r"оқытушы\s+([a-zA-Z0-9_-]+)",
        r"мұғалім\s+([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        m = re.search(pattern, question, flags=re.IGNORECASE)
        if m:
            return str(m.group(1)).strip()
    return None
