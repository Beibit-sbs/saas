from __future__ import annotations

import logging
import time

from fastapi import Request


_dependency_logger = logging.getLogger("app.dependency")


def log_dependency_unavailable(
    request: Request,
    *,
    dependency: str,
    reason: str,
    started_at: float,
) -> None:
    elapsed_ms = round((time.perf_counter() - started_at) * 1000.0, 2)
    _dependency_logger.warning(
        "dependency_unavailable",
        extra={
            "dependency": dependency,
            "reason": reason,
            "timing_ms": elapsed_ms,
            "path": request.url.path,
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None),
            "trace_id": getattr(request.state, "trace_id", None),
            "tenant_id": getattr(request.state, "request_tenant_id", None),
        },
    )
