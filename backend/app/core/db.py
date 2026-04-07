from __future__ import annotations

import contextlib
import logging
import os
import threading
from typing import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_db_connect_options

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
        connect_args={"connect_timeout": 5, "options": get_db_connect_options()},
    )


def make_session_factory(engine: Engine) -> sessionmaker:
    """Return a ``sessionmaker`` bound to *engine*.

    Sessions are created with ``autoflush=False`` and ``autocommit=False`` so
    callers control exactly when flushes and commits happen — the same safe
    default used by the SQLAlchemy docs and most FastAPI patterns.
    """
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ---------------------------------------------------------------------------
# Process-level singleton engine & raw-connection pool
# ---------------------------------------------------------------------------
_engine_lock = threading.Lock()
_shared_engine: Engine | None = None


def _get_shared_engine() -> Engine | None:
    global _shared_engine
    if _shared_engine is not None:
        return _shared_engine
    with _engine_lock:
        if _shared_engine is not None:
            return _shared_engine
        url = os.environ.get("DATABASE_URL", "").strip()
        if not url:
            return None
        try:
            _shared_engine = build_engine(pool_size=10, max_overflow=20)
        except Exception:
            return None
    return _shared_engine


@contextlib.contextmanager
def get_raw_conn() -> Generator:
    """Yield a native psycopg connection borrowed from the process-level pool.

    Usage matches ``psycopg.connect()`` — the connection supports
    ``conn.cursor()``, ``conn.commit()``, ``conn.rollback()``.
    Commits/rollbacks are the caller's responsibility; the context manager
    only returns the connection to the pool on exit.

    Falls back to ``None`` when ``DATABASE_URL`` is absent (test isolation).
    """
    engine = _get_shared_engine()
    if engine is None:
        yield None
        return
    raw = engine.raw_connection()
    try:
        yield raw
    except Exception:
        try:
            raw.rollback()
        except Exception:
            pass
        raise
    finally:
        # Always rollback before returning to pool to clean up any
        # uncommitted state (especially from read-only callers that never commit).
        try:
            raw.rollback()
        except Exception:
            pass
        raw.close()  # returns to pool, does NOT drop the physical connection
