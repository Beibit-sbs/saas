"""Document Workflow OS — DB session dependency."""

from __future__ import annotations

import time
from collections.abc import Generator

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.dependency_logging import log_dependency_unavailable
from app.modules.observability.perf_profile import perf_segment


def get_doc_workflow_db(request: Request) -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session from the doc_workflow session factory."""
    started = time.perf_counter()
    with perf_segment("db.session.open"):
        session_factory = getattr(request.app.state, "doc_workflow_session_factory", None)
    if session_factory is None:
        log_dependency_unavailable(
            request,
            dependency="doc_workflow_db_session",
            reason="doc_workflow session factory is not configured",
            started_at=started,
        )
        raise HTTPException(
            status_code=503,
            detail="document_workflow_os database session is not configured",
        )
    with perf_segment("db.session.create"):
        session = session_factory()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            with perf_segment("db.session.close"):
                close()
