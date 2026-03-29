from pathlib import Path


def _read(rel: str) -> str:
    return (Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")


def test_runtime_bootstrap_has_no_tenant_default_one() -> None:
    audit_text = _read("app/modules/audit/service.py")
    ai_text = _read("app/modules/ai_gateway/service.py")
    rbac_text = _read("app/modules/rbac/service.py")

    assert "tenant_id BIGINT NOT NULL DEFAULT 1" not in audit_text
    assert "tenant_id BIGINT NOT NULL DEFAULT 1" not in ai_text
    assert "tenant_id BIGINT NOT NULL DEFAULT 1" not in rbac_text


def test_runtime_bootstrap_has_no_silent_backfill_to_tenant_one() -> None:
    audit_text = _read("app/modules/audit/service.py")
    ai_text = _read("app/modules/ai_gateway/service.py")

    assert "UPDATE app_audit_events SET tenant_id = 1 WHERE tenant_id IS NULL" not in audit_text
    assert "UPDATE app_ai_models SET tenant_id = 1 WHERE tenant_id IS NULL" not in ai_text
    assert "UPDATE app_ai_usage_logs SET tenant_id = 1 WHERE tenant_id IS NULL" not in ai_text


def test_university_models_require_tenant_id_not_nullable() -> None:
    for rel in (
        "app/modules/courses/models.py",
        "app/modules/programs/models.py",
        "app/modules/faculty/models.py",
        "app/modules/academic_records/models.py",
    ):
        text = _read(rel)
        assert "tenant_id" in text
        assert "nullable=False" in text


def test_fail_closed_migration_exists_and_enforces_drop_default() -> None:
    migration = _read("alembic/versions/f1c2d3e4a5b7_tenant_fail_closed_platform_wide.py")

    assert "ALTER TABLE app_audit_events ALTER COLUMN tenant_id DROP DEFAULT" in migration
    assert "ALTER TABLE app_ai_models ALTER COLUMN tenant_id DROP DEFAULT" in migration
    assert "ALTER TABLE app_ai_usage_logs ALTER COLUMN tenant_id DROP DEFAULT" in migration
    assert "ALTER TABLE app_roles ALTER COLUMN tenant_id DROP DEFAULT" in migration
    assert "ALTER TABLE app_platform_developer_apps ALTER COLUMN tenant_id SET NOT NULL" in migration


def test_feature_flags_no_longer_use_null_tenant_rows() -> None:
    repo_text = _read("app/platform/repository/feature_flag_repository.py")
    model_text = _read("app/platform/models.py")

    assert "tenant_id IS NULL" not in repo_text
    assert "tenant_id: Mapped[int]" in model_text
    assert "nullable=False" in model_text
