from __future__ import annotations

from typing import Any


def run_post_operation_rehydration(*, operation: str) -> dict[str, Any]:
    """Rehydrate runtime caches after out-of-band persistent state changes.

    This hook must be called after operations that mutate DB state outside normal
    runtime write-paths (for example restore, migration, bulk import).
    """

    from app.modules.auth.local_users_service import local_user_store
    from app.modules.integrations.service import clear_settings_read_cache

    clear_settings_read_cache()
    local_user_store.reload_from_persistent_state()

    return {
        "operation": str(operation).strip().lower() or "unknown",
        "rehydrated": True,
        "components": [
            "settings_read_cache",
            "local_user_store",
        ],
    }


def rehydrate_after_restore() -> dict[str, Any]:
    return run_post_operation_rehydration(operation="restore")


def rehydrate_after_migration() -> dict[str, Any]:
    return run_post_operation_rehydration(operation="migration")


def rehydrate_after_bulk_import() -> dict[str, Any]:
    return run_post_operation_rehydration(operation="bulk_import")
