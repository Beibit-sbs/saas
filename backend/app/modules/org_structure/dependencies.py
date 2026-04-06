from __future__ import annotations

from collections.abc import Generator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session


def get_org_structure_db(request: Request) -> Generator[Session, None, None]:
    session_factory = getattr(request.app.state, "org_structure_session_factory", None)
    if session_factory is None:
        # fall back to shared admissions engine
        session_factory = getattr(request.app.state, "admissions_session_factory", None)
    if session_factory is None:
        raise HTTPException(status_code=503, detail="org_structure database session is not configured")

    session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()
