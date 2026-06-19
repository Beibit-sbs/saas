from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.main import app
from app.modules.finance_procurement_asset import permissions, service
from app.modules.rbac.security import get_actor


BACKEND_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = BACKEND_DIR / "app" / "modules" / "finance_procurement_asset"
MIGRATION_FILE = BACKEND_DIR / "alembic" / "versions" / "fpa40a2rt01_a0402_finance_procurement_asset_tables.py"


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_no_hard_delete_patterns_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    assert "session.delete" not in text
    assert ".delete(" not in text
    assert "DELETE FROM" not in text


def test_no_provider_or_external_call_patterns_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    for marker in ["requests.post", "requests.get", "httpx", "boto3", "smtplib", "send_email", "send_sms"]:
        assert marker not in text.lower()


def test_explicit_false_safety_flags_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    for marker in [
        "FAKE_METRICS = False",
        "FAKE_FINANCE_DATA = False",
        "FAKE_PAYMENT_DATA = False",
        "PROVIDER_CONNECTED = False",
        "LIVE_BANK_SYNC = False",
        "LIVE_ERP_SYNC = False",
        "PAYMENT_EXECUTION_ENABLED = False",
        "AUTOMATIC_PROCUREMENT_APPROVAL_ENABLED = False",
        "AUTOMATIC_BUDGET_APPROVAL_ENABLED = False",
        "AUTOMATIC_VENDOR_AWARD_ENABLED = False",
        "HIDDEN_SCORE_PRESENT = False",
    ]:
        assert marker in text


def test_no_forbidden_execution_or_hidden_score_markers_present() -> None:
    text = "\n".join(path.read_text() for path in MODULE_DIR.glob("*.py"))
    for marker in ["def execute_payment", "sync_bank_live", "sync_1c_live", "approve_procurement_auto", "approve_budget_auto", "award_vendor_auto", "HiddenVendorScore", "HiddenFinanceScore"]:
        assert marker not in text


def test_dashboard_and_health_have_no_fake_metrics_or_hidden_scores() -> None:
    db = _db()
    with patch("app.modules.finance_procurement_asset.service.repository.get_dashboard_inputs", return_value={"billing": {"VISIBLE_METADATA_ONLY": 1}}):
        dashboard = service.get_dashboard(db, 1)
    health = service.get_health(db, 1)
    assert dashboard.fake_metrics is False
    assert dashboard.hidden_score_present is False
    assert health["fake_metrics"] is False
    assert health["hidden_score_present"] is False


def test_bridge_methods_are_metadata_only() -> None:
    db = _db()
    with patch("app.modules.finance_procurement_asset.service.repository.get_bridge_inputs", return_value=[]):
        bridge = service.get_bridge_provider_readiness(db, 1)
    assert bridge.payment_execution_enabled is False
    assert bridge.automatic_vendor_award_enabled is False


def test_migration_create_drop_sets_match_24() -> None:
    text = MIGRATION_FILE.read_text()
    assert text.count('op.create_table("fpa_') == 24
    assert text.count('op.drop_table("fpa_') == 24


def test_all_routes_are_actor_and_permission_guarded() -> None:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith("/api/admin/finance-procurement-asset")]
    assert len(routes) == 57
    for route in routes:
        dependency_calls = [getattr(dep.call, "__name__", "") for dep in route.dependant.dependencies]
        assert "get_actor" in dependency_calls
        assert len(route.dependant.dependencies) >= 4


def test_permission_inventory_count_is_exact() -> None:
    assert len(permissions.ALL_PERMISSIONS) == 51