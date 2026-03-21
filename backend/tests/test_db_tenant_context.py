import pytest

from app.modules.security.db_tenant_context import set_db_tenant_context


class _FakeCursor:
    def __init__(self, calls: list[tuple[str, tuple[str, ...]]]) -> None:
        self._calls = calls

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query: str, params: tuple[str, ...]) -> None:
        self._calls.append((query, params))


class _FakeConn:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self.calls)


def test_set_db_tenant_context_sets_local_pg_setting() -> None:
    conn = _FakeConn()
    set_db_tenant_context(conn, tenant_id=42)

    assert len(conn.calls) == 1
    query, params = conn.calls[0]
    assert "set_config('app.tenant_id'" in query
    assert params == ("42",)


@pytest.mark.parametrize("tenant_id", [None, 0, -1])
def test_set_db_tenant_context_requires_positive_tenant(tenant_id: int | None) -> None:
    conn = _FakeConn()
    with pytest.raises(ValueError):
        set_db_tenant_context(conn, tenant_id=tenant_id)
