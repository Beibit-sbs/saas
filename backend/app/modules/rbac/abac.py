"""
Attribute-Based Access Control (ABAC) — Ownership & Resource Validation
========================================================================

ABAC enforces resource-level access control beyond role-based permissions.

Rules:
- Students: user can view/edit own profile OR if authorized advisor/teacher
- Enrollments: user can access only own enrollments OR if course teacher/admin
- Grades: only course teacher/admin can submit/modify grades
- Courses: only course owner/admin can manage

Security Model:
- actor_id: who is requesting (from JWT)
- resource_owner: who owns/created the resource (from DB)
- role: actor's role (admin, teacher, student, etc)
- fail-closed: deny by default if no owner match
"""

from typing import Optional
from fastapi import HTTPException

from app.modules.audit.service import log_data_access_event
from app.modules.rbac.service import get_user_roles_for_tenant


class AbacDenyError(HTTPException):
    """Resource access denied by ABAC policy."""

    def __init__(self, resource_type: str, reason: str):
        super().__init__(
            status_code=403,
            detail=f"Resource access denied ({resource_type}): {reason}",
        )


def _deny(
    *,
    resource: str,
    action: str,
    actor_id: str,
    tenant_id: int,
    resource_id: str | int,
    reason: str,
) -> None:
    log_data_access_event(
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource=resource,
        resource_id=resource_id,
        action=action,
        result="denied",
        reason=reason,
    )
    raise AbacDenyError(resource, reason)


# ============================================================================
# STUDENT OWNERSHIP VALIDATORS
# ============================================================================


async def validate_student_ownership(
    *,
    actor_id: str,
    student_id: int,
    tenant_id: int,
    student_owner_id: Optional[str] = None,
    actor_roles: Optional[list[str]] = None,
) -> None:
    """
    Validate actor can access student resource.

    Rules:
    1. Admin role can access any student
    2. Student can access own profile (actor_id == student_owner_id)
    3. Advisor/Teacher role can access any student in their advisee list
       (can be enhanced with explicit advisor mappings)

    Args:
        actor_id: User making request
        student_id: Student profile being accessed
        tenant_id: Tenant context
        student_owner_id: User ID of student (optional, for prefetch optimization)
        actor_roles: Actor's roles (optional, will be fetched if not provided)

    Raises:
        AbacDenyError: If access denied
    """
    # Admin bypass
    if actor_roles is None:
        actor_roles = get_user_roles_for_tenant(actor_id, tenant_id)

    if "admin" in actor_roles or "superadmin" in actor_roles:
        return  # Admin can access any student

    # Self-access
    if actor_id == student_owner_id:
        return

    # Teacher/Dean/Advisor can access students (enhanced ABAC in future)
    # For now, only self or admin
    _deny(
        resource="student",
        action="read",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_id=student_id,
        reason="ownership_mismatch",
    )


# ============================================================================
# ENROLLMENT OWNERSHIP VALIDATORS
# ============================================================================


async def validate_enrollment_ownership(
    *,
    actor_id: str,
    enrollment_id: int,
    student_id: int,
    course_id: int,
    tenant_id: int,
    actor_roles: Optional[list[str]] = None,
) -> None:
    """
    Validate actor can access enrollment resource.

    Rules:
    1. Admin role can access any enrollment
    2. Student can access own enrollment (actor_id == student_id)
    3. Course instructor/teacher can access enrollments in their course
       (enhanced in future with course teacher mapping)

    Args:
        actor_id: User making request
        enrollment_id: Enrollment being accessed
        student_id: Student ID for this enrollment
        course_id: Course ID for this enrollment
        tenant_id: Tenant context
        actor_roles: Actor's roles (optional, will be fetched if not provided)

    Raises:
        AbacDenyError: If access denied
    """
    # Admin bypass
    if actor_roles is None:
        actor_roles = get_user_roles_for_tenant(actor_id, tenant_id)

    if "admin" in actor_roles or "superadmin" in actor_roles:
        return

    # Student can access own enrollment
    if actor_id == student_id:
        return

    # Teacher of course can access (enhanced ABAC in future)
    if "teacher" in actor_roles:
        # Would check: is actor_id a teacher of course_id
        # For now, allow all teachers (enhanced validation in future)
        return

    _deny(
        resource="enrollment",
        action="read",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_id=enrollment_id,
        reason="ownership_mismatch",
    )


async def validate_enrollment_creation(
    *,
    actor_id: str,
    student_id: int,
    course_id: int,
    tenant_id: int,
    actor_roles: Optional[list[str]] = None,
) -> None:
    """
    Validate actor can CREATE/MODIFY enrollment.

    Rules:
    1. Admin can enroll any student in any course
    2. Teacher can enroll students in own courses (enhanced ABAC)
    3. Student cannot self-enroll (must be admin/registrar)

    Args:
        actor_id: Who is creating the enrollment
        student_id: Student being enrolled
        course_id: Course to enroll into
        tenant_id: Tenant context
        actor_roles: Actor's roles (optional, will be fetched if not provided)

    Raises:
        AbacDenyError: If access denied
    """
    if actor_roles is None:
        actor_roles = get_user_roles_for_tenant(actor_id, tenant_id)

    if "admin" in actor_roles or "superadmin" in actor_roles:
        return

    # Teacher can enroll (enhanced: only in their courses)
    if "teacher" in actor_roles:
        return

    # Student cannot self-enroll (fail-closed)
    _deny(
        resource="enrollment",
        action="write",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_id=f"{student_id}:{course_id}",
        reason="insufficient_role",
    )


# ============================================================================
# GRADE OWNERSHIP VALIDATORS
# ============================================================================


async def validate_grade_submission(
    *,
    actor_id: str,
    course_id: int,
    tenant_id: int,
    actor_roles: Optional[list[str]] = None,
) -> None:
    """
    Validate actor can SUBMIT grade for course.

    Rules:
    1. Admin/superadmin can submit grades for any course
    2. Only course instructor/teacher can submit grades
    3. Students cannot submit grades for themselves or others

    Args:
        actor_id: Who is submitting the grade
        course_id: Course where grade is being submitted
        tenant_id: Tenant context
        actor_roles: Actor's roles (optional, will be fetched if not provided)

    Raises:
        AbacDenyError: If access denied
    """
    if actor_roles is None:
        actor_roles = get_user_roles_for_tenant(actor_id, tenant_id)

    if "admin" in actor_roles or "superadmin" in actor_roles:
        return

    # Only teachers can submit grades
    if "teacher" in actor_roles:
        # Enhanced ABAC: validate actor_id is instructor of course_id
        # For now, allow (will enhance with course enrollment check)
        return

    _deny(
        resource="grade",
        action="write",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_id=course_id,
        reason="insufficient_role",
    )


async def validate_grade_ownership(
    *,
    actor_id: str,
    grade_id: int,
    course_id: int,
    student_id: int,
    submitted_by: str,
    tenant_id: int,
    actor_roles: Optional[list[str]] = None,
) -> None:
    """
    Validate actor can VIEW/MODIFY grade.

    Rules:
    1. Admin/superadmin can view/modify any grade
    2. Course instructor can view/modify grades in their course
    3. Student can view own grades (for their enrollment)
    4. Only original submitter or admin can modify

    Args:
        actor_id: Who is accessing the grade
        grade_id: Grade being accessed
        course_id: Course context
        student_id: Student who received the grade
        submitted_by: User ID who submitted the grade
        tenant_id: Tenant context
        actor_roles: Actor's roles (optional, will be fetched if not provided)

    Raises:
        AbacDenyError: If access denied
    """
    if actor_roles is None:
        actor_roles = get_user_roles_for_tenant(actor_id, tenant_id)

    if "admin" in actor_roles or "superadmin" in actor_roles:
        return

    # Student can view own grades
    if actor_id == student_id and "student" in actor_roles:
        return

    # Teacher can view grades in own course (enhanced ABAC in future)
    if "teacher" in actor_roles:
        return

    _deny(
        resource="grade",
        action="read",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_id=grade_id,
        reason="ownership_mismatch",
    )


async def validate_grade_modification(
    *,
    actor_id: str,
    grade_id: int,
    submitted_by: str,
    tenant_id: int,
    actor_roles: Optional[list[str]] = None,
) -> None:
    """
    Validate actor can MODIFY (not just view) grade.

    Rules:
    1. Admin/superadmin can modify any grade
    2. Only original submitter (teacher) can modify own submission
    3. Students cannot modify grades

    Args:
        actor_id: Who is modifying the grade
        grade_id: Grade being modified
        submitted_by: Original submitter user ID
        tenant_id: Tenant context
        actor_roles: Actor's roles (optional, will be fetched if not provided)

    Raises:
        AbacDenyError: If access denied
    """
    if actor_roles is None:
        actor_roles = get_user_roles_for_tenant(actor_id, tenant_id)

    if "admin" in actor_roles or "superadmin" in actor_roles:
        return

    # Only original submitter can modify
    if actor_id == submitted_by:
        return

    _deny(
        resource="grade",
        action="update",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_id=grade_id,
        reason="ownership_mismatch",
    )


# ============================================================================
# COURSE OWNERSHIP VALIDATORS
# ============================================================================


async def validate_course_ownership(
    *,
    actor_id: str,
    course_id: int,
    tenant_id: int,
    course_instructor_id: Optional[str] = None,
    actor_roles: Optional[list[str]] = None,
) -> None:
    """
    Validate actor can access course resource.

    Rules:
    1. Admin/superadmin can access any course
    2. Course instructor can access own course
    3. Teachers can access basic course info (enhanced in future)

    Args:
        actor_id: Who is accessing
        course_id: Course being accessed
        tenant_id: Tenant context
        course_instructor_id: Instructor user ID (for prefetch optimization)
        actor_roles: Actor's roles (optional, will be fetched if not provided)

    Raises:
        AbacDenyError: If access denied
    """
    if actor_roles is None:
        actor_roles = get_user_roles_for_tenant(actor_id, tenant_id)

    if "admin" in actor_roles or "superadmin" in actor_roles:
        return

    # Course instructor can access own course
    if actor_id == course_instructor_id:
        return

    # Teachers can access course info (limited ABAC)
    if "teacher" in actor_roles:
        return

    _deny(
        resource="course",
        action="read",
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_id=course_id,
        reason="ownership_mismatch",
    )
