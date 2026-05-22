from app.core.db import get_raw_conn
from app.modules.auth.local_users_service import local_user_store
import os
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Set

_rbac_schema_ready = False
_rbac_schema_lock = Lock()

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


_CANONICAL_PLATFORM_ADMIN_PERMISSIONS: Set[str] = {
    "platform.admin.read",
    "platform.admin.write",
    "analytics.data.read",
    "analytics.data.write",
    "health.read",
    "metrics.read",
    "ops.read",
    "ops.write",
    "jobs.read",
    "jobs.write",
    "audit.read",
    "rbac.read",
    "rbac.write",
    "tenants.read",
    "tenants.write",
    "students.read",
    "students.write",
    "faculty.read",
    "faculty.write",
    "programs.read",
    "programs.write",
    "courses.read",
    "courses.write",
    "enrollments.read",
    "enrollments.write",
    "records.read",
    "records.write",
    "grades.read",
    "grades.write",
    "transcripts.read",
    "transcripts.write",
    "scheduling.read",
    "scheduling.write",
    "degree_progress.read",
    "advising.read",
    "advising.write",
    "student_services.read",
    "student_services.write",
    "career_services.read",
    "career_services.write",
    "financial_aid.read",
    "financial_aid.write",
    "finance.read",
    "finance.write",
    "housing.read",
    "housing.write",
    "alumni.read",
    "alumni.write",
    "research.read",
    "research.write",
    "operations.read",
    "operations.write",
    "student_life.read",
    "student_life.write",
    "procurement.read",
    "procurement.write",
}

_CANONICAL_AUDITOR_PERMISSIONS: Set[str] = {
    "health.read",
    "metrics.read",
    "ops.read",
    "jobs.read",
    "audit.read",
    "rbac.read",
    "tenants.read",
    "students.read",
    "faculty.read",
    "programs.read",
    "courses.read",
    "enrollments.read",
    "records.read",
    "grades.read",
    "transcripts.read",
    "scheduling.read",
    "degree_progress.read",
    "advising.read",
    "student_services.read",
    "career_services.read",
    "financial_aid.read",
    "finance.read",
    "housing.read",
    "alumni.read",
    "research.read",
    "operations.read",
    "student_life.read",
    "procurement.read",
}

_EXECUTIVE_CONTROL_TOWER_PERMISSIONS: Set[str] = {
    "admin.executive_control_tower.read",
    "admin.executive_control_tower.summary.read",
    "admin.executive_control_tower.assignments.read",
    "admin.executive_control_tower.documents.read",
    "admin.executive_control_tower.sla_risk.read",
    "admin.executive_control_tower.strategy.read",
    "admin.executive_control_tower.audit.read",
    "admin.executive_control_tower.department.read",
    "admin.executive_control_tower.metric_registry.read",
}

_EXECUTIVE_CONTROL_TOWER_AUDITOR_PERMISSIONS: Set[str] = {
    "admin.executive_control_tower.read",
    "admin.executive_control_tower.summary.read",
    "admin.executive_control_tower.audit.read",
    "admin.executive_control_tower.metric_registry.read",
}

_STUDENT_LIFECYCLE_PERMISSIONS: Set[str] = {
    "student_lifecycle.applicants.read",
    "student_lifecycle.applicants.create",
    "student_lifecycle.applicants.update",
    "student_lifecycle.applicants.status.update",
    "student_lifecycle.students.read",
    "student_lifecycle.students.create",
    "student_lifecycle.students.update",
    "student_lifecycle.students.status.update",
    "student_lifecycle.enrollment.read",
    "student_lifecycle.enrollment.create",
    "student_lifecycle.enrollment.update",
    "student_lifecycle.enrollment.review",
    "student_lifecycle.records.read",
    "student_lifecycle.records.create",
    "student_lifecycle.records.result_metadata.write",
    "student_lifecycle.transcripts.read",
    "student_lifecycle.transcripts.preview",
    "student_lifecycle.degree_progress.read",
    "student_lifecycle.degree_progress.compute",
    "student_lifecycle.graduation_readiness.review",
    "student_lifecycle.requests.read",
    "student_lifecycle.requests.create",
    "student_lifecycle.requests.review",
    "student_lifecycle.appeals.read",
    "student_lifecycle.appeals.create",
    "student_lifecycle.appeals.review",
    "student_lifecycle.interventions.read",
    "student_lifecycle.interventions.signal.create",
    "student_lifecycle.interventions.plan.create",
    "student_lifecycle.interventions.followup.write",
    "student_lifecycle.audit.read",
    "student_lifecycle.evidence.read",
    "student_lifecycle.evidence.attach",
    "student_lifecycle.dashboard.read",
    "student_lifecycle.health.read",
    "student_lifecycle.admin.read",
}

_ACADEMIC_OPERATIONS_PERMISSIONS: Set[str] = {
    "academic_operations.overview.read",
    "academic_operations.dashboard.read",
    "academic_operations.health.read",
    "academic_operations.audit.read",
    "academic_operations.evidence.read",
    "academic_operations.evidence.attach",
    "academic_operations.academic_groups.read",
    "academic_operations.academic_groups.create",
    "academic_operations.academic_groups.update",
    "academic_operations.cohorts.read",
    "academic_operations.cohorts.create",
    "academic_operations.cohorts.update",
    "academic_operations.gradebook_metadata.read",
    "academic_operations.gradebook_metadata.create",
    "academic_operations.gradebook_metadata.update",
    "academic_operations.retake_management.read",
    "academic_operations.retake_management.create",
    "academic_operations.retake_management.update",
    "academic_operations.summer_semester.read",
    "academic_operations.summer_semester.create",
    "academic_operations.summer_semester.update",
    "academic_operations.advisor_tutor.read",
    "academic_operations.advisor_tutor.create",
    "academic_operations.advisor_tutor.update",
    "academic_operations.canonical_bridge.read",
    "academic_operations.canonical_bridge.create",
    "academic_operations.canonical_bridge.update",
    "academic_operations.student_lifecycle_bridge.read",
    "academic_operations.document_workflow_bridge.read",
    "academic_operations.executive_governance_bridge.read",
    "academic_operations.quality_accreditation_bridge.read",
    "academic_operations.course_catalog_bridge.read",
    "academic_operations.elective_selection_bridge.read",
    "academic_operations.committee_decision_bridge.read",
    "academic_operations.prerequisite_bridge.read",
    "academic_operations.teaching_load_bridge.read",
    "academic_operations.thesis_bridge.read",
    "academic_operations.degree_audit_bridge.read",
    "academic_operations.admin.read",
    "academic_operations.admin.configure",
}

_ACADEMIC_OPERATIONS_AUDITOR_PERMISSIONS: Set[str] = {
    "academic_operations.overview.read",
    "academic_operations.dashboard.read",
    "academic_operations.health.read",
    "academic_operations.audit.read",
    "academic_operations.evidence.read",
    "academic_operations.canonical_bridge.read",
    "academic_operations.student_lifecycle_bridge.read",
    "academic_operations.document_workflow_bridge.read",
    "academic_operations.executive_governance_bridge.read",
    "academic_operations.quality_accreditation_bridge.read",
    "academic_operations.course_catalog_bridge.read",
    "academic_operations.elective_selection_bridge.read",
    "academic_operations.committee_decision_bridge.read",
    "academic_operations.prerequisite_bridge.read",
    "academic_operations.teaching_load_bridge.read",
    "academic_operations.thesis_bridge.read",
    "academic_operations.degree_audit_bridge.read",
}

_RESEARCH_SCIENCE_PERMISSIONS: Set[str] = {
    "research_science.overview.read",
    "research_science.dashboard.read",
    "research_science.health.read",
    "research_science.matrix.read",
    "research_science.limitations.read",
    "research_science.projects.read",
    "research_science.projects.create",
    "research_science.projects.update",
    "research_science.student_research.read",
    "research_science.student_research.create",
    "research_science.student_research.update",
    "research_science.supervision.read",
    "research_science.supervision.create",
    "research_science.supervision.update",
    "research_science.publications.read",
    "research_science.publications.create",
    "research_science.publications.update",
    "research_science.conferences.read",
    "research_science.conferences.create",
    "research_science.conferences.update",
    "research_science.grants.read",
    "research_science.grants.create",
    "research_science.grants.update",
    "research_science.grant_deliverables.read",
    "research_science.grant_deliverables.create",
    "research_science.grant_deliverables.update",
    "research_science.ethics.read",
    "research_science.ethics.create",
    "research_science.ethics.update",
    "research_science.ethics_amendments.read",
    "research_science.ethics_amendments.create",
    "research_science.ethics_amendments.update",
    "research_science.evidence.read",
    "research_science.evidence.attach",
    "research_science.audit.read",
    "research_science.bridges.read",
    "research_science.bridges.create",
    "research_science.bridges.update",
    "research_science.admin.read",
    "research_science.admin.configure",
}

_RESEARCH_SCIENCE_AUDITOR_PERMISSIONS: Set[str] = {
    "research_science.overview.read",
    "research_science.dashboard.read",
    "research_science.health.read",
    "research_science.matrix.read",
    "research_science.limitations.read",
    "research_science.projects.read",
    "research_science.student_research.read",
    "research_science.supervision.read",
    "research_science.publications.read",
    "research_science.conferences.read",
    "research_science.grants.read",
    "research_science.grant_deliverables.read",
    "research_science.ethics.read",
    "research_science.ethics_amendments.read",
    "research_science.evidence.read",
    "research_science.audit.read",
    "research_science.bridges.read",
}

BASELINE_ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "superadmin": {
        "admin.dashboard.read",
        "admin.expansion.read",
        "admin.roles.manage",
        "admin.audit.read",
        "admin.integrations.manage",
        "admin.ai.providers.manage",
        "admin.ai.models.manage",
        "ai.chat.execute",
        "admin.i18n.manage",
        "admin.users.manage",
        "admin.backup.manage",
        "admin.jobs.read",
        "admin.jobs.write",
        "admin.org_units.read",
        "admin.org_units.write",
        "admin.students.read",
        "admin.students.write",
        "admin.faculty.read",
        "admin.faculty.write",
        "admin.programs.read",
        "admin.programs.write",
        "admin.courses.read",
        "admin.courses.write",
        "admin.enrollments.read",
        "admin.enrollments.write",
        "admin.records.read",
        "admin.records.write",
        "admin.tenants.read",
        "admin.tenants.write",
        "admissions.read",
        "admissions.write",
        "admissions.decide",
        "admissions.documents.write",
        "profiles.read",
        "profiles.write",
        "profiles.manage",
        "workflows.read",
        "workflows.write",
        "federation.read",
        "federation.write",
        "developer_platform.read",
        "developer_platform.write",
        "admin.rector_assignments.create",
        "admin.rector_assignments.read",
        "admin.rector_assignments.read_all",
        "admin.rector_assignments.read_department",
        "admin.rector_assignments.assign",
        "admin.rector_assignments.accept",
        "admin.rector_assignments.report.submit",
        "admin.rector_assignments.report.review",
        "admin.rector_assignments.evidence.attach",
        "admin.rector_assignments.comment",
        "admin.rector_assignments.status.change",
        "admin.rector_assignments.complete",
        "admin.rector_assignments.return",
        "admin.rector_assignments.escalate",
        "admin.rector_assignments.cancel",
        "admin.rector_assignments.archive",
        "admin.rector_assignments.audit.read",
        "admin.rector_assignments.templates.manage",
        "admin.rector_assignments.dashboard.read",
        "admin.rector_assignments.admin",
        "admin.rector_assignments.outbox.read",
        "admin.rector_assignments.outbox.manage",
        "admin.rector_assignments.sla.manage",
        "admin.rector_assignments.escalation_policy.manage",
        "admin.executive_control_tower.read",
        "admin.executive_control_tower.summary.read",
        "admin.executive_control_tower.assignments.read",
        "admin.executive_control_tower.documents.read",
        "admin.executive_control_tower.sla_risk.read",
        "admin.executive_control_tower.strategy.read",
        "admin.executive_control_tower.audit.read",
        "admin.executive_control_tower.department.read",
        "admin.executive_control_tower.metric_registry.read",
    }
    | _CANONICAL_PLATFORM_ADMIN_PERMISSIONS
    | _STUDENT_LIFECYCLE_PERMISSIONS
    | _ACADEMIC_OPERATIONS_PERMISSIONS
    | _RESEARCH_SCIENCE_PERMISSIONS,
    "admin": {
        "admin.dashboard.read",
        "admin.expansion.read",
        "admin.roles.manage",
        "admin.audit.read",
        "admin.integrations.manage",
        "admin.ai.providers.manage",
        "admin.ai.models.manage",
        "ai.chat.execute",
        "admin.i18n.manage",
        "admin.users.manage",
        "admin.backup.manage",
        "admin.jobs.read",
        "admin.jobs.write",
        "admin.org_units.read",
        "admin.org_units.write",
        "admin.students.read",
        "admin.students.write",
        "admin.faculty.read",
        "admin.faculty.write",
        "admin.programs.read",
        "admin.programs.write",
        "admin.courses.read",
        "admin.courses.write",
        "admin.enrollments.read",
        "admin.enrollments.write",
        "admin.records.read",
        "admin.records.write",
        "admin.tenants.read",
        "admin.tenants.write",
        "admissions.read",
        "admissions.write",
        "admissions.decide",
        "admissions.documents.write",
        "profiles.read",
        "profiles.write",
        "profiles.manage",
        "workflows.read",
        "workflows.write",
        "federation.read",
        "federation.write",
        "developer_platform.read",
        "developer_platform.write",
        "exams.read",
        "exams.write",
        "admin.rector_assignments.create",
        "admin.rector_assignments.read",
        "admin.rector_assignments.read_all",
        "admin.rector_assignments.read_department",
        "admin.rector_assignments.assign",
        "admin.rector_assignments.accept",
        "admin.rector_assignments.report.submit",
        "admin.rector_assignments.report.review",
        "admin.rector_assignments.evidence.attach",
        "admin.rector_assignments.comment",
        "admin.rector_assignments.status.change",
        "admin.rector_assignments.complete",
        "admin.rector_assignments.return",
        "admin.rector_assignments.escalate",
        "admin.rector_assignments.cancel",
        "admin.rector_assignments.archive",
        "admin.rector_assignments.audit.read",
        "admin.rector_assignments.templates.manage",
        "admin.rector_assignments.dashboard.read",
        "admin.rector_assignments.admin",
        "admin.rector_assignments.outbox.read",
        "admin.rector_assignments.outbox.manage",
        "admin.rector_assignments.sla.manage",
        "admin.rector_assignments.escalation_policy.manage",
        "admin.executive_control_tower.read",
        "admin.executive_control_tower.summary.read",
        "admin.executive_control_tower.assignments.read",
        "admin.executive_control_tower.documents.read",
        "admin.executive_control_tower.sla_risk.read",
        "admin.executive_control_tower.strategy.read",
        "admin.executive_control_tower.audit.read",
        "admin.executive_control_tower.department.read",
        "admin.executive_control_tower.metric_registry.read",
    }
    | _CANONICAL_PLATFORM_ADMIN_PERMISSIONS
    | _STUDENT_LIFECYCLE_PERMISSIONS
    | _ACADEMIC_OPERATIONS_PERMISSIONS
    | _RESEARCH_SCIENCE_PERMISSIONS,
    "auditor": {
        "admin.audit.read",
        "admin.dashboard.read",
        "admin.students.read",
        "admin.faculty.read",
        "admin.programs.read",
        "admin.courses.read",
        "admin.enrollments.read",
        "admin.records.read",
        "admin.tenants.read",
        "admin.jobs.read",
        "admissions.read",
        "profiles.read",
        "workflows.read",
        "federation.read",
        "developer_platform.read",
    }
    | _EXECUTIVE_CONTROL_TOWER_AUDITOR_PERMISSIONS
    | _CANONICAL_AUDITOR_PERMISSIONS
    | _ACADEMIC_OPERATIONS_AUDITOR_PERMISSIONS
    | _RESEARCH_SCIENCE_AUDITOR_PERMISSIONS,
    "student": {
        "enrollments.read",
        "grades.read",
        "transcripts.read",
        "scheduling.read",
        "analytics.data.read",
    },
    "teacher": {
        "profiles.read",
        "students.read",
        "enrollments.read",
        "grades.read",
        "grades.write",
        "transcripts.read",
        "scheduling.read",
    },
    "dean": {
        "profiles.read",
        "students.read",
        "enrollments.read",
        "grades.read",
        "transcripts.read",
        "scheduling.read",
        "degree_progress.read",
        "admissions.read",
        "health.read",
        "metrics.read",
        "ops.read",
        "jobs.read",
    },
    # ------------------------------------------------------------------
    # Ministry of Education (وزارة التعليم) roles — GCC PDPL / TIER-3
    # ------------------------------------------------------------------
    "ministry_observer": {
        # Read-only cross-tenant view for ministerial oversight
        "admin.dashboard.read",
        "admin.audit.read",
        "admin.students.read",
        "admin.faculty.read",
        "admin.programs.read",
        "admin.courses.read",
        "admin.enrollments.read",
        "admin.records.read",
        "admin.tenants.read",
        "admissions.read",
        "profiles.read",
        "metrics.read",
        "health.read",
    },
    "ministry_auditor": {
        # All observer permissions plus compliance/audit exports
        "admin.dashboard.read",
        "admin.audit.read",
        "admin.audit.export",
        "admin.students.read",
        "admin.faculty.read",
        "admin.programs.read",
        "admin.courses.read",
        "admin.enrollments.read",
        "admin.records.read",
        "admin.tenants.read",
        "admissions.read",
        "profiles.read",
        "metrics.read",
        "health.read",
        "compliance.read",
        "compliance.export",
    },
    "ministry_admin": {
        # Full ministry access: observer + auditor + ability to manage tenants
        "admin.dashboard.read",
        "admin.audit.read",
        "admin.audit.export",
        "admin.students.read",
        "admin.students.write",
        "admin.faculty.read",
        "admin.programs.read",
        "admin.programs.write",
        "admin.courses.read",
        "admin.enrollments.read",
        "admin.records.read",
        "admin.records.write",
        "admin.tenants.read",
        "admin.tenants.write",
        "admin.users.manage",
        "admissions.read",
        "profiles.read",
        "profiles.manage",
        "metrics.read",
        "health.read",
        "compliance.read",
        "compliance.export",
        "compliance.write",
        "federation.read",
    },
}

@dataclass
class RbacState:
    roles: Dict[str, Set[str]] = field(default_factory=dict)
    user_roles: Dict[str, Set[str]] = field(default_factory=dict)


state = RbacState(
    roles={role: set(perms) for role, perms in BASELINE_ROLE_PERMISSIONS.items()},
    user_roles={},
)

_permission_cache: dict[tuple[str, ...], Set[str]] = {}
_cache_lock = Lock()

_DEFAULT_TENANT_ID = 1
_PLATFORM_ADMIN_ROLE = "superadmin"

# Role hierarchy: higher number = higher privilege
# Used to prevent privilege escalation (e.g., admin can't assign superadmin)
ROLE_HIERARCHY: Dict[str, int] = {
    "superadmin": 100,
    "admin": 50,
    "ministry_admin": 45,
    "dean": 40,
    "ministry_auditor": 35,
    "teacher": 20,
    "auditor": 10,
    "ministry_observer": 8,
    "student": 0,
}

# Tenant-aware in-memory stores used by tenant-scoped APIs.
_tenant_roles_state: dict[int, dict[str, set[str]]] = {
    _DEFAULT_TENANT_ID: {role: set(perms) for role, perms in BASELINE_ROLE_PERMISSIONS.items()}
}
_tenant_user_roles_state: dict[int, dict[str, set[str]]] = {
    _DEFAULT_TENANT_ID: {}
}


def _db_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _use_database() -> bool:
    return bool(_db_url()) and psycopg is not None


def _should_fallback_to_memory(exc: Exception) -> bool:
    if isinstance(exc, RuntimeError) and str(exc) == "database unavailable":
        return True
    if isinstance(exc, (ConnectionError, TimeoutError, OSError)):
        return True
    if psycopg is not None and isinstance(
        exc,
        (
            psycopg.OperationalError,
            psycopg.InterfaceError,
            psycopg.ProgrammingError,
            psycopg.DataError,
        ),
    ):
        return True
    return False


def _clear_permission_cache() -> None:
    with _cache_lock:
        _permission_cache.clear()


def _seed_baseline_data(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app_roles (name, description, tenant_id)
            VALUES
                ('superadmin', 'Full platform access', 1),
                ('admin', 'Platform administration access', 1),
                ('auditor', 'Read-only audit and dashboard access', 1),
                ('student', 'Student self-service access', 1),
                ('teacher', 'Teacher instructional access', 1),
                ('dean', 'Dean academic oversight access', 1)
            ON CONFLICT (tenant_id, name) DO NOTHING
            """
        )

        permission_values = sorted({perm for perms in BASELINE_ROLE_PERMISSIONS.values() for perm in perms})
        cur.executemany(
            """
            INSERT INTO app_permissions (code, description)
            VALUES (%s, %s)
            ON CONFLICT (code) DO NOTHING
            """,
            [(perm, "") for perm in permission_values],
        )

        for role_name, permission_codes in BASELINE_ROLE_PERMISSIONS.items():
            cur.executemany(
                """
                INSERT INTO app_role_permissions (role_id, permission_id, tenant_id)
                SELECT r.id, p.id, 1
                FROM app_roles r
                JOIN app_permissions p ON p.code = %s
                WHERE r.tenant_id = 1 AND r.name = %s
                ON CONFLICT (role_id, permission_id) DO NOTHING
                """,
                [(code, role_name) for code in permission_codes],
            )


def _ensure_schema_and_seed(conn) -> None:
    # RBAC schema is Alembic-authoritative (see b7d3f1a9c2e4, f9a1b2c3d4e5, f1c2d3e4a5b7).
    # Runtime path only enforces baseline seed for environments where DB is available.
    _seed_baseline_data(conn)
    conn.commit()


def _ensure_schema_and_seed_once(conn) -> None:
    global _rbac_schema_ready
    if _rbac_schema_ready:
        return
    with _rbac_schema_lock:
        if _rbac_schema_ready:
            return
        _ensure_schema_and_seed(conn)
        _rbac_schema_ready = True

def _list_roles_db() -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.name, p.code
                FROM app_roles r
                LEFT JOIN app_role_permissions rp ON rp.role_id = r.id
                LEFT JOIN app_permissions p ON p.id = rp.permission_id
                ORDER BY r.name, p.code
                """
            )
            rows = cur.fetchall()

    roles: Dict[str, Set[str]] = {}
    for role_name, permission_code in rows:
        roles.setdefault(role_name, set())
        if permission_code:
            roles[role_name].add(permission_code)
    return {name: sorted(perms) for name, perms in roles.items()}


def _add_or_update_role_db(name: str, permissions: Set[str]) -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_roles (name, description)
                VALUES (%s, '')
                ON CONFLICT (name) DO NOTHING
                """,
                (name,),
            )

            if permissions:
                cur.executemany(
                    """
                    INSERT INTO app_permissions (code, description)
                    VALUES (%s, '')
                    ON CONFLICT (code) DO NOTHING
                    """,
                    [(perm,) for perm in sorted(permissions)],
                )

            cur.execute(
                """
                DELETE FROM app_role_permissions
                WHERE role_id = (SELECT id FROM app_roles WHERE name = %s)
                """,
                (name,),
            )

            if permissions:
                cur.executemany(
                    """
                    INSERT INTO app_role_permissions (role_id, permission_id)
                    SELECT r.id, p.id
                    FROM app_roles r
                    JOIN app_permissions p ON p.code = %s
                    WHERE r.name = %s
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                    """,
                    [(perm, name) for perm in sorted(permissions)],
                )

        conn.commit()

    return {name: sorted(permissions)}


def _assign_role_db(user_id: str, role: str) -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM app_roles WHERE name = %s", (role,))
            role_row = cur.fetchone()
            if role_row is None:
                raise ValueError(f"unknown role: {role}")

            cur.execute(
                """
                INSERT INTO app_user_roles (user_id, role_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, role_id) DO NOTHING
                """,
                (user_id, role_row[0]),
            )

            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY r.name
                """,
                (user_id,),
            )
            roles = [row[0] for row in cur.fetchall()]

        conn.commit()

    return {"user_id": user_id, "roles": roles}


def _sync_user_roles_db(user_id: str, roles: List[str], tenant_id: int) -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    normalized_roles = sorted({role.strip() for role in roles if role.strip()})

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM app_user_roles WHERE user_id = %s AND tenant_id = %s",
                (user_id, tenant_id),
            )

            if normalized_roles:
                cur.executemany(
                    """
                    INSERT INTO app_user_roles (user_id, role_id, tenant_id)
                    SELECT %s, r.id, %s
                    FROM app_roles r
                    WHERE r.name = %s AND r.tenant_id = %s
                    ON CONFLICT (user_id, role_id) DO NOTHING
                    """,
                    [
                        (user_id, tenant_id, role_name, tenant_id)
                        for role_name in normalized_roles
                    ],
                )

            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                                    AND ur.tenant_id = %s
                                    AND r.tenant_id = %s
                ORDER BY r.name
                """,
                                (user_id, tenant_id, tenant_id),
            )
            resolved_roles = [row[0] for row in cur.fetchall()]

        conn.commit()

    return {"user_id": user_id, "roles": resolved_roles}


def _get_user_roles_db(user_id: str) -> List[str]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY r.name
                """,
                (user_id,),
            )
            return [row[0] for row in cur.fetchall()]


def _list_user_role_assignments_db(user_id: str | None = None, role: str | None = None) -> List[Dict[str, object]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    clauses: list[str] = []
    params: list[str] = []
    if user_id:
        clauses.append("ur.user_id = %s")
        params.append(user_id)
    if role:
        clauses.append("r.name = %s")
        params.append(role)

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT ur.user_id, r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                {where_clause}
                ORDER BY ur.user_id, r.name
                """,
                params,
            )
            rows = cur.fetchall()

    assignments: Dict[str, List[str]] = {}
    for current_user_id, current_role in rows:
        assignments.setdefault(current_user_id, []).append(current_role)

    return [
        {"user_id": current_user_id, "roles": roles}
        for current_user_id, roles in assignments.items()
    ]


def _revoke_role_db(user_id: str, role: str) -> Dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    removed = False
    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM app_roles WHERE name = %s",
                (role,),
            )
            role_row = cur.fetchone()
            if role_row is not None:
                cur.execute(
                    "DELETE FROM app_user_roles WHERE user_id = %s AND role_id = %s",
                    (user_id, role_row[0]),
                )
                removed = cur.rowcount > 0

            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                ORDER BY r.name
                """,
                (user_id,),
            )
            roles = [row[0] for row in cur.fetchall()]

        conn.commit()

    return {"user_id": user_id, "role": role, "removed": removed, "roles": roles}


def _resolve_permissions_db(roles: List[str]) -> Set[str]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")
    if not roles:
        return set()

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT p.code
                FROM app_roles r
                JOIN app_role_permissions rp ON rp.role_id = r.id
                JOIN app_permissions p ON p.id = rp.permission_id
                WHERE r.name = ANY(%s)
                """,
                (roles,),
            )
            return {row[0] for row in cur.fetchall()}


def list_roles() -> Dict[str, List[str]]:
    if _use_database():
        try:
            return _list_roles_db()
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
    return {name: sorted(perms) for name, perms in state.roles.items()}


def add_or_update_role(name: str, permissions: List[str]) -> Dict[str, List[str]]:
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("role name is required")

    normalized = {perm.strip() for perm in permissions if perm.strip()}
    if _use_database():
        try:
            result = _add_or_update_role_db(normalized_name, normalized)
            _clear_permission_cache()
            return result
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    state.roles[normalized_name] = normalized
    _clear_permission_cache()
    return {normalized_name: sorted(normalized)}


def assign_role(user_id: str, role: str) -> Dict[str, List[str]]:
    normalized_user_id = user_id.strip()
    normalized_role = role.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")

    if _use_database():
        try:
            assigned = _assign_role_db(normalized_user_id, normalized_role)
            _clear_permission_cache()
            return assigned
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    if normalized_role not in state.roles:
        raise ValueError(f"unknown role: {normalized_role}")

    if normalized_user_id not in state.user_roles:
        state.user_roles[normalized_user_id] = set()

    state.user_roles[normalized_user_id].add(normalized_role)
    _clear_permission_cache()
    return {"user_id": normalized_user_id, "roles": sorted(state.user_roles[normalized_user_id])}


def sync_user_roles_from_trusted_source(
    user_id: str,
    roles: List[str],
    tenant_id: int,
) -> Dict[str, List[str]]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")

    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_roles = sorted({role.strip() for role in roles if role.strip()})

    if normalized_tenant_id == _DEFAULT_TENANT_ID and _use_database():
        try:
            synced = _sync_user_roles_db(normalized_user_id, normalized_roles, normalized_tenant_id)
            _clear_permission_cache()
            return synced
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _ensure_tenant_memory_state(normalized_tenant_id)
    _tenant_user_roles_state[normalized_tenant_id][normalized_user_id] = set(normalized_roles)
    if not normalized_roles:
        _tenant_user_roles_state[normalized_tenant_id].pop(normalized_user_id, None)

    if normalized_tenant_id == _DEFAULT_TENANT_ID:
        state.user_roles[normalized_user_id] = set(normalized_roles)
        if not normalized_roles:
            state.user_roles.pop(normalized_user_id, None)

    _clear_permission_cache()
    return {"user_id": normalized_user_id, "roles": normalized_roles}


def clear_user_roles_for_user(user_id: str, tenant_id: int) -> Dict[str, object]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")

    previous_roles = get_user_roles_for_tenant(normalized_user_id, tenant_id)
    sync_user_roles_from_trusted_source(normalized_user_id, [], tenant_id=tenant_id)
    return {
        "user_id": normalized_user_id,
        "removed": bool(previous_roles),
        "roles": [],
    }


def get_user_roles(user_id: str, tenant_id: int) -> List[str]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        return []

    normalized_tenant_id = _normalize_tenant_id(tenant_id)

    if _use_database():
        try:
            if normalized_tenant_id == _DEFAULT_TENANT_ID:
                return _get_user_roles_db(normalized_user_id)
            return _get_user_roles_for_tenant_db(normalized_user_id, normalized_tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
    return get_user_roles_for_tenant(normalized_user_id, normalized_tenant_id)


def get_user_roles_db_source(user_id: str, tenant_id: int) -> List[str]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        return []
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    return _get_user_roles_for_tenant_db(normalized_user_id, normalized_tenant_id)


def resolve_permissions(roles: List[str]) -> Set[str]:
    normalized_roles = sorted({role.strip() for role in roles if role.strip()})
    cache_key = tuple(normalized_roles)
    with _cache_lock:
        cached = _permission_cache.get(cache_key)
        if cached is not None:
            return set(cached)

    if _use_database():
        try:
            permissions = _resolve_permissions_db(normalized_roles)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
            permissions = set()
            for role in normalized_roles:
                permissions.update(state.roles.get(role, set()))
    else:
        permissions: Set[str] = set()
        for role in normalized_roles:
            permissions.update(state.roles.get(role, set()))

    with _cache_lock:
        _permission_cache[cache_key] = set(permissions)
    return permissions


def resolve_permissions_db_source(roles: List[str]) -> Set[str]:
    normalized_roles = sorted({role.strip() for role in roles if role.strip()})
    if not normalized_roles:
        return set()
    return _resolve_permissions_db(normalized_roles)


def list_user_role_assignments(user_id: str | None = None, role: str | None = None) -> List[Dict[str, object]]:
    normalized_user_id = user_id.strip() if user_id else None
    normalized_role = role.strip() if role else None

    if _use_database():
        try:
            return _list_user_role_assignments_db(normalized_user_id, normalized_role)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    assignments: List[Dict[str, object]] = []
    for current_user_id in sorted(state.user_roles):
        if normalized_user_id and current_user_id != normalized_user_id:
            continue
        roles = sorted(state.user_roles.get(current_user_id, set()))
        if normalized_role and normalized_role not in roles:
            continue
        assignments.append({"user_id": current_user_id, "roles": roles})
    return assignments


def revoke_role(user_id: str, role: str) -> Dict[str, object]:
    normalized_user_id = user_id.strip()
    normalized_role = role.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")
    if not normalized_role:
        raise ValueError("role is required")

    if _use_database():
        try:
            result = _revoke_role_db(normalized_user_id, normalized_role)
            _clear_permission_cache()
            return result
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    assigned_roles = state.user_roles.setdefault(normalized_user_id, set())
    removed = normalized_role in assigned_roles
    assigned_roles.discard(normalized_role)
    if not assigned_roles:
        state.user_roles.pop(normalized_user_id, None)
        remaining_roles: list[str] = []
    else:
        remaining_roles = sorted(assigned_roles)
    _clear_permission_cache()
    return {
        "user_id": normalized_user_id,
        "role": normalized_role,
        "removed": removed,
        "roles": remaining_roles,
    }


# ---------------------------------------------------------------------------
# Tenant-aware RBAC API
# ---------------------------------------------------------------------------


def _normalize_tenant_id(tenant_id: int) -> int:
    if tenant_id <= 0:
        raise ValueError("tenant_id must be positive")
    return int(tenant_id)


def _ensure_tenant_memory_state(tenant_id: int) -> None:
    _tenant_roles_state.setdefault(tenant_id, {})
    _tenant_user_roles_state.setdefault(tenant_id, {})


def _list_roles_for_tenant_db(tenant_id: int) -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.name, p.code
                FROM app_roles r
                LEFT JOIN app_role_permissions rp ON rp.role_id = r.id AND rp.tenant_id = %s
                LEFT JOIN app_permissions p ON p.id = rp.permission_id
                WHERE r.tenant_id = %s
                ORDER BY r.name, p.code
                """,
                (tenant_id, tenant_id),
            )
            rows = cur.fetchall()

    roles: Dict[str, Set[str]] = {}
    for role_name, permission_code in rows:
        roles.setdefault(role_name, set())
        if permission_code:
            roles[role_name].add(permission_code)
    return {name: sorted(perms) for name, perms in roles.items()}


def _add_or_update_role_for_tenant_db(
    tenant_id: int,
    name: str,
    permissions: Set[str],
) -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO app_roles (name, description, tenant_id)
                VALUES (%s, '', %s)
                ON CONFLICT (tenant_id, name) DO UPDATE
                SET updated_at = NOW()
                """,
                (name, tenant_id),
            )

            if permissions:
                cur.executemany(
                    """
                    INSERT INTO app_permissions (code, description)
                    VALUES (%s, '')
                    ON CONFLICT (code) DO NOTHING
                    """,
                    [(perm,) for perm in sorted(permissions)],
                )

            cur.execute(
                """
                DELETE FROM app_role_permissions
                WHERE tenant_id = %s
                  AND role_id = (
                      SELECT id FROM app_roles WHERE tenant_id = %s AND name = %s
                  )
                """,
                (tenant_id, tenant_id, name),
            )

            if permissions:
                cur.executemany(
                    """
                    INSERT INTO app_role_permissions (role_id, permission_id, tenant_id)
                    SELECT r.id, p.id, %s
                    FROM app_roles r
                    JOIN app_permissions p ON p.code = %s
                    WHERE r.tenant_id = %s AND r.name = %s
                    ON CONFLICT (role_id, permission_id) DO NOTHING
                    """,
                    [(tenant_id, perm, tenant_id, name) for perm in sorted(permissions)],
                )

        conn.commit()

    return {name: sorted(permissions)}


def _is_platform_admin_db(user_id: str) -> bool:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                  AND r.name = %s
                  AND r.tenant_id = %s
                LIMIT 1
                """,
                (user_id, _PLATFORM_ADMIN_ROLE, _DEFAULT_TENANT_ID),
            )
            return cur.fetchone() is not None


def _get_user_roles_for_tenant_db(
    user_id: str,
    tenant_id: int,
    include_platform_admin: bool = True,
) -> List[str]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    roles: set[str] = set()
    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                  AND ur.tenant_id = %s
                  AND r.tenant_id = %s
                ORDER BY r.name
                """,
                (user_id, tenant_id, tenant_id),
            )
            roles.update(row[0] for row in cur.fetchall())

    if include_platform_admin:
        try:
            if _is_platform_admin_db(user_id):
                roles.add(_PLATFORM_ADMIN_ROLE)
        except Exception:
            # Keep primary tenant result when platform-admin probe is unavailable.
            pass

    return sorted(roles)


def _resolve_permissions_for_tenant_db(roles: List[str], tenant_id: int) -> Set[str]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")
    if not roles:
        return set()

    if _PLATFORM_ADMIN_ROLE in roles:
        return set(BASELINE_ROLE_PERMISSIONS.get(_PLATFORM_ADMIN_ROLE, set()))

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT p.code
                FROM app_roles r
                JOIN app_role_permissions rp ON rp.role_id = r.id AND rp.tenant_id = %s
                JOIN app_permissions p ON p.id = rp.permission_id
                WHERE r.tenant_id = %s AND r.name = ANY(%s)
                """,
                (tenant_id, tenant_id, roles),
            )
            return {row[0] for row in cur.fetchall()}


def _assert_user_tenant_match(user_id: str, tenant_id: int) -> None:
    local_user = local_user_store.get_user(user_id)
    if local_user is None:
        return
    local_user_tenant = local_user.get("tenant_id")
    if local_user_tenant is None:
        raise PermissionError("user tenant context is missing")
    user_tenant = int(local_user_tenant)
    if user_tenant != tenant_id:
        raise PermissionError("cross-tenant role assignment is forbidden")


def _assign_role_for_tenant_db(user_id: str, role: str, tenant_id: int) -> Dict[str, List[str]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    _assert_user_tenant_match(user_id, tenant_id)

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM app_roles WHERE tenant_id = %s AND name = %s",
                (tenant_id, role),
            )
            role_row = cur.fetchone()
            if role_row is None:
                raise ValueError(f"unknown role: {role}")

            cur.execute(
                """
                INSERT INTO app_user_roles (user_id, role_id, tenant_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, role_id) DO NOTHING
                """,
                (user_id, role_row[0], tenant_id),
            )

            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                  AND ur.tenant_id = %s
                  AND r.tenant_id = %s
                ORDER BY r.name
                """,
                (user_id, tenant_id, tenant_id),
            )
            roles = [row[0] for row in cur.fetchall()]

        conn.commit()

    return {"user_id": user_id, "roles": roles}


def _list_user_role_assignments_for_tenant_db(
    tenant_id: int,
    user_id: str | None = None,
    role: str | None = None,
) -> List[Dict[str, object]]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            if user_id and role:
                cur.execute(
                    """
                    SELECT ur.user_id, r.name
                    FROM app_user_roles ur
                    JOIN app_roles r ON r.id = ur.role_id
                    WHERE ur.tenant_id = %s AND r.tenant_id = %s AND ur.user_id = %s AND r.name = %s
                    ORDER BY ur.user_id, r.name
                    """,
                    (tenant_id, tenant_id, user_id, role),
                )
            elif user_id:
                cur.execute(
                    """
                    SELECT ur.user_id, r.name
                    FROM app_user_roles ur
                    JOIN app_roles r ON r.id = ur.role_id
                    WHERE ur.tenant_id = %s AND r.tenant_id = %s AND ur.user_id = %s
                    ORDER BY ur.user_id, r.name
                    """,
                    (tenant_id, tenant_id, user_id),
                )
            elif role:
                cur.execute(
                    """
                    SELECT ur.user_id, r.name
                    FROM app_user_roles ur
                    JOIN app_roles r ON r.id = ur.role_id
                    WHERE ur.tenant_id = %s AND r.tenant_id = %s AND r.name = %s
                    ORDER BY ur.user_id, r.name
                    """,
                    (tenant_id, tenant_id, role),
                )
            else:
                cur.execute(
                    """
                    SELECT ur.user_id, r.name
                    FROM app_user_roles ur
                    JOIN app_roles r ON r.id = ur.role_id
                    WHERE ur.tenant_id = %s AND r.tenant_id = %s
                    ORDER BY ur.user_id, r.name
                    """,
                    (tenant_id, tenant_id),
                )
            rows = cur.fetchall()

    assignments: Dict[str, List[str]] = {}
    for current_user_id, current_role in rows:
        assignments.setdefault(current_user_id, []).append(current_role)

    return [
        {"user_id": current_user_id, "roles": roles}
        for current_user_id, roles in assignments.items()
    ]


def _revoke_role_for_tenant_db(user_id: str, role: str, tenant_id: int) -> Dict[str, object]:
    if not _db_url() or psycopg is None:
        raise RuntimeError("database unavailable")

    removed = False
    with get_raw_conn() as conn:
        _ensure_schema_and_seed_once(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM app_roles WHERE tenant_id = %s AND name = %s",
                (tenant_id, role),
            )
            role_row = cur.fetchone()
            if role_row is not None:
                cur.execute(
                    "DELETE FROM app_user_roles WHERE user_id = %s AND role_id = %s AND tenant_id = %s",
                    (user_id, role_row[0], tenant_id),
                )
                removed = cur.rowcount > 0

            cur.execute(
                """
                SELECT r.name
                FROM app_user_roles ur
                JOIN app_roles r ON r.id = ur.role_id
                WHERE ur.user_id = %s
                  AND ur.tenant_id = %s
                  AND r.tenant_id = %s
                ORDER BY r.name
                """,
                (user_id, tenant_id, tenant_id),
            )
            roles = [row[0] for row in cur.fetchall()]

        conn.commit()

    return {"user_id": user_id, "role": role, "removed": removed, "roles": roles}


def is_platform_admin(user_id: str) -> bool:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        return False

    if _use_database():
        try:
            return _is_platform_admin_db(normalized_user_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    # Memory fallback: platform admin role is valid ONLY in the platform tenant.
    platform_tenant_roles = _tenant_user_roles_state.get(_DEFAULT_TENANT_ID, {})
    return _PLATFORM_ADMIN_ROLE in platform_tenant_roles.get(normalized_user_id, set())


def get_role_hierarchy_level(role: str) -> int:
    """
    Get privilege level of a role.
    Higher number = higher privilege.
    Unknown roles return -1 (lowest privilege).

    Hierarchy:
        superadmin: 100
        admin:      50
        dean:       40
        teacher:    20
        auditor:    10
        student:    0
    """
    normalized_role = role.strip().lower()
    return ROLE_HIERARCHY.get(normalized_role, -1)


def get_highest_role_level(roles: List[str]) -> int:
    """Get the highest privilege level from the given roles."""
    if not roles:
        return -1
    return max(get_role_hierarchy_level(role) for role in roles)


def list_roles_for_tenant(tenant_id: int) -> Dict[str, List[str]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)

    if _use_database():
        try:
            return _list_roles_for_tenant_db(normalized_tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _ensure_tenant_memory_state(normalized_tenant_id)
    roles = _tenant_roles_state.get(normalized_tenant_id, {})
    return {name: sorted(perms) for name, perms in roles.items()}


def add_or_update_role_for_tenant(
    tenant_id: int,
    name: str,
    permissions: List[str],
) -> Dict[str, List[str]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("role name is required")

    # Platform-reserved roles may only exist in the platform tenant (tenant_id=1).
    if normalized_name == _PLATFORM_ADMIN_ROLE and normalized_tenant_id != _DEFAULT_TENANT_ID:
        raise PermissionError(
            f"role '{_PLATFORM_ADMIN_ROLE}' is reserved for the platform tenant "
            "and cannot be created in other tenants"
        )

    normalized_permissions = {perm.strip() for perm in permissions if perm.strip()}

    if _use_database():
        try:
            result = _add_or_update_role_for_tenant_db(
                normalized_tenant_id,
                normalized_name,
                normalized_permissions,
            )
            _clear_permission_cache()
            return result
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _ensure_tenant_memory_state(normalized_tenant_id)
    _tenant_roles_state[normalized_tenant_id][normalized_name] = normalized_permissions
    _clear_permission_cache()
    return {normalized_name: sorted(normalized_permissions)}


def add_or_update_role_for_tenant_with_replay(
    tenant_id: int,
    name: str,
    permissions: List[str],
) -> Dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_name = name.strip()
    normalized_permissions = sorted({perm.strip() for perm in permissions if perm.strip()})

    existing_roles = list_roles_for_tenant(normalized_tenant_id)
    existing_permissions = sorted(existing_roles.get(normalized_name, []))
    replayed = existing_permissions == normalized_permissions

    result = add_or_update_role_for_tenant(
        normalized_tenant_id,
        normalized_name,
        normalized_permissions,
    )
    return {
        "role": result,
        "idempotent_replay": replayed,
    }


def assign_role_to_user(tenant_id: int, user_id: str, role: str) -> Dict[str, List[str]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_user_id = user_id.strip()
    normalized_role = role.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")
    if not normalized_role:
        raise ValueError("role is required")

    if _use_database():
        try:
            assigned = _assign_role_for_tenant_db(normalized_user_id, normalized_role, normalized_tenant_id)
            _clear_permission_cache()
            return assigned
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _ensure_tenant_memory_state(normalized_tenant_id)
    _assert_user_tenant_match(normalized_user_id, normalized_tenant_id)
    roles_for_tenant = _tenant_roles_state[normalized_tenant_id]
    if normalized_role not in roles_for_tenant:
        raise ValueError(f"unknown role: {normalized_role}")

    tenant_assignments = _tenant_user_roles_state[normalized_tenant_id]
    tenant_assignments.setdefault(normalized_user_id, set()).add(normalized_role)
    _clear_permission_cache()
    return {
        "user_id": normalized_user_id,
        "roles": sorted(tenant_assignments[normalized_user_id]),
    }


def get_user_roles_for_tenant(user_id: str, tenant_id: int) -> List[str]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        return []
    normalized_tenant_id = _normalize_tenant_id(tenant_id)

    if _use_database():
        try:
            return _get_user_roles_for_tenant_db(normalized_user_id, normalized_tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _ensure_tenant_memory_state(normalized_tenant_id)
    roles = set(_tenant_user_roles_state[normalized_tenant_id].get(normalized_user_id, set()))
    if is_platform_admin(normalized_user_id):
        roles.add(_PLATFORM_ADMIN_ROLE)
    return sorted(roles)


def get_user_roles_for_tenant_db_source(user_id: str, tenant_id: int) -> List[str]:
    normalized_user_id = user_id.strip()
    if not normalized_user_id:
        return []
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    if normalized_tenant_id == _DEFAULT_TENANT_ID:
        return _get_user_roles_db(normalized_user_id)
    return _get_user_roles_for_tenant_db(normalized_user_id, normalized_tenant_id)


def resolve_permissions_for_tenant(roles: List[str], tenant_id: int) -> Set[str]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_roles = sorted({role.strip() for role in roles if role.strip()})
    cache_key = tuple([f"tenant:{normalized_tenant_id}", *normalized_roles])

    with _cache_lock:
        cached = _permission_cache.get(cache_key)
        if cached is not None:
            return set(cached)

    if _PLATFORM_ADMIN_ROLE in normalized_roles:
        permissions = set(BASELINE_ROLE_PERMISSIONS.get(_PLATFORM_ADMIN_ROLE, set()))
    elif _use_database():
        try:
            permissions = _resolve_permissions_for_tenant_db(normalized_roles, normalized_tenant_id)
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise
            _ensure_tenant_memory_state(normalized_tenant_id)
            permissions = set()
            for role in normalized_roles:
                permissions.update(_tenant_roles_state[normalized_tenant_id].get(role, set()))
    else:
        _ensure_tenant_memory_state(normalized_tenant_id)
        permissions = set()
        for role in normalized_roles:
            permissions.update(_tenant_roles_state[normalized_tenant_id].get(role, set()))

    with _cache_lock:
        _permission_cache[cache_key] = set(permissions)
    return permissions


def resolve_permissions_for_tenant_db_source(roles: List[str], tenant_id: int) -> Set[str]:
    normalized_roles = sorted({role.strip() for role in roles if role.strip()})
    if not normalized_roles:
        return set()
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    if normalized_tenant_id == _DEFAULT_TENANT_ID:
        return _resolve_permissions_db(normalized_roles)
    return _resolve_permissions_for_tenant_db(normalized_roles, normalized_tenant_id)


def list_user_role_assignments_for_tenant(
    tenant_id: int,
    user_id: str | None = None,
    role: str | None = None,
) -> List[Dict[str, object]]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_user_id = user_id.strip() if user_id else None
    normalized_role = role.strip() if role else None

    if _use_database():
        try:
            return _list_user_role_assignments_for_tenant_db(
                normalized_tenant_id,
                normalized_user_id,
                normalized_role,
            )
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _ensure_tenant_memory_state(normalized_tenant_id)
    assignments: List[Dict[str, object]] = []
    for current_user_id in sorted(_tenant_user_roles_state[normalized_tenant_id]):
        if normalized_user_id and current_user_id != normalized_user_id:
            continue
        roles_for_user = sorted(_tenant_user_roles_state[normalized_tenant_id].get(current_user_id, set()))
        if normalized_role and normalized_role not in roles_for_user:
            continue
        assignments.append({"user_id": current_user_id, "roles": roles_for_user})
    return assignments


def revoke_role_for_tenant(tenant_id: int, user_id: str, role: str) -> Dict[str, object]:
    normalized_tenant_id = _normalize_tenant_id(tenant_id)
    normalized_user_id = user_id.strip()
    normalized_role = role.strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")
    if not normalized_role:
        raise ValueError("role is required")

    if _use_database():
        try:
            result = _revoke_role_for_tenant_db(normalized_user_id, normalized_role, normalized_tenant_id)
            _clear_permission_cache()
            return result
        except Exception as exc:
            if not _should_fallback_to_memory(exc):
                raise

    _ensure_tenant_memory_state(normalized_tenant_id)
    tenant_assignments = _tenant_user_roles_state[normalized_tenant_id]
    roles_for_user = tenant_assignments.setdefault(normalized_user_id, set())
    removed = normalized_role in roles_for_user
    roles_for_user.discard(normalized_role)
    if not roles_for_user:
        tenant_assignments.pop(normalized_user_id, None)
        remaining: list[str] = []
    else:
        remaining = sorted(roles_for_user)
    _clear_permission_cache()
    return {
        "user_id": normalized_user_id,
        "role": normalized_role,
        "removed": removed,
        "roles": remaining,
    }
