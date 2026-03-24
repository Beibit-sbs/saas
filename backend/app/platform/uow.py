from __future__ import annotations

from dataclasses import dataclass

from app.platform.repository.billing_repository import BillingRepository
from app.platform.repository.db import db_available, db_url, ensure_platform_core_schema
from app.platform.repository.feature_flag_repository import FeatureFlagRepository
from app.platform.idempotency.repository import IdempotencyRepository
from app.platform.repository.job_repository import JobRepository
from app.platform.repository.notification_repository import NotificationRepository
from app.platform.repository.tenant_repository import TenantRepository
from app.platform.repository.usage_repository import UsageRepository

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None


# Shared repository instances keep in-memory fallback state stable across requests/tests.
_SHARED_TENANT_REPOSITORY = TenantRepository()
_SHARED_FEATURE_FLAG_REPOSITORY = FeatureFlagRepository()
_SHARED_BILLING_REPOSITORY = BillingRepository()
_SHARED_USAGE_REPOSITORY = UsageRepository()
_SHARED_JOB_REPOSITORY = JobRepository()
_SHARED_NOTIFICATION_REPOSITORY = NotificationRepository()
_SHARED_IDEMPOTENCY_REPOSITORY = IdempotencyRepository()


@dataclass
class UnitOfWork:
    tenant_repository: TenantRepository = _SHARED_TENANT_REPOSITORY
    feature_flag_repository: FeatureFlagRepository = _SHARED_FEATURE_FLAG_REPOSITORY
    billing_repository: BillingRepository = _SHARED_BILLING_REPOSITORY
    usage_repository: UsageRepository = _SHARED_USAGE_REPOSITORY
    job_repository: JobRepository = _SHARED_JOB_REPOSITORY
    notification_repository: NotificationRepository = _SHARED_NOTIFICATION_REPOSITORY
    idempotency_repository: IdempotencyRepository = _SHARED_IDEMPOTENCY_REPOSITORY

    def __post_init__(self) -> None:
        self.conn: object | None = None

    def __enter__(self) -> UnitOfWork:
        if db_available() and db_url() and psycopg is not None:
            self.conn = psycopg.connect(db_url(), connect_timeout=5)
            ensure_platform_core_schema(self.conn)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.conn is None:
            return
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            self.conn.close()
            self.conn = None
