from collections.abc import Generator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session


def get_students_db(request: Request) -> Generator[Session, None, None]:
    """Provide DB session for Students module.

    Prefers dedicated students_session_factory when configured, and falls back
    to profiles_session_factory to stay compatible with current app wiring.
    """
    session_factory = getattr(request.app.state, "students_session_factory", None)
    if session_factory is None:
        session_factory = getattr(request.app.state, "profiles_session_factory", None)
    if session_factory is None:
        raise HTTPException(status_code=503, detail="students database session is not configured")

    session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()
