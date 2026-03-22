from __future__ import annotations

import logging
import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _normalize_db_url(url: str) -> str:
    """Rewrite plain ``postgresql://`` URLs to use the psycopg (v3) driver.

    Alembic applies the same normalisation in ``alembic/env.py``.  Having it
    here keeps the production engine consistent with migrations.
    """
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def build_engine(
    *,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_timeout: int = 30,
) -> Engine:
    """Create a synchronous SQLAlchemy engine from the ``DATABASE_URL`` env var.

    Pool settings (conservative defaults suited for a multi-worker deployment):
    - ``pool_size=5``       — persistent connections kept open per process
    - ``max_overflow=10``   — burst headroom before requests queue
    - ``pool_pre_ping=True``— validates connections before use; avoids
                              stale-connection errors after idle periods
    - ``pool_timeout=30``   — seconds to wait for a connection before raising

    Raises ``RuntimeError`` if ``DATABASE_URL`` is not set so callers can
    decide whether to abort startup or log a warning.
    """
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set; "
            "cannot create the application database engine."
        )
    return create_engine(
        _normalize_db_url(url),
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_timeout=pool_timeout,
    )


def make_session_factory(engine: Engine) -> sessionmaker:
    """Return a ``sessionmaker`` bound to *engine*.

    Sessions are created with ``autoflush=False`` and ``autocommit=False`` so
    callers control exactly when flushes and commits happen — the same safe
    default used by the SQLAlchemy docs and most FastAPI patterns.
    """
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
