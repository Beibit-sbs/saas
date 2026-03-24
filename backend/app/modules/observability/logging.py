"""JSON structured logging with request_id propagation."""
from __future__ import annotations

import json
import logging
from contextvars import ContextVar

# Stores the current request_id for the running async/sync context.
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="-")
actor_id_var: ContextVar[str] = ContextVar("actor_id", default="-")


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: dict = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get("-"),
            "tenant_id": tenant_id_var.get("-"),
            "actor_id": actor_id_var.get("-"),
        }
        for key in ("method", "path", "status_code", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class _RequestIdFilter(logging.Filter):
    """Inject request context from ContextVar into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        record.tenant_id = tenant_id_var.get("-")
        record.actor_id = actor_id_var.get("-")
        return True


def configure_json_logging(level: int = logging.INFO) -> None:
    """
    Replace the root handler with a JSON formatter.
    Call once at application startup (before uvicorn installs its own handlers).
    """
    formatter = _JsonFormatter()
    filter_ = _RequestIdFilter()

    root = logging.getLogger()
    root.setLevel(level)

    # Replace all existing handlers on root logger
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(filter_)
    root.addHandler(handler)

    # Route uvicorn loggers through root so output stays in JSON format.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
