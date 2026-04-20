from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from opentelemetry import trace


_tracer = trace.get_tracer(__name__)


@contextmanager
def f3_operation_span(
    operation_name: str,
    *,
    tenant_id: int,
    cohort_id: int | None = None,
    playbook_id: int | None = None,
    actor: str | None = None,
) -> Generator[None, None, None]:
    """Record a scoped F3 span without affecting business-flow execution.

    The global tracer provider can be disabled in local/test envs; in that case
    this context manager remains effectively a no-op.
    """

    with _tracer.start_as_current_span(f"f3.{operation_name}") as span:
        span.set_attribute("tenant_id", tenant_id)
        if cohort_id is not None:
            span.set_attribute("cohort_id", cohort_id)
        if playbook_id is not None:
            span.set_attribute("playbook_id", playbook_id)
        if actor:
            span.set_attribute("actor", actor)
        yield
