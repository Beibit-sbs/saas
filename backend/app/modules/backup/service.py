import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.modules.integrations.service import get_runtime_value, save_setting

_BACKUP_HISTORY_LIMIT = 100
_backup_history: dict[int, list[dict[str, Any]]] = {}


def _require_tenant_id(tenant_id: int | None, *, operation: str) -> int:
    if tenant_id is None:
        raise ValueError(f"tenant_id is required for {operation}")
    normalized = int(tenant_id)
    if normalized <= 0:
        raise ValueError("tenant_id must be positive")
    return normalized


def _retention_days(tenant_id: int) -> int:
    raw = get_runtime_value(
        "backup.retention_days",
        "BACKUP_RETENTION_DAYS",
        "14",
        tenant_id=tenant_id,
    )
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return 14
    return max(0, min(value, 3650))


def _retention_min_files(tenant_id: int) -> int:
    raw = get_runtime_value(
        "backup.retention_min_files",
        "BACKUP_RETENTION_MIN_FILES",
        "3",
        tenant_id=tenant_id,
    )
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return 3
    return max(0, min(value, 1000))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _allowed_roots() -> list[str]:
    raw = os.getenv("BACKUP_ALLOWED_ROOTS", "/tmp/app-backups,/var/backups/app")
    roots: list[str] = []
    for item in raw.split(","):
        value = item.strip()
        if not value:
            continue
        roots.append(str(Path(value).expanduser().resolve()))
    return roots


def _is_path_allowed(path_value: str, roots: list[str]) -> bool:
    target = Path(path_value).expanduser().resolve()
    for root in roots:
        root_path = Path(root).expanduser().resolve()
        if target == root_path or target.is_relative_to(root_path):
            return True
    return False


def _normalize_profile(profile: dict[str, Any], roots: list[str]) -> dict[str, str]:
    profile_id = str(profile.get("id", "")).strip().lower()
    label = str(profile.get("label", "")).strip()
    path_raw = str(profile.get("path", "")).strip()

    if not profile_id:
        raise ValueError("backup profile id is required")
    if not label:
        raise ValueError(f"backup profile '{profile_id}' label is required")
    if not path_raw:
        raise ValueError(f"backup profile '{profile_id}' path is required")

    profile_path = Path(path_raw).expanduser().resolve()
    if not profile_path.is_absolute():
        raise ValueError(f"backup profile '{profile_id}' path must be absolute")
    if not _is_path_allowed(str(profile_path), roots):
        raise ValueError(
            f"backup profile '{profile_id}' path is outside allowed roots"
        )

    return {
        "id": profile_id,
        "label": label,
        "path": str(profile_path),
    }


def _default_profiles() -> list[dict[str, str]]:
    raw = os.getenv("BACKUP_PROFILES_JSON", "").strip()
    roots = _allowed_roots()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and parsed:
                normalized = [_normalize_profile(item, roots) for item in parsed]
                ids = [item["id"] for item in normalized]
                if len(ids) != len(set(ids)):
                    raise ValueError("duplicate backup profile ids")
                return normalized
        except (ValueError, json.JSONDecodeError):
            pass

    return [
        {
            "id": "local",
            "label": "Local backup volume",
            "path": str(Path("/tmp/app-backups/local").resolve()),
        },
        {
            "id": "archive",
            "label": "Archive backup volume",
            "path": str(Path("/tmp/app-backups/archive").resolve()),
        },
    ]


def get_backup_settings_for_admin(tenant_id: int | None = None) -> dict[str, Any]:
    tenant = _require_tenant_id(tenant_id, operation="get_backup_settings_for_admin")
    roots = _allowed_roots()
    profiles_json = get_runtime_value(
        "backup.profiles_json",
        "BACKUP_PROFILES_JSON",
        "",
        tenant_id=tenant,
    )

    if profiles_json:
        try:
            parsed = json.loads(profiles_json)
            profiles = [_normalize_profile(item, roots) for item in parsed]
        except (ValueError, json.JSONDecodeError):
            profiles = _default_profiles()
    else:
        profiles = _default_profiles()

    seen_ids: set[str] = set()
    deduped: list[dict[str, str]] = []
    for profile in profiles:
        if profile["id"] in seen_ids:
            continue
        seen_ids.add(profile["id"])
        deduped.append(profile)
    profiles = deduped

    configured_active = get_runtime_value(
        "backup.active_profile",
        "BACKUP_DEFAULT_PROFILE",
        "",
        tenant_id=tenant,
    )
    active_profile = configured_active.strip().lower() if configured_active else ""
    available_ids = {profile["id"] for profile in profiles}
    if active_profile not in available_ids:
        active_profile = profiles[0]["id"] if profiles else ""

    return {
        "active_profile": active_profile,
        "profiles": profiles,
        "allowed_roots": roots,
        "retention_days": _retention_days(tenant),
        "retention_min_files": _retention_min_files(tenant),
    }


def save_backup_settings(payload: dict[str, Any], tenant_id: int | None = None) -> dict[str, Any]:
    tenant = _require_tenant_id(tenant_id, operation="save_backup_settings")
    roots = _allowed_roots()
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, list) or not raw_profiles:
        raise ValueError("at least one backup profile is required")

    profiles = [_normalize_profile(item, roots) for item in raw_profiles]
    ids = [item["id"] for item in profiles]
    if len(ids) != len(set(ids)):
        raise ValueError("backup profile ids must be unique")

    active_profile = str(payload.get("active_profile", "")).strip().lower()
    if not active_profile:
        raise ValueError("active backup profile is required")
    if active_profile not in set(ids):
        raise ValueError("active backup profile must exist in profiles")

    save_setting(
        "backup.profiles_json",
        json.dumps(profiles),
        is_secret=False,
        tenant_id=tenant,
    )
    save_setting(
        "backup.active_profile",
        active_profile,
        is_secret=False,
        tenant_id=tenant,
    )

    if payload.get("retention_days") is not None:
        try:
            retention_days = int(payload.get("retention_days"))
        except (TypeError, ValueError) as exc:
            raise ValueError("retention_days must be an integer") from exc
        if retention_days < 0 or retention_days > 3650:
            raise ValueError("retention_days must be between 0 and 3650")
        save_setting(
            "backup.retention_days",
            str(retention_days),
            is_secret=False,
            tenant_id=tenant,
        )

    if payload.get("retention_min_files") is not None:
        try:
            retention_min_files = int(payload.get("retention_min_files"))
        except (TypeError, ValueError) as exc:
            raise ValueError("retention_min_files must be an integer") from exc
        if retention_min_files < 0 or retention_min_files > 1000:
            raise ValueError("retention_min_files must be between 0 and 1000")
        save_setting(
            "backup.retention_min_files",
            str(retention_min_files),
            is_secret=False,
            tenant_id=tenant,
        )

    return get_backup_settings_for_admin(tenant_id=tenant)


def _run_pg_dump_command(db_url: str, output_path: str) -> None:
    subprocess.run(
        [
            "pg_dump",
            f"--dbname={db_url}",
            "--format=custom",
            f"--file={output_path}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _run_pg_restore_command(db_url: str, input_path: str) -> None:
    subprocess.run(
        [
            "pg_restore",
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            f"--dbname={db_url}",
            input_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _record_history(entry: dict[str, Any], tenant_id: int) -> None:
    rows = _backup_history.setdefault(tenant_id, [])
    rows.insert(0, entry)
    if len(rows) > _BACKUP_HISTORY_LIMIT:
        del rows[_BACKUP_HISTORY_LIMIT:]


def list_backup_history(tenant_id: int | None = None) -> list[dict[str, Any]]:
    tenant = _require_tenant_id(tenant_id, operation="list_backup_history")
    return list(_backup_history.get(tenant, []))


def _resolve_profile(settings: dict[str, Any], profile_id: str | None = None) -> dict[str, str]:
    requested = (profile_id or settings.get("active_profile") or "").strip().lower()
    profiles = settings.get("profiles", [])
    profile = next((item for item in profiles if item["id"] == requested), None)
    if profile is None:
        raise ValueError("backup profile is not configured")
    return profile


def list_restore_candidates(profile_id: str | None = None, tenant_id: int | None = None) -> dict[str, Any]:
    tenant = _require_tenant_id(tenant_id, operation="list_restore_candidates")
    settings = get_backup_settings_for_admin(tenant_id=tenant)
    profile = _resolve_profile(settings, profile_id=profile_id)

    profile_dir = Path(profile["path"]).expanduser().resolve()
    candidates: list[dict[str, Any]] = []

    if profile_dir.exists() and profile_dir.is_dir():
        for item in sorted(
            profile_dir.glob("*.dump"),
            key=lambda row: row.stat().st_mtime,
            reverse=True,
        ):
            stat = item.stat()
            candidates.append(
                {
                    "file_name": item.name,
                    "file_path": str(item),
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )

    return {
        "profile_id": profile["id"],
        "profile_label": profile["label"],
        "profile_path": str(profile_dir),
        "candidates": candidates[:100],
    }


def _resolve_restore_file(profile_path: str, file_name: str | None) -> Path:
    profile_dir = Path(profile_path).expanduser().resolve()
    if not profile_dir.exists() or not profile_dir.is_dir():
        raise ValueError("backup profile directory does not exist")

    if file_name and file_name.strip():
        name = file_name.strip()
        target = (profile_dir / name).resolve()
        if target.parent != profile_dir:
            raise ValueError("restore file must be inside selected profile directory")
        if not target.exists() or not target.is_file():
            raise ValueError("restore file does not exist")
        return target

    newest = sorted(
        profile_dir.glob("*.dump"),
        key=lambda row: row.stat().st_mtime,
        reverse=True,
    )
    if not newest:
        raise ValueError("no backup files found for selected profile")
    return newest[0]


def run_restore_now(
    actor: str,
    profile_id: str | None,
    file_name: str | None,
    dry_run: bool,
    confirm_text: str | None,
    tenant_id: int | None = None,
) -> dict[str, Any]:
    tenant = _require_tenant_id(tenant_id, operation="run_restore_now")
    settings = get_backup_settings_for_admin(tenant_id=tenant)
    profile = _resolve_profile(settings, profile_id=profile_id)

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise ValueError("DATABASE_URL is not configured")

    restore_file = _resolve_restore_file(profile["path"], file_name)
    job_id = str(uuid.uuid4())
    started_at = _now_iso()
    base_result = {
        "job_id": job_id,
        "job_type": "restore",
        "profile_id": profile["id"],
        "profile_label": profile["label"],
        "file_path": str(restore_file),
        "size_bytes": restore_file.stat().st_size,
        "started_at": started_at,
        "actor": actor,
    }

    if dry_run:
        planned = {
            **base_result,
            "tenant_id": tenant,
            "status": "planned",
            "finished_at": _now_iso(),
            "command_preview": f"pg_restore --clean --if-exists --no-owner --no-privileges --dbname=<DATABASE_URL> {restore_file}",
        }
        _record_history(planned, tenant_id=tenant)
        return planned

    if (confirm_text or "").strip().upper() != "RESTORE":
        raise ValueError("confirm_text must be RESTORE for non-dry-run restore")

    try:
        _run_pg_restore_command(database_url, str(restore_file))
        completed = {
            **base_result,
            "tenant_id": tenant,
            "status": "completed",
            "finished_at": _now_iso(),
        }
        _record_history(completed, tenant_id=tenant)
        return completed
    except FileNotFoundError as exc:
        failed = {
            **base_result,
            "tenant_id": tenant,
            "status": "failed",
            "finished_at": _now_iso(),
            "error": "pg_restore is not available in backend runtime",
        }
        _record_history(failed, tenant_id=tenant)
        raise ValueError("pg_restore is not available in backend runtime") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "pg_restore failed").strip()[:300]
        failed = {
            **base_result,
            "tenant_id": tenant,
            "status": "failed",
            "finished_at": _now_iso(),
            "error": detail,
        }
        _record_history(failed, tenant_id=tenant)
        raise ValueError(f"restore failed: {detail}") from exc


def apply_retention_policy(
    profile_id: str | None,
    dry_run: bool,
    actor: str,
    tenant_id: int | None = None,
) -> dict[str, Any]:
    tenant = _require_tenant_id(tenant_id, operation="apply_retention_policy")
    settings = get_backup_settings_for_admin(tenant_id=tenant)
    profile = _resolve_profile(settings, profile_id=profile_id)
    profile_dir = Path(profile["path"]).expanduser().resolve()
    if not profile_dir.exists() or not profile_dir.is_dir():
        raise ValueError("backup profile directory does not exist")

    retention_days = int(settings.get("retention_days", 14))
    retention_min_files = int(settings.get("retention_min_files", 3))
    now_ts = datetime.now(timezone.utc).timestamp()
    cutoff_ts = now_ts - (retention_days * 86400)

    dumps = sorted(
        [row for row in profile_dir.glob("*.dump") if row.is_file()],
        key=lambda row: row.stat().st_mtime,
        reverse=True,
    )

    keep_set = set(dumps[:retention_min_files])
    to_delete: list[Path] = []
    for item in dumps[retention_min_files:]:
        if item.stat().st_mtime < cutoff_ts:
            to_delete.append(item)
            continue
        keep_set.add(item)

    deleted_files: list[str] = []
    if not dry_run:
        for item in to_delete:
            item.unlink(missing_ok=True)
            deleted_files.append(str(item))

    result = {
        "job_id": str(uuid.uuid4()),
        "job_type": "retention",
        "tenant_id": tenant,
        "status": "planned" if dry_run else "completed",
        "profile_id": profile["id"],
        "profile_label": profile["label"],
        "retention_days": retention_days,
        "retention_min_files": retention_min_files,
        "deleted_count": len(to_delete) if dry_run else len(deleted_files),
        "deleted_files": [str(row) for row in to_delete] if dry_run else deleted_files,
        "scanned_count": len(dumps),
        "kept_count": len(dumps) - len(to_delete),
        "started_at": _now_iso(),
        "finished_at": _now_iso(),
        "actor": actor,
    }
    _record_history(result, tenant_id=tenant)
    return result


def run_backup_now(actor: str, tenant_id: int | None = None) -> dict[str, Any]:
    tenant = _require_tenant_id(tenant_id, operation="run_backup_now")

    from app.modules.billing.service import assert_billing_write_allowed, assert_quota_with_increment

    assert_billing_write_allowed(tenant, action="backup.run_now")
    assert_quota_with_increment(tenant, "backup_storage_mb", increment=0)

    settings = get_backup_settings_for_admin(tenant_id=tenant)
    active_profile = str(settings.get("active_profile", ""))
    profiles = settings.get("profiles", [])

    profile = next((item for item in profiles if item["id"] == active_profile), None)
    if profile is None:
        raise ValueError("active backup profile is not configured")

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise ValueError("DATABASE_URL is not configured")

    backup_dir = Path(profile["path"]).expanduser().resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_name = datetime.now(timezone.utc).strftime("backup-%Y%m%d-%H%M%S.dump")
    output_path = backup_dir / backup_name

    job_id = str(uuid.uuid4())
    started_at = _now_iso()

    try:
        _run_pg_dump_command(database_url, str(output_path))
        size_bytes = output_path.stat().st_size if output_path.exists() else 0
        result = {
            "job_id": job_id,
            "job_type": "backup",
            "tenant_id": tenant,
            "status": "completed",
            "profile_id": profile["id"],
            "profile_label": profile["label"],
            "file_path": str(output_path),
            "size_bytes": size_bytes,
            "started_at": started_at,
            "finished_at": _now_iso(),
            "actor": actor,
        }
        _record_history(result, tenant_id=tenant)

        try:
            from app.modules.usage.service import record_usage_event

            record_usage_event(tenant, "backups_created", 1)
            record_usage_event(tenant, "backup_storage_mb", int(size_bytes / (1024 * 1024)))
        except Exception:
            pass

        return result
    except FileNotFoundError as exc:
        failure = {
            "job_id": job_id,
            "job_type": "backup",
            "tenant_id": tenant,
            "status": "failed",
            "profile_id": profile["id"],
            "profile_label": profile["label"],
            "file_path": str(output_path),
            "size_bytes": 0,
            "started_at": started_at,
            "finished_at": _now_iso(),
            "actor": actor,
            "error": "pg_dump is not available in backend runtime",
        }
        _record_history(failure, tenant_id=tenant)
        raise ValueError("pg_dump is not available in backend runtime") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "pg_dump failed").strip()[:300]
        failure = {
            "job_id": job_id,
            "job_type": "backup",
            "tenant_id": tenant,
            "status": "failed",
            "profile_id": profile["id"],
            "profile_label": profile["label"],
            "file_path": str(output_path),
            "size_bytes": 0,
            "started_at": started_at,
            "finished_at": _now_iso(),
            "actor": actor,
            "error": detail,
        }
        _record_history(failure, tenant_id=tenant)
        raise ValueError(f"backup failed: {detail}") from exc
