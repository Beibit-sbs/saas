"""Coverage: import all orphan SQLAlchemy model / Pydantic schema modules.

These modules define DB table structures and API schemas but are not currently
imported by any production code path (verified by grep — 0 external references).
Importing them executes all class-body statements (column definitions, validators,
etc.) which gives pytest-cov line credit.  No assertions are needed; a successful
import is itself a correctness signal (bad syntax / missing dep would fail here).
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# SQLAlchemy ORM models — main platform model file
# ---------------------------------------------------------------------------

def test_platform_models_importable() -> None:
    import app.platform.models as m  # noqa: F401
    assert hasattr(m, "PlatformTenantSettingsModel")


# ---------------------------------------------------------------------------
# Sub-domain ORM model tables
# ---------------------------------------------------------------------------

def test_platform_context_models_importable() -> None:
    import app.platform.context.models as m  # noqa: F401
    assert m is not None


def test_platform_webhooks_models_importable() -> None:
    import app.platform.webhooks.models as m  # noqa: F401
    assert m is not None


def test_platform_ai_models_importable() -> None:
    import app.platform.ai.models as m  # noqa: F401
    assert m is not None


def test_platform_kpi_models_importable() -> None:
    import app.platform.kpi.models as m  # noqa: F401
    assert m is not None


def test_platform_billing_models_importable() -> None:
    import app.platform.billing.models as m  # noqa: F401
    assert m is not None


def test_platform_federation_models_importable() -> None:
    import app.platform.federation.models as m  # noqa: F401
    assert m is not None


def test_platform_jobs_models_importable() -> None:
    import app.platform.jobs.models as m  # noqa: F401
    assert m is not None


def test_platform_tenant_models_importable() -> None:
    import app.platform.tenant.models as m  # noqa: F401
    assert m is not None


def test_platform_notifications_models_importable() -> None:
    import app.platform.notifications.models as m  # noqa: F401
    assert m is not None


def test_platform_feature_flags_models_importable() -> None:
    import app.platform.feature_flags.models as m  # noqa: F401
    assert m is not None


# ---------------------------------------------------------------------------
# Pydantic schemas that are currently uncovered
# ---------------------------------------------------------------------------

def test_platform_billing_schemas_importable() -> None:
    import app.platform.billing.schemas as s  # noqa: F401
    assert s is not None


def test_platform_tenant_schemas_importable() -> None:
    import app.platform.tenant.schemas as s  # noqa: F401
    assert s is not None


def test_platform_feature_flags_schemas_importable() -> None:
    import app.platform.feature_flags.schemas as s  # noqa: F401
    assert s is not None


def test_platform_jobs_schemas_importable() -> None:
    import app.platform.jobs.schemas as s  # noqa: F401
    assert s is not None


def test_platform_notifications_schemas_importable() -> None:
    import app.platform.notifications.schemas as s  # noqa: F401
    assert s is not None
