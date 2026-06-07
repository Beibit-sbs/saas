from __future__ import annotations

import pytest

from app.modules.integration_provider_readiness import EXPECTED_PERMISSION_COUNT
from app.modules.integration_provider_readiness import permissions


class TestPermissionInventory:
    def test_permission_count(self) -> None:
        assert len(permissions.ALL_PERMISSIONS) == EXPECTED_PERMISSION_COUNT == 42

    def test_permission_inventory_count(self) -> None:
        assert len(permissions.PERMISSION_INVENTORY) == 42

    def test_permission_slugs_unique(self) -> None:
        assert len(set(permissions.ALL_PERMISSIONS)) == 42

    @pytest.mark.parametrize("slug", permissions.ALL_PERMISSIONS)
    def test_permission_slug_prefix(self, slug: str) -> None:
        assert slug.startswith("admin.integration_provider_readiness.")

    @pytest.mark.parametrize("spec", permissions.PERMISSION_INVENTORY, ids=[item["slug"] for item in permissions.PERMISSION_INVENTORY])
    def test_permission_has_family(self, spec: dict[str, object]) -> None:
        assert spec["family"]

    @pytest.mark.parametrize("spec", permissions.PERMISSION_INVENTORY, ids=[item["slug"] for item in permissions.PERMISSION_INVENTORY])
    def test_permission_has_workflow(self, spec: dict[str, object]) -> None:
        assert spec["workflow"]

    @pytest.mark.parametrize("spec", permissions.PERMISSION_INVENTORY, ids=[item["slug"] for item in permissions.PERMISSION_INVENTORY])
    def test_permission_has_allowed_roles(self, spec: dict[str, object]) -> None:
        assert len(spec["roles"]) > 0


class TestPermissionFamilies:
    @pytest.mark.parametrize(
        ("family", "expected"),
        [
            ("registry", 4),
            ("profile", 4),
            ("capability", 4),
            ("readiness_assessment", 4),
            ("evidence", 5),
            ("compliance_security", 6),
            ("risk_exception", 4),
            ("audit", 3),
            ("integration_plan", 4),
            ("dashboard", 4),
        ],
    )
    def test_family_count(self, family: str, expected: int) -> None:
        actual = sum(1 for spec in permissions.PERMISSION_INVENTORY if spec["family"] == family)
        assert actual == expected
