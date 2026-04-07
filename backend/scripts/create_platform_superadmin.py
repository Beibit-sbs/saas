# ruff: noqa: E402

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.modules.auth.platform_superadmin_service import ensure_platform_superadmin


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update platform superadmin account (explicit one-time management command)."
    )
    parser.add_argument("--login", required=True, help="Platform superadmin login")
    parser.add_argument(
        "--password",
        help="Platform superadmin password. If omitted, secure prompt is used.",
    )
    parser.add_argument("--email", help="Optional email", default=None)
    parser.add_argument(
        "--update-password",
        action="store_true",
        help="Update password for existing account. By default existing password is kept.",
    )
    parser.add_argument(
        "--force-password-change",
        action="store_true",
        help="Mark account for forced password change on first login.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    password = args.password
    if password is None:
        password = getpass.getpass("Platform superadmin password: ")

    result = ensure_platform_superadmin(
        login=str(args.login),
        password=str(password),
        email=args.email,
        update_password=bool(args.update_password),
        force_password_change=bool(args.force_password_change),
    )
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
