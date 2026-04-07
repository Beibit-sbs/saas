from collections.abc import Generator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session


def get_profiles_db(request: Request) -> Generator[Session, None, None]:
    session_factory = getattr(request.app.state, "profiles_session_factory", None)
    if session_factory is None:
        raise HTTPException(status_code=503, detail="profiles database session is not configured")

    session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()