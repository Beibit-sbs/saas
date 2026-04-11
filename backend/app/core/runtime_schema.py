from __future__ import annotations

import logging
from threading import Lock

from app.core.config import runtime_schema_bootstrap_scope
from app.core.db import get_raw_conn
from app.modules.ai_gateway.service import _ensure_ai_gateway_tables
from app.modules.audit.service import _ensure_table_once as ensure_audit_table_once
from app.modules.auth.preferences_service import _ensure_preferences_table
from app.modules.auth.session_service import _ensure_session_table
from app.modules.billing.service import _ensure_db as ensure_billing_schema
from app.modules.i18n.service import _ensure_schema_and_seed
from app.modules.integrations.service import _ensure_table_once as ensure_integration_settings_once
from app.modules.jobs.service import _ensure_schema_once as ensure_jobs_schema_once
from app.modules.plans.service import _ensure_db as ensure_plans_schema
from app.modules.quotas.service import _ensure_db as ensure_quotas_schema
from app.modules.quotas.service import _ensure_seeded_db as ensure_quotas_seeded_db
from app.modules.rbac.service import _ensure_schema_and_seed_once as ensure_rbac_schema_once
from app.modules.usage.service import _ensure_table_once as ensure_usage_table_once
from app.platform.repository.db import ensure_platform_core_schema


logger = logging.getLogger("app.audit")
_runtime_schema_bootstrap_lock = Lock()
_runtime_schema_bootstrap_done = False


def bootstrap_runtime_schema() -> None:
    global _runtime_schema_bootstrap_done
    if _runtime_schema_bootstrap_done:
        return

    with _runtime_schema_bootstrap_lock:
        if _runtime_schema_bootstrap_done:
            return

        with runtime_schema_bootstrap_scope():
            with get_raw_conn() as conn:
                if conn is None:
                    logger.info("runtime schema bootstrap skipped: database unavailable")
                    _runtime_schema_bootstrap_done = True
                    return

                ensure_platform_core_schema(conn)
                _ensure_session_table(conn)
                _ensure_preferences_table(conn)
                ensure_audit_table_once(conn)
                ensure_integration_settings_once(conn)
                ensure_usage_table_once(conn)
                _ensure_schema_and_seed(conn)
                _ensure_ai_gateway_tables(conn)
                ensure_billing_schema(conn)
                ensure_plans_schema(conn)
                ensure_quotas_schema(conn)
                ensure_quotas_seeded_db(conn)
                ensure_jobs_schema_once(conn)
                ensure_rbac_schema_once(conn)

        _runtime_schema_bootstrap_done = True
        logger.info("runtime schema bootstrap completed during startup")
