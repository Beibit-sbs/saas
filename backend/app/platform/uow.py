from __future__ import annotations

from dataclasses import dataclass

from app.platform.analytics.repository import AnalyticsRepository
from app.platform.ai.repository import AiCopilotRepository
from app.platform.ai.recommendations.repository import AiRecommendationRepository
from app.platform.automation.repository import AutomationRepository
from app.platform.automation.templates.repository import AutomationTemplateRepository
from app.platform.context.repository import ContextRepository
from app.platform.kpi.repository import KpiRepository
from app.platform.repository.billing_repository import BillingRepository
from app.platform.repository.db import db_available, db_url, ensure_platform_core_schema
from app.platform.repository.feature_flag_repository import FeatureFlagRepository
from app.platform.events.repository import OutboxEventRepository
from app.platform.idempotency.repository import IdempotencyRepository
from app.platform.repository.job_repository import JobRepository
from app.platform.repository.notification_repository import NotificationRepository
from app.platform.repository.tenant_repository import TenantRepository
from app.platform.repository.usage_repository import UsageRepository
from app.platform.webhooks.repository import WebhookRepository

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
_SHARED_ANALYTICS_REPOSITORY = AnalyticsRepository()
_SHARED_AI_COPILOT_REPOSITORY = AiCopilotRepository()
_SHARED_AI_RECOMMENDATION_REPOSITORY = AiRecommendationRepository()
_SHARED_AUTOMATION_REPOSITORY = AutomationRepository()
_SHARED_AUTOMATION_TEMPLATE_REPOSITORY = AutomationTemplateRepository()
_SHARED_CONTEXT_REPOSITORY = ContextRepository()
_SHARED_KPI_REPOSITORY = KpiRepository()
_SHARED_OUTBOX_EVENT_REPOSITORY = OutboxEventRepository()
_SHARED_WEBHOOK_REPOSITORY = WebhookRepository()


@dataclass
class UnitOfWork:
    tenant_repository: TenantRepository = _SHARED_TENANT_REPOSITORY
    feature_flag_repository: FeatureFlagRepository = _SHARED_FEATURE_FLAG_REPOSITORY
    billing_repository: BillingRepository = _SHARED_BILLING_REPOSITORY
    usage_repository: UsageRepository = _SHARED_USAGE_REPOSITORY
    job_repository: JobRepository = _SHARED_JOB_REPOSITORY
    notification_repository: NotificationRepository = _SHARED_NOTIFICATION_REPOSITORY
    idempotency_repository: IdempotencyRepository = _SHARED_IDEMPOTENCY_REPOSITORY
    analytics_repository: AnalyticsRepository = _SHARED_ANALYTICS_REPOSITORY
    ai_copilot_repository: AiCopilotRepository = _SHARED_AI_COPILOT_REPOSITORY
    ai_recommendation_repository: AiRecommendationRepository = _SHARED_AI_RECOMMENDATION_REPOSITORY
    automation_repository: AutomationRepository = _SHARED_AUTOMATION_REPOSITORY
    automation_template_repository: AutomationTemplateRepository = _SHARED_AUTOMATION_TEMPLATE_REPOSITORY
    context_repository: ContextRepository = _SHARED_CONTEXT_REPOSITORY
    kpi_repository: KpiRepository = _SHARED_KPI_REPOSITORY
    outbox_event_repository: OutboxEventRepository = _SHARED_OUTBOX_EVENT_REPOSITORY
    webhook_repository: WebhookRepository = _SHARED_WEBHOOK_REPOSITORY

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
