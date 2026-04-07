from __future__ import annotations

from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import (
    assert_resource_belongs_to_tenant,
    validate_tenant_id_provided,
    validate_version_match,
)
from app.modules.audit.service import log_admin_action
from app.modules.profiles.business_rules import (
    DepartmentRules,
    FacultyRules,
    PersonRules,
    ProgramRules,
    StudentRules,
)
from app.modules.profiles.models import (
    DepartmentModel,
    FacultyModel,
    PersonModel,
    ProgramModel,
    StudentModel,
)
from app.modules.profiles.schemas import (
    DepartmentCreateSchema,
    DepartmentListResponseSchema,
    DepartmentReadSchema,
    FacultyCreateSchema,
    FacultyReadSchema,
    PersonCreateSchema,
    PersonListResponseSchema,
    PersonReadSchema,
    PersonUpdateSchema,
    ProgramCreateSchema,
    ProgramReadSchema,
    StudentCreateSchema,
    StudentReadSchema,
)


def _audit(
    *,
    actor: str,
    action: str,
    path: str,
    entity: str,
    metadata: dict,
    tenant_id: int,
) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity=entity,
        metadata=metadata,
        tenant_id=tenant_id,
    )


class PersonService:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_person(
        self,
        tenant_id: int,
        request: PersonCreateSchema,
        created_by: str,
    ) -> PersonReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        PersonRules.validate_unique_lookup_keys(
            email=request.email,
            external_person_key=request.external_person_key,
        )

        person = PersonModel(
            tenant_id=tenant_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            external_person_key=request.external_person_key,
            status=request.status.value,
            metadata_json=request.metadata_json,
            created_by=created_by,
        )

        self.db.add(person)
        self.db.flush()
        self.db.refresh(person)

        _audit(
            actor=created_by,
            action=build_audit_action("profiles", "person", "created"),
            path=f"/internal/profiles/people/{person.id}",
            entity="person",
            metadata={"resource_id": str(person.id), "email": person.email},
            tenant_id=tenant_id,
        )

        self.db.commit()
        return PersonReadSchema.model_validate(person)

    async def get_person(self, tenant_id: int, person_id: int) -> PersonReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        person = self.db.execute(
            select(PersonModel).where(
                and_(
                    PersonModel.id == person_id,
                    PersonModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

        assert_resource_belongs_to_tenant(
            person,
            tenant_id,
            resource_name="Person",
            resource_id=person_id,
        )
        return PersonReadSchema.model_validate(person)

    async def update_person(
        self,
        tenant_id: int,
        person_id: int,
        request: PersonUpdateSchema,
        updated_by: str,
    ) -> PersonReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        person = self.db.execute(
            select(PersonModel).where(
                and_(
                    PersonModel.id == person_id,
                    PersonModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        assert_resource_belongs_to_tenant(
            person,
            tenant_id,
            resource_name="Person",
            resource_id=person_id,
        )

        validate_version_match(person.version, request.version)

        if request.email is not None:
            person.email = request.email
        if request.first_name is not None:
            person.first_name = request.first_name
        if request.last_name is not None:
            person.last_name = request.last_name
        if request.phone is not None:
            person.phone = request.phone
        if request.external_person_key is not None:
            person.external_person_key = request.external_person_key
        if request.status is not None:
            person.status = request.status.value
        if request.metadata_json is not None:
            person.metadata_json = request.metadata_json

        person.version += 1
        self.db.flush()
        self.db.refresh(person)

        _audit(
            actor=updated_by,
            action=build_audit_action("profiles", "person", "updated"),
            path=f"/internal/profiles/people/{person.id}",
            entity="person",
            metadata={"resource_id": str(person.id), "updates": request.model_dump(exclude_none=True)},
            tenant_id=tenant_id,
        )

        self.db.commit()
        return PersonReadSchema.model_validate(person)

    async def list_persons(
        self,
        tenant_id: int,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> PersonListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        filters = [PersonModel.tenant_id == tenant_id]
        if status is not None:
            filters.append(PersonModel.status == status)

        total = self.db.execute(
            select(func.count()).select_from(PersonModel).where(and_(*filters))
        ).scalar_one()

        persons = self.db.execute(
            select(PersonModel)
            .where(and_(*filters))
            .order_by(desc(PersonModel.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        return PersonListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[PersonReadSchema.model_validate(item) for item in persons],
        )


class DepartmentService:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_department(
        self,
        tenant_id: int,
        request: DepartmentCreateSchema,
        created_by: str,
    ) -> DepartmentReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)
        DepartmentRules.validate_parent_not_self(request.parent_department_id)

        if request.parent_department_id is not None:
            parent_department = self.db.execute(
                select(DepartmentModel).where(
                    and_(
                        DepartmentModel.id == request.parent_department_id,
                        DepartmentModel.tenant_id == tenant_id,
                    )
                )
            ).scalar_one_or_none()
            assert_resource_belongs_to_tenant(
                parent_department,
                tenant_id,
                resource_name="Department",
                resource_id=request.parent_department_id,
            )

        if request.head_person_id is not None:
            head_person = self.db.execute(
                select(PersonModel).where(
                    and_(
                        PersonModel.id == request.head_person_id,
                        PersonModel.tenant_id == tenant_id,
                    )
                )
            ).scalar_one_or_none()
            DepartmentRules.validate_head_belongs_to_tenant(head_person, tenant_id)

        department = DepartmentModel(
            tenant_id=tenant_id,
            code=request.code,
            name=request.name,
            unit_type=request.unit_type.value,
            parent_department_id=request.parent_department_id,
            head_person_id=request.head_person_id,
            email=request.email,
            phone=request.phone,
            location=request.location,
            status=request.status.value,
            metadata_json=request.metadata_json,
            created_by=created_by,
        )

        self.db.add(department)
        self.db.flush()
        self.db.refresh(department)

        _audit(
            actor=created_by,
            action=build_audit_action("profiles", "department", "created"),
            path=f"/internal/profiles/departments/{department.id}",
            entity="department",
            metadata={
                "resource_id": str(department.id),
                "code": department.code,
                "parent_department_id": department.parent_department_id,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return DepartmentReadSchema.model_validate(department)

    async def list_departments(
        self,
        tenant_id: int,
        *,
        page: int = 1,
        page_size: int = 50,
        unit_type: str | None = None,
    ) -> DepartmentListResponseSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        filters = [DepartmentModel.tenant_id == tenant_id]
        if unit_type:
            filters.append(DepartmentModel.unit_type == unit_type)

        total = self.db.execute(
            select(func.count()).select_from(DepartmentModel).where(and_(*filters))
        ).scalar_one()

        rows = self.db.execute(
            select(DepartmentModel)
            .where(and_(*filters))
            .order_by(DepartmentModel.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).scalars().all()

        return DepartmentListResponseSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=[DepartmentReadSchema.model_validate(item) for item in rows],
        )


class ProgramService:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_program(
        self,
        tenant_id: int,
        request: ProgramCreateSchema,
        created_by: str,
    ) -> ProgramReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        department = self.db.execute(
            select(DepartmentModel).where(
                and_(
                    DepartmentModel.id == request.department_id,
                    DepartmentModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        ProgramRules.validate_department_belongs_to_tenant(department, tenant_id)

        program = ProgramModel(
            tenant_id=tenant_id,
            department_id=request.department_id,
            code=request.code,
            title=request.title,
            degree_type=request.degree_type.value,
            status=request.status.value,
            metadata_json=request.metadata_json,
            created_by=created_by,
        )

        self.db.add(program)
        self.db.flush()
        self.db.refresh(program)

        _audit(
            actor=created_by,
            action=build_audit_action("profiles", "program", "created"),
            path=f"/internal/profiles/programs/{program.id}",
            entity="program",
            metadata={
                "resource_id": str(program.id),
                "department_id": program.department_id,
                "code": program.code,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return ProgramReadSchema.model_validate(program)


class StudentService:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_student(
        self,
        tenant_id: int,
        request: StudentCreateSchema,
        created_by: str,
    ) -> StudentReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        person = self.db.execute(
            select(PersonModel).where(
                and_(
                    PersonModel.id == request.person_id,
                    PersonModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        StudentRules.validate_person_eligible(person, tenant_id)

        program = self.db.execute(
            select(ProgramModel).where(
                and_(
                    ProgramModel.id == request.program_id,
                    ProgramModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        StudentRules.validate_program_eligible(program, tenant_id)

        existing_role = self.db.execute(
            select(StudentModel).where(
                and_(
                    StudentModel.person_id == request.person_id,
                    StudentModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        StudentRules.validate_no_existing_student_role(existing_role, request.person_id, tenant_id)

        student = StudentModel(
            tenant_id=tenant_id,
            person_id=request.person_id,
            program_id=request.program_id,
            student_number=request.student_number,
            cohort_year=request.cohort_year,
            status=request.status.value,
            metadata_json=request.metadata_json,
            created_by=created_by,
        )

        self.db.add(student)
        self.db.flush()
        self.db.refresh(student)

        _audit(
            actor=created_by,
            action=build_audit_action("profiles", "student", "created"),
            path=f"/internal/profiles/students/{student.id}",
            entity="student",
            metadata={
                "resource_id": str(student.id),
                "person_id": student.person_id,
                "program_id": student.program_id,
                "student_number": student.student_number,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return StudentReadSchema.model_validate(student)


class FacultyService:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_faculty(
        self,
        tenant_id: int,
        request: FacultyCreateSchema,
        created_by: str,
    ) -> FacultyReadSchema:
        tenant_id = validate_tenant_id_provided(tenant_id)

        person = self.db.execute(
            select(PersonModel).where(
                and_(
                    PersonModel.id == request.person_id,
                    PersonModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        FacultyRules.validate_person_eligible(person, tenant_id)

        department = self.db.execute(
            select(DepartmentModel).where(
                and_(
                    DepartmentModel.id == request.department_id,
                    DepartmentModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        FacultyRules.validate_department_eligible(department, tenant_id)

        existing_role = self.db.execute(
            select(FacultyModel).where(
                and_(
                    FacultyModel.person_id == request.person_id,
                    FacultyModel.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()
        FacultyRules.validate_no_existing_faculty_role(existing_role, request.person_id, tenant_id)

        faculty = FacultyModel(
            tenant_id=tenant_id,
            person_id=request.person_id,
            department_id=request.department_id,
            faculty_number=request.faculty_number,
            academic_title=request.academic_title,
            status=request.status.value,
            metadata_json=request.metadata_json,
            created_by=created_by,
        )

        self.db.add(faculty)
        self.db.flush()
        self.db.refresh(faculty)

        _audit(
            actor=created_by,
            action=build_audit_action("profiles", "faculty", "created"),
            path=f"/internal/profiles/faculty/{faculty.id}",
            entity="faculty",
            metadata={
                "resource_id": str(faculty.id),
                "person_id": faculty.person_id,
                "department_id": faculty.department_id,
                "faculty_number": faculty.faculty_number,
            },
            tenant_id=tenant_id,
        )

        self.db.commit()
        return FacultyReadSchema.model_validate(faculty)


__all__ = [
    "DepartmentService",
    "FacultyService",
    "PersonService",
    "ProgramService",
    "StudentService",
    "IntegrityError",
]