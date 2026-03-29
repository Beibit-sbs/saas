from collections.abc import Generator
import time

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.dependency_logging import log_dependency_unavailable
from app.modules.observability.perf_profile import perf_segment


def get_students_db(request: Request) -> Generator[Session, None, None]:
    """Provide DB session for Students module.

    Prefers dedicated students_session_factory when configured, and falls back
    to profiles_session_factory to stay compatible with current app wiring.
    """
    started = time.perf_counter()
    with perf_segment("db.session.open"):
        session_factory = getattr(request.app.state, "students_session_factory", None)
    if session_factory is None:
        session_factory = getattr(request.app.state, "profiles_session_factory", None)
    if session_factory is None:
        log_dependency_unavailable(
            request,
            dependency="students_db_session",
            reason="students/profiles session factory is not configured",
            started_at=started,
        )
        raise HTTPException(status_code=503, detail="students database session is not configured")

    with perf_segment("db.session.create"):
        session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            with perf_segment("db.session.close"):
                close()
