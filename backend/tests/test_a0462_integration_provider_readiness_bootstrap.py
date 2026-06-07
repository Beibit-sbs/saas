from __future__ import annotations

import importlib

from app.main import app
from app.modules.integration_provider_readiness import API_PREFIX, EXPECTED_PERMISSION_COUNT, EXPECTED_ROUTE_COUNT
from app.modules.integration_provider_readiness.permissions import PERMISSION_COUNT


def test_a0462_module_imports() -> None:
    module = importlib.import_module("app.modules.integration_provider_readiness.router")
    assert hasattr(module, "router")


def test_a0462_permission_count_bootstrap() -> None:
    assert PERMISSION_COUNT == EXPECTED_PERMISSION_COUNT == 42


def test_a0462_route_count_bootstrap() -> None:
    operations = 0
    for path, methods in app.openapi()["paths"].items():
        if path.startswith(API_PREFIX):
            operations += len(methods)
    assert operations == EXPECTED_ROUTE_COUNT

