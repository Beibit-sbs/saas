from __future__ import annotations

import os

import pytest

from app.modules.university_core import shared as university_shared
from app.modules.university_core.entity_impl import validate_entity_tables_impl


def test_all_entity_tables_exist() -> None:
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not configured for DB integration checks")

    expected_tables = {cfg.table for cfg in university_shared.ENTITY_CONFIGS.values()}
    result = validate_entity_tables_impl()

    missing = sorted(set(result.get("missing", [])))
    assert missing == [], f"Missing university_core tables: {', '.join(missing)}"

    present = set(result.get("present", []))
    assert expected_tables.issubset(present), "Not all ENTITY_CONFIGS tables are reported as present"
