from collections.abc import Generator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session


def get_grades_db(request: Request) -> Generator[Session, None, None]:
    """Provide DB session for Grades module.

    Grades currently share the admissions/profiles engine until a dedicated
    grades session factory is wired in app startup.
    """
    session_factory = getattr(request.app.state, "grades_session_factory", None)
    if session_factory is None:
        session_factory = getattr(request.app.state, "profiles_session_factory", None)
    if session_factory is None:
        raise HTTPException(status_code=503, detail="grades database session is not configured")

    session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()
