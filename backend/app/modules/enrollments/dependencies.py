from collections.abc import Generator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session


def get_enrollments_db(request: Request) -> Generator[Session, None, None]:
    """Provide DB session for Enrollments module.

    Enrollment currently shares the same engine with profiles/students and
    falls back to profiles_session_factory while dedicated wiring is absent.
    """
    session_factory = getattr(request.app.state, "enrollments_session_factory", None)
    if session_factory is None:
        session_factory = getattr(request.app.state, "profiles_session_factory", None)
    if session_factory is None:
        raise HTTPException(status_code=503, detail="enrollments database session is not configured")

    session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()
