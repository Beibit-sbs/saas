from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    DomainValidationError,
    MutationResult,
    TenantResourceNotFoundError,
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.billing.service import assert_billing_write_allowed, assert_quota_with_increment
from app.modules.courses.models import CourseModel
from app.modules.enrollments.models import AcademicTermModel, EnrollmentModel
from app.modules.grades.service import GradeLifecycleService
from app.modules.students.models import StudentProfileModel
from app.modules.transcripts.business_rules import TranscriptRules
from app.modules.transcripts.models import TranscriptRecordModel, TranscriptSnapshotModel
from app.modules.transcripts.schemas import (
    TranscriptConsistencyIssueSchema,
    TranscriptConsistencyReportSchema,
    TranscriptTenantConsistencyReportSchema,
    StudentTranscriptSchema,
    TranscriptItemSchema,
    TranscriptSnapshotSchema,
)
from app.modules.usage.service import record_usage_event


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _audit(actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="transcript",
        metadata=metadata,
        tenant_id=tenant_id,
    )


class TranscriptService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def _load_student(self, tenant_id: int, student_profile_id: int) -> StudentProfileModel:
        student = self.db.execute(
            select(StudentProfileModel).where(
                and_(
                    StudentProfileModel.id == student_profile_id,
                    StudentProfileModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            student,
            tenant_id,
            resource_name="Student profile",
            resource_id=student_profile_id,
        )
        return student

    def _load_enrollments(self, tenant_id: int, student_profile_id: int) -> list[EnrollmentModel]:
        return self.db.execute(
            select(EnrollmentModel)
            .where(
                and_(
                    EnrollmentModel.tenant_id == tenant_id,
                    EnrollmentModel.student_profile_id == student_profile_id,
                )
            )
            .order_by(EnrollmentModel.term_id, EnrollmentModel.course_id, EnrollmentModel.id)
        ).scalars().all()

    def _load_course(self, tenant_id: int, course_id: int) -> CourseModel:
        course = self.db.execute(select(CourseModel).where(CourseModel.id == course_id)).scalar_one_or_none()
        if course is None:
            raise TenantResourceNotFoundError(
                f"Course {course_id} not found or does not belong to tenant {tenant_id}"
            )
        raw_tenant = getattr(course, "tenant_id", None)
        if raw_tenant is not None:
            try:
                normalized = int(raw_tenant)
            except (TypeError, ValueError):
                raise TenantResourceNotFoundError(
                    f"Course {course_id} not found or does not belong to tenant {tenant_id}"
                ) from None
            if normalized != tenant_id:
                raise TenantResourceNotFoundError(
                    f"Course {course_id} not found or does not belong to tenant {tenant_id}"
                )
        return course

    def _load_term(self, tenant_id: int, term_id: int) -> AcademicTermModel | None:
        return self.db.execute(
            select(AcademicTermModel).where(
                and_(
                    AcademicTermModel.id == term_id,
                    AcademicTermModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

    def _load_record(self, tenant_id: int, enrollment_id: int) -> TranscriptRecordModel | None:
        return self.db.execute(
            select(TranscriptRecordModel).where(
                and_(
                    TranscriptRecordModel.tenant_id == tenant_id,
                    TranscriptRecordModel.enrollment_id == enrollment_id,
                )
            )
        ).scalar_one_or_none()

    async def generate_transcript(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
        actor_id: str,
        expected_record_version: int | None = None,
    ) -> StudentTranscriptSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        assert_billing_write_allowed(tenant_id, action="transcripts.generate")
        assert_quota_with_increment(tenant_id, "transcripts_generated", increment=1)
        self._load_student(tenant_id, student_profile_id)

        enrollments = self._load_enrollments(tenant_id, student_profile_id)
        items: list[TranscriptItemSchema] = []

        for enrollment in enrollments:
            course = self._load_course(tenant_id, enrollment.course_id)
            term = self._load_term(tenant_id, enrollment.term_id)

            credits_value = int(getattr(course, "credits", 0) or 0)
            existing = self._load_record(tenant_id, enrollment.id)

            if existing is None:
                record = TranscriptRecordModel(
                    tenant_id=tenant_id,
                    student_profile_id=student_profile_id,
                    enrollment_id=enrollment.id,
                    course_id=enrollment.course_id,
                    term_id=enrollment.term_id,
                    grade_code=enrollment.grade_code,
                    grade_points=enrollment.grade_points,
                    credits=credits_value,
                    recorded_at=_utc_now(),
                    metadata_json={"source": "transcript.generate"},
                )
                self.db.add(record)
            else:
                if expected_record_version is not None:
                    validate_version_match(existing.version, expected_record_version)
                existing.course_id = enrollment.course_id
                existing.term_id = enrollment.term_id
                existing.grade_code = enrollment.grade_code
                existing.grade_points = enrollment.grade_points
                existing.credits = credits_value
                existing.recorded_at = _utc_now()
                existing.version += 1
                record = existing

            items.append(
                TranscriptItemSchema(
                    enrollment_id=enrollment.id,
                    term_id=enrollment.term_id,
                    term_code=getattr(term, "term_code", None),
                    term_name=getattr(term, "term_name", None),
                    course_id=enrollment.course_id,
                    course_code=getattr(course, "course_code", None),
                    course_title=getattr(course, "title", None),
                    credits=credits_value,
                    grade_code=enrollment.grade_code,
                    grade_points=enrollment.grade_points,
                )
            )

        total_credits = sum(max(int(item.credits), 0) for item in items)
        TranscriptRules.validate_transcript_integrity(enrollments)
        TranscriptRules.validate_credit_totals(total_credits)

        gpa = await GradeLifecycleService(self.db).calculate_student_gpa(
            tenant_id,
            student_profile_id=student_profile_id,
        )
        TranscriptRules.validate_gpa_threshold(gpa)

        self.db.flush()
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to generate transcript due to constraint violation") from exc

        record_usage_event(tenant_id=tenant_id, metric="transcripts_generated", value=1)

        _audit(
            actor_id,
            build_audit_action("transcripts", "transcript", "generated"),
            f"/internal/transcripts/students/{student_profile_id}/generate",
            {
                "student_profile_id": student_profile_id,
                "records": len(items),
            },
            tenant_id,
        )

        return StudentTranscriptSchema(
            student_profile_id=student_profile_id,
            total_credits=total_credits,
            gpa=gpa,
            items=items,
        )

    async def get_student_transcript(self, tenant_id: int, *, student_profile_id: int) -> StudentTranscriptSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_student(tenant_id, student_profile_id)

        rows = self.db.execute(
            select(TranscriptRecordModel)
            .where(
                and_(
                    TranscriptRecordModel.tenant_id == tenant_id,
                    TranscriptRecordModel.student_profile_id == student_profile_id,
                )
            )
            .order_by(TranscriptRecordModel.term_id, TranscriptRecordModel.course_id, TranscriptRecordModel.id)
        ).scalars().all()

        if not rows:
            transcript = await self.generate_transcript(
                tenant_id,
                student_profile_id=student_profile_id,
                actor_id="system@transcripts",
            )
            record_usage_event(tenant_id=tenant_id, metric="transcripts_read", value=1)
            return transcript

        items: list[TranscriptItemSchema] = []
        for record in rows:
            course = self._load_course(tenant_id, record.course_id)
            term = self._load_term(tenant_id, record.term_id)
            items.append(
                TranscriptItemSchema(
                    enrollment_id=record.enrollment_id,
                    term_id=record.term_id,
                    term_code=getattr(term, "term_code", None),
                    term_name=getattr(term, "term_name", None),
                    course_id=record.course_id,
                    course_code=getattr(course, "course_code", None),
                    course_title=getattr(course, "title", None),
                    credits=record.credits,
                    grade_code=record.grade_code,
                    grade_points=record.grade_points,
                )
            )

        total_credits = sum(max(int(item.credits), 0) for item in items)
        gpa = await GradeLifecycleService(self.db).calculate_student_gpa(
            tenant_id,
            student_profile_id=student_profile_id,
        )

        record_usage_event(tenant_id=tenant_id, metric="transcripts_read", value=1)

        return StudentTranscriptSchema(
            student_profile_id=student_profile_id,
            total_credits=total_credits,
            gpa=gpa,
            items=items,
        )

    async def create_transcript_snapshot(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
        actor_id: str,
    ) -> MutationResult[TranscriptSnapshotSchema]:
        transcript = await self.generate_transcript(
            tenant_id,
            student_profile_id=student_profile_id,
            actor_id=actor_id,
        )

        snapshot = TranscriptSnapshotModel(
            tenant_id=tenant_id,
            student_profile_id=student_profile_id,
            snapshot_json=transcript.model_dump(mode="json"),
            generated_by=actor_id,
            generated_at=_utc_now(),
        )
        self.db.add(snapshot)
        self.db.flush()
        self.db.refresh(snapshot)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DomainValidationError("Unable to create transcript snapshot due to constraint violation") from exc

        _audit(
            actor_id,
            build_audit_action("transcripts", "snapshot", "created"),
            f"/internal/transcripts/students/{student_profile_id}/snapshot",
            {
                "student_profile_id": student_profile_id,
                "snapshot_id": snapshot.id,
            },
            tenant_id,
        )

        return MutationResult(entity=TranscriptSnapshotSchema.model_validate(snapshot))

    async def get_student_transcript_consistency_report(
        self,
        tenant_id: int,
        *,
        student_profile_id: int,
    ) -> TranscriptConsistencyReportSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        self._load_student(tenant_id, student_profile_id)

        enrollments = self._load_enrollments(tenant_id, student_profile_id)
        transcript_records = self.db.execute(
            select(TranscriptRecordModel)
            .where(
                and_(
                    TranscriptRecordModel.tenant_id == tenant_id,
                    TranscriptRecordModel.student_profile_id == student_profile_id,
                )
            )
            .order_by(TranscriptRecordModel.enrollment_id, TranscriptRecordModel.id)
        ).scalars().all()

        return self._build_transcript_consistency_report(
            student_profile_id=student_profile_id,
            enrollments=enrollments,
            transcript_records=transcript_records,
        )

    def _build_transcript_consistency_report(
        self,
        *,
        student_profile_id: int,
        enrollments: list[EnrollmentModel],
        transcript_records: list[TranscriptRecordModel],
    ) -> TranscriptConsistencyReportSchema:
        enrollment_by_id = {int(enrollment.id): enrollment for enrollment in enrollments}
        records_by_enrollment_id: dict[int, list[TranscriptRecordModel]] = {}
        for record in transcript_records:
            records_by_enrollment_id.setdefault(int(record.enrollment_id), []).append(record)

        issues: list[TranscriptConsistencyIssueSchema] = []

        for enrollment in enrollments:
            enrollment_id = int(enrollment.id)
            records = records_by_enrollment_id.get(enrollment_id, [])
            if not records:
                issues.append(
                    TranscriptConsistencyIssueSchema(
                        issue_type="missing_transcript_record",
                        enrollment_id=enrollment_id,
                    )
                )
                continue

            if len(records) > 1:
                issues.append(
                    TranscriptConsistencyIssueSchema(
                        issue_type="duplicate_transcript_records_for_enrollment",
                        enrollment_id=enrollment_id,
                        transcript_record_id=int(records[0].id),
                    )
                )

            record = records[0]

            field_pairs = [
                ("course_id", int(enrollment.course_id), int(record.course_id)),
                ("term_id", int(enrollment.term_id), int(record.term_id)),
                ("grade_code", enrollment.grade_code, record.grade_code),
                (
                    "grade_points",
                    str(enrollment.grade_points) if enrollment.grade_points is not None else None,
                    str(record.grade_points) if record.grade_points is not None else None,
                ),
            ]

            for field_name, expected, actual in field_pairs:
                if expected != actual:
                    issues.append(
                        TranscriptConsistencyIssueSchema(
                            issue_type="transcript_record_mismatch",
                            enrollment_id=enrollment_id,
                            transcript_record_id=int(record.id),
                            field=field_name,
                            expected=str(expected) if expected is not None else None,
                            actual=str(actual) if actual is not None else None,
                        )
                    )

        for record in transcript_records:
            if int(record.enrollment_id) not in enrollment_by_id:
                issues.append(
                    TranscriptConsistencyIssueSchema(
                        issue_type="dangling_transcript_record",
                        enrollment_id=int(record.enrollment_id),
                        transcript_record_id=int(record.id),
                    )
                )

        return TranscriptConsistencyReportSchema(
            student_profile_id=student_profile_id,
            enrollment_count=len(enrollments),
            transcript_record_count=len(transcript_records),
            issue_count=len(issues),
            issues=issues,
        )

    async def list_tenant_transcript_consistency_reports(
        self,
        tenant_id: int,
    ) -> TranscriptTenantConsistencyReportSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        enrollments = self.db.execute(
            select(EnrollmentModel)
            .where(EnrollmentModel.tenant_id == tenant_id)
            .order_by(EnrollmentModel.student_profile_id, EnrollmentModel.id)
        ).scalars().all()

        transcript_records = self.db.execute(
            select(TranscriptRecordModel)
            .where(TranscriptRecordModel.tenant_id == tenant_id)
            .order_by(
                TranscriptRecordModel.student_profile_id,
                TranscriptRecordModel.enrollment_id,
                TranscriptRecordModel.id,
            )
        ).scalars().all()

        enrollments_by_student: dict[int, list[EnrollmentModel]] = {}
        for enrollment in enrollments:
            enrollments_by_student.setdefault(int(enrollment.student_profile_id), []).append(enrollment)

        records_by_student: dict[int, list[TranscriptRecordModel]] = {}
        for record in transcript_records:
            records_by_student.setdefault(int(record.student_profile_id), []).append(record)

        student_ids = sorted(set(enrollments_by_student.keys()) | set(records_by_student.keys()))
        reports: list[TranscriptConsistencyReportSchema] = []
        total_issue_count = 0

        for student_profile_id in student_ids:
            report = self._build_transcript_consistency_report(
                student_profile_id=student_profile_id,
                enrollments=enrollments_by_student.get(student_profile_id, []),
                transcript_records=records_by_student.get(student_profile_id, []),
            )
            if report.issue_count > 0:
                reports.append(report)
                total_issue_count += report.issue_count

        return TranscriptTenantConsistencyReportSchema(
            scanned_student_count=len(student_ids),
            students_with_issues=len(reports),
            total_issue_count=total_issue_count,
            reports=reports,
        )
