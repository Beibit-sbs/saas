from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CourseModel(Base):
    __tablename__ = "university_courses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    program_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("university_programs.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False)


class CoursePrerequisiteModel(Base):
    """Records a prerequisite course that must be COMPLETED before enrolling in `course_id`."""

    __tablename__ = "university_course_prerequisites"
    __table_args__ = (
        UniqueConstraint("tenant_id", "course_id", "prerequisite_course_id", name="uq_course_prereq"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    course_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("university_courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    prerequisite_course_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("university_courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
