from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AcademicRecordModel(Base):
    __tablename__ = "university_academic_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("university_students.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("university_courses.id", ondelete="CASCADE"), nullable=False)
    grade: Mapped[str] = mapped_column(String(16), nullable=False)
    semester: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)
