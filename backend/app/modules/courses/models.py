from sqlalchemy import BigInteger, ForeignKey, Integer, String
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
