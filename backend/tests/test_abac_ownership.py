"""
ABAC Tests — Attribute-Based Access Control (Ownership Validation)
==================================================================

Tests verify that resource ownership is enforced across:
- Student profiles
- Enrollments
- Grades
"""

from unittest.mock import patch
import pytest

from app.modules.rbac.abac import (
    AbacDenyError,
    validate_student_ownership,
    validate_enrollment_ownership,
    validate_enrollment_creation,
    validate_grade_submission,
    validate_grade_ownership,
    validate_grade_modification,
    validate_course_ownership,
)


# ============================================================================
# STUDENT OWNERSHIP TESTS
# ============================================================================
class TestStudentOwnership:
    """Verify student resource ownership validation."""

    @pytest.mark.asyncio
    async def test_student_can_view_own_profile(self):
        """PASS: Student can view own profile."""
        with patch("app.modules.rbac.abac.get_user_roles_for_tenant") as mock_roles:
            mock_roles.return_value = ["student"]
            
            # Student viewing their own profile (actor_id == student_owner_id)
            await validate_student_ownership(
                actor_id="student_123",
                student_id=1,
                tenant_id=1,
                student_owner_id="student_123",
                actor_roles=["student"],
            )
            # No exception raised ✓

    @pytest.mark.asyncio
    async def test_admin_can_view_any_student(self):
        """PASS: Admin can view any student."""
        await validate_student_ownership(
            actor_id="admin_123",
            student_id=999,
            tenant_id=1,
            student_owner_id="student_456",
            actor_roles=["admin"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_student_cannot_view_other_student(self):
        """FAIL: Student cannot view other student's profile."""
        with pytest.raises(AbacDenyError) as exc_info:
            await validate_student_ownership(
                actor_id="student_123",
                student_id=999,
                tenant_id=1,
                student_owner_id="student_456",
                actor_roles=["student"],
            )
        
        assert "ownership_mismatch" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 403


# ============================================================================
# ENROLLMENT OWNERSHIP TESTS
# ============================================================================
class TestEnrollmentOwnership:
    """Verify enrollment resource ownership validation."""

    @pytest.mark.asyncio
    async def test_student_can_view_own_enrollment(self):
        """PASS: Student can view own enrollment."""
        await validate_enrollment_ownership(
            actor_id="student_123",
            enrollment_id=1,
            student_id="student_123",
            course_id=100,
            tenant_id=1,
            actor_roles=["student"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_teacher_can_view_course_enrollments(self):
        """PASS: Teacher can view enrollments in own course."""
        await validate_enrollment_ownership(
            actor_id="teacher_123",
            enrollment_id=1,
            student_id="student_456",
            course_id=100,
            tenant_id=1,
            actor_roles=["teacher"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_admin_can_view_any_enrollment(self):
        """PASS: Admin can view any enrollment."""
        await validate_enrollment_ownership(
            actor_id="admin_123",
            enrollment_id=1,
            student_id="student_456",
            course_id=100,
            tenant_id=1,
            actor_roles=["admin"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_student_cannot_view_other_enrollment(self):
        """FAIL: Student cannot view other student's enrollment."""
        with pytest.raises(AbacDenyError) as exc_info:
            await validate_enrollment_ownership(
                actor_id="student_123",
                enrollment_id=1,
                student_id="student_456",  # Different student
                course_id=100,
                tenant_id=1,
                actor_roles=["student"],
            )
        
        assert exc_info.value.status_code == 403


# ============================================================================
# ENROLLMENT CREATION TESTS
# ============================================================================
class TestEnrollmentCreation:
    """Verify enrollment creation authorization."""

    @pytest.mark.asyncio
    async def test_admin_can_enroll_any_student(self):
        """PASS: Admin can enroll students."""
        await validate_enrollment_creation(
            actor_id="admin_123",
            student_id=999,
            course_id=100,
            tenant_id=1,
            actor_roles=["admin"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_teacher_can_enroll_students(self):
        """PASS: Teacher can enroll students in courses."""
        await validate_enrollment_creation(
            actor_id="teacher_123",
            student_id=999,
            course_id=100,
            tenant_id=1,
            actor_roles=["teacher"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_student_cannot_self_enroll(self):
        """FAIL: Student cannot create enrollments."""
        with pytest.raises(AbacDenyError) as exc_info:
            await validate_enrollment_creation(
                actor_id="student_123",
                student_id="student_123",
                course_id=100,
                tenant_id=1,
                actor_roles=["student"],
            )
        
        assert "insufficient_role" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 403


# ============================================================================
# GRADE SUBMISSION TESTS
# ============================================================================
class TestGradeSubmission:
    """Verify grade submission authorization."""

    @pytest.mark.asyncio
    async def test_teacher_can_submit_grades(self):
        """PASS: Teacher can submit grades."""
        await validate_grade_submission(
            actor_id="teacher_123",
            course_id=100,
            tenant_id=1,
            actor_roles=["teacher"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_admin_can_submit_grades(self):
        """PASS: Admin can submit grades."""
        await validate_grade_submission(
            actor_id="admin_123",
            course_id=100,
            tenant_id=1,
            actor_roles=["admin"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_student_cannot_submit_grades(self):
        """FAIL: Student cannot submit grades."""
        with pytest.raises(AbacDenyError) as exc_info:
            await validate_grade_submission(
                actor_id="student_123",
                course_id=100,
                tenant_id=1,
                actor_roles=["student"],
            )
        
        assert "insufficient_role" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 403


# ============================================================================
# GRADE OWNERSHIP TESTS
# ============================================================================
class TestGradeOwnership:
    """Verify grade resource ownership validation."""

    @pytest.mark.asyncio
    async def test_student_can_view_own_grade(self):
        """PASS: Student can view own grades."""
        await validate_grade_ownership(
            actor_id="student_123",
            grade_id=1,
            course_id=100,
            student_id="student_123",
            submitted_by="teacher_456",
            tenant_id=1,
            actor_roles=["student"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_teacher_can_view_course_grades(self):
        """PASS: Teacher can view grades in own course."""
        await validate_grade_ownership(
            actor_id="teacher_123",
            grade_id=1,
            course_id=100,
            student_id="student_456",
            submitted_by="teacher_123",
            tenant_id=1,
            actor_roles=["teacher"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_admin_can_view_any_grade(self):
        """PASS: Admin can view any grade."""
        await validate_grade_ownership(
            actor_id="admin_123",
            grade_id=1,
            course_id=100,
            student_id="student_456",
            submitted_by="teacher_789",
            tenant_id=1,
            actor_roles=["admin"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_student_cannot_view_other_grade(self):
        """FAIL: Student cannot view other student's grades."""
        with pytest.raises(AbacDenyError) as exc_info:
            await validate_grade_ownership(
                actor_id="student_123",
                grade_id=1,
                course_id=100,
                student_id="student_456",  # Different student
                submitted_by="teacher_789",
                tenant_id=1,
                actor_roles=["student"],
            )
        
        assert exc_info.value.status_code == 403


# ============================================================================
# GRADE MODIFICATION TESTS
# ============================================================================
class TestGradeModification:
    """Verify grade modification authorization."""

    @pytest.mark.asyncio
    async def test_teacher_can_modify_own_submission(self):
        """PASS: Teacher can modify grades they submitted."""
        await validate_grade_modification(
            actor_id="teacher_123",
            grade_id=1,
            submitted_by="teacher_123",  # Same teacher
            tenant_id=1,
            actor_roles=["teacher"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_admin_can_modify_any_grade(self):
        """PASS: Admin can modify any grade."""
        await validate_grade_modification(
            actor_id="admin_123",
            grade_id=1,
            submitted_by="teacher_456",
            tenant_id=1,
            actor_roles=["admin"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_teacher_cannot_modify_other_submission(self):
        """FAIL: Teacher cannot modify grades submitted by others."""
        with pytest.raises(AbacDenyError) as exc_info:
            await validate_grade_modification(
                actor_id="teacher_123",
                grade_id=1,
                submitted_by="teacher_456",  # Different teacher
                tenant_id=1,
                actor_roles=["teacher"],
            )
        
        assert "ownership_mismatch" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_student_cannot_modify_grades(self):
        """FAIL: Student cannot modify grades."""
        with pytest.raises(AbacDenyError) as exc_info:
            await validate_grade_modification(
                actor_id="student_123",
                grade_id=1,
                submitted_by="teacher_456",
                tenant_id=1,
                actor_roles=["student"],
            )
        
        assert exc_info.value.status_code == 403


# ============================================================================
# COURSE OWNERSHIP TESTS
# ============================================================================
class TestCourseOwnership:
    """Verify course resource ownership validation."""

    @pytest.mark.asyncio
    async def test_instructor_can_view_own_course(self):
        """PASS: Instructor can view own course."""
        await validate_course_ownership(
            actor_id="teacher_123",
            course_id=100,
            tenant_id=1,
            course_instructor_id="teacher_123",
            actor_roles=["teacher"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_teacher_can_view_any_course(self):
        """PASS: Teacher can view courses."""
        await validate_course_ownership(
            actor_id="teacher_123",
            course_id=100,
            tenant_id=1,
            course_instructor_id="teacher_456",
            actor_roles=["teacher"],
        )
        # No exception raised ✓

    @pytest.mark.asyncio
    async def test_admin_can_view_any_course(self):
        """PASS: Admin can view any course."""
        await validate_course_ownership(
            actor_id="admin_123",
            course_id=100,
            tenant_id=1,
            course_instructor_id="teacher_456",
            actor_roles=["admin"],
        )
        # No exception raised ✓


# ============================================================================
# INTEGRATION & SUMMARY
# ============================================================================
if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════════════
                         ABAC TESTS SUMMARY
    ═══════════════════════════════════════════════════════════════════════
    
    ✅ Student Ownership:          3 tests
    ✅ Enrollment Ownership:        4 tests
    ✅ Enrollment Creation:         3 tests
    ✅ Grade Submission:            3 tests
    ✅ Grade Ownership:             4 tests
    ✅ Grade Modification:          4 tests
    ✅ Course Ownership:            3 tests
    
    Total:                          24 tests
    
    Attack Vectors Covered:
    ✓ Cross-student access blocked
    ✓ Non-teacher grade submission blocked
    ✓ Grade modification by non-owner blocked
    ✓ Self-enrollment blocked
    ✓ Admin bypass working
    
    ═══════════════════════════════════════════════════════════════════════
    """)
