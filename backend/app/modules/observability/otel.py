"""Optional OpenTelemetry SDK instrumentation.

Activated only when ``OTEL_EXPORTER_OTLP_ENDPOINT`` is set in the environment.
When the variable is absent (local development, tests), this module is a no-op
and adds zero runtime overhead.

Usage from ``app/main.py`` lifespan:

    from app.modules.observability.otel import setup_otel, teardown_otel
    setup_otel(app)   # call once at startup
    teardown_otel()   # call on shutdown (optional – flushes pending spans)

The OTEL exporter sends spans over gRPC to the configured OTLP endpoint
(e.g. an OpenTelemetry Collector sidecar or Grafana Tempo direct-ingest).
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger("app.otel")

_provider = None  # holds TracerProvider when OTEL is active


def _is_otel_enabled() -> bool:
    return bool(os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip())


def setup_otel(app: "FastAPI") -> None:
    """Initialise OTEL SDK and instrument FastAPI if the endpoint is configured.

    Safe to call unconditionally — does nothing when the endpoint is not set.
    """
    global _provider  # noqa: PLW0603

    if not _is_otel_enabled():
        logger.debug("OTEL_EXPORTER_OTLP_ENDPOINT not set — OpenTelemetry disabled")
        return

    endpoint = os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"].strip()
    service_name = os.environ.get("OTEL_SERVICE_NAME", "ai-platform-backend")

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        resource = Resource.create({SERVICE_NAME: service_name})
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _provider = provider

        FastAPIInstrumentor.instrument_app(app)

        logger.info(
            "OpenTelemetry enabled — service=%s endpoint=%s",
            service_name,
            endpoint,
        )
    except Exception as exc:  # noqa: BLE001
        # Never crash the application over observability setup failures.
        logger.error("OpenTelemetry setup failed (continuing without OTEL): %s", exc)


def teardown_otel() -> None:
    """Flush and shut down the TracerProvider cleanly on application shutdown."""
    global _provider  # noqa: PLW0603

    if _provider is None:
        return
    try:
        _provider.shutdown()
        logger.info("OpenTelemetry TracerProvider shut down")
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenTelemetry shutdown error (ignored): %s", exc)
    finally:
        _provider = None
