"""W31 domain-depth tests — IP management hardening upgrade.

Focus:
- Cross-entity guard: inventor must have active faculty contract
- Fail-closed behavior on lookup failure
- Guard-before-persist ordering
- Existing cap + licensing side-effect behavior regression checks
"""
from __future__ import annotations

import importlib
import types

import pytest



def _load_service() -> types.ModuleType:
    return importlib.import_module("app.modules.ip_management.service")


class TestW31Constants:
    def test_source_contains_new_guard_symbols(self) -> None:
        import inspect

        svc = _load_service()
        src = inspect.getsource(svc)
        assert "_check_inventors_have_active_contracts_for_ip_asset" in src
        assert "_INVENTOR_REQUIRED_ASSET_STATUSES" in src
        assert "_INVENTOR_ACTIVE_CONTRACT_STATUSES" in src
        assert "DomainValidationError" in src


class TestW31ParseInventors:
    def test_parse_none(self) -> None:
        svc = _load_service()
        assert svc._parse_inventor_ids(None) == []

    def test_parse_empty_string(self) -> None:
        svc = _load_service()
        assert svc._parse_inventor_ids("   ") == []

    def test_parse_csv(self) -> None:
        svc = _load_service()
        assert svc._parse_inventor_ids("f1,f2,f3") == ["f1", "f2", "f3"]

    def test_parse_csv_with_spaces(self) -> None:
        svc = _load_service()
        assert svc._parse_inventor_ids(" f1 , f2 ,  f3 ") == ["f1", "f2", "f3"]

    def test_parse_csv_deduplicates(self) -> None:
        svc = _load_service()
        assert svc._parse_inventor_ids("f1,f1,f2") == ["f1", "f2"]

    def test_parse_list(self) -> None:
        svc = _load_service()
        assert svc._parse_inventor_ids(["f1", "f2"]) == ["f1", "f2"]

    def test_parse_tuple_with_blanks(self) -> None:
        svc = _load_service()
        assert svc._parse_inventor_ids(("f1", "", "f2")) == ["f1", "f2"]

    def test_parse_scalar(self) -> None:
        svc = _load_service()
        assert svc._parse_inventor_ids(101) == ["101"]


class TestW31GuardRequiredness:
    @pytest.mark.parametrize(
        "status,comm_status,required",
        [
            ("draft", "none", False),
            ("draft", "licensed", True),
            ("filed", "none", True),
            ("granted", "none", True),
            ("active", "none", True),
            ("archived", "sold", True),
        ],
    )
    def test_guard_requiredness_matrix(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: str,
        comm_status: str,
        required: bool,
    ) -> None:
        svc = _load_service()

        calls = {"contracts_lookup": 0}

        def fake_list(entity_name: str, _tenant_id: int):
            if entity_name == "faculty_contracts":
                calls["contracts_lookup"] += 1
                return [{"faculty_id": "f1", "status": "active"}]
            return []

        monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)

        if required:
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=1,
                ip_type="patent",
                status=status,
                commercialization_status=comm_status,
                inventor_ids_raw="f1",
            )
            assert calls["contracts_lookup"] == 1
        else:
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=1,
                ip_type="patent",
                status=status,
                commercialization_status=comm_status,
                inventor_ids_raw="",
            )
            assert calls["contracts_lookup"] == 0


class TestW31GuardFailures:
    @pytest.mark.parametrize(
        "status,comm_status",
        [
            ("filed", "none"),
            ("granted", "none"),
            ("active", "none"),
            ("draft", "licensed"),
            ("archived", "sold"),
        ],
    )
    def test_required_guard_blocks_without_inventors(
        self,
        status: str,
        comm_status: str,
    ) -> None:
        svc = _load_service()
        with pytest.raises(svc.DomainValidationError, match="inventor_ids"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=1,
                ip_type="patent",
                status=status,
                commercialization_status=comm_status,
                inventor_ids_raw="",
            )

    def test_guard_fail_closed_on_contract_lookup_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()

        def boom(_name: str, _tenant_id: int):
            raise RuntimeError("db down")

        monkeypatch.setattr(svc, "list_entities_for_tenant", boom)

        with pytest.raises(svc.DomainValidationError, match="faculty_contracts lookup failed"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=1,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw="f1",
            )

    def test_guard_blocks_when_no_contracts_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()
        monkeypatch.setattr(svc, "list_entities_for_tenant", lambda _n, _t: [])

        with pytest.raises(svc.DomainValidationError, match="without active faculty contract"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=1,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw="f_missing",
            )

    def test_guard_blocks_when_contract_inactive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()

        monkeypatch.setattr(
            svc,
            "list_entities_for_tenant",
            lambda _n, _t: [{"faculty_id": "f1", "status": "terminated"}],
        )

        with pytest.raises(svc.DomainValidationError, match="f1"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=1,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw="f1",
            )

    def test_guard_blocks_when_any_inventor_inactive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()

        monkeypatch.setattr(
            svc,
            "list_entities_for_tenant",
            lambda _n, _t: [
                {"faculty_id": "f1", "status": "active"},
                {"faculty_id": "f2", "status": "terminated"},
            ],
        )

        with pytest.raises(svc.DomainValidationError, match="f2"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=1,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw="f1,f2",
            )


class TestW31GuardSuccess:
    def test_guard_passes_for_active_single_inventor(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()
        monkeypatch.setattr(
            svc,
            "list_entities_for_tenant",
            lambda _n, _t: [{"faculty_id": "f1", "status": "active"}],
        )

        svc._check_inventors_have_active_contracts_for_ip_asset(
            tenant_id=1,
            ip_type="patent",
            status="filed",
            commercialization_status="none",
            inventor_ids_raw="f1",
        )

    def test_guard_passes_for_all_active_multiple_inventors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()
        monkeypatch.setattr(
            svc,
            "list_entities_for_tenant",
            lambda _n, _t: [
                {"faculty_id": "f1", "status": "active"},
                {"faculty_id": "f2", "status": "active"},
            ],
        )

        svc._check_inventors_have_active_contracts_for_ip_asset(
            tenant_id=1,
            ip_type="patent",
            status="granted",
            commercialization_status="none",
            inventor_ids_raw=["f1", "f2"],
        )

    def test_guard_ignores_non_required_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()

        def fail_if_called(_n: str, _t: int):
            raise AssertionError("faculty_contracts lookup should not happen")

        monkeypatch.setattr(svc, "list_entities_for_tenant", fail_if_called)

        svc._check_inventors_have_active_contracts_for_ip_asset(
            tenant_id=1,
            ip_type="copyright",
            status="draft",
            commercialization_status="none",
            inventor_ids_raw=None,
        )


class TestW31CreatePath:
    def test_create_calls_guard_before_persist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()
        calls: list[str] = []

        def fake_guard(**_kwargs):
            calls.append("guard")

        def fake_list(entity_name: str, _tenant_id: int):
            calls.append(f"list:{entity_name}")
            return []

        def fake_create(entity_name: str, payload: dict, tenant_id: int):
            calls.append(f"create:{entity_name}")
            return {**payload, "id": 10, "tenant_id": tenant_id}

        monkeypatch.setattr(svc, "_check_inventors_have_active_contracts_for_ip_asset", fake_guard)
        monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
        monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

        svc.create_ip_asset(
            {
                "asset_code": "IP-001",
                "title": "New Patent",
                "ip_type": "patent",
                "status": "draft",
                "inventor_ids": "f1",
            },
            tenant_id=3,
        )

        assert calls[0] == "guard"
        assert any(c.startswith("create:ip_assets") for c in calls)

    def test_create_blocked_by_guard_does_not_persist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()

        def fake_guard(**_kwargs):
            raise svc.DomainValidationError("blocked")

        persisted = {"called": False}

        def fake_create(_entity_name: str, _payload: dict, _tenant_id: int):
            persisted["called"] = True
            return {}

        monkeypatch.setattr(svc, "_check_inventors_have_active_contracts_for_ip_asset", fake_guard)
        monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

        with pytest.raises(svc.DomainValidationError, match="blocked"):
            svc.create_ip_asset(
                {
                    "asset_code": "IP-002",
                    "title": "Blocked",
                    "ip_type": "patent",
                    "status": "filed",
                    "inventor_ids": "f1",
                },
                tenant_id=9,
            )

        assert persisted["called"] is False

    def test_create_cap_guard_still_blocks_when_limit_reached(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()
        cap = svc._IP_TYPE_MAX_ACTIVE_ASSETS["patent"]

        def fake_list(entity_name: str, _tenant_id: int):
            if entity_name == "ip_assets":
                return [{"ip_type": "patent", "status": "filed"} for _ in range(cap)]
            if entity_name == "faculty_contracts":
                return [{"faculty_id": "f1", "status": "active"}]
            return []

        monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)

        with pytest.raises(ValueError, match="cap"):
            svc.create_ip_asset(
                {
                    "asset_code": "IP-003",
                    "title": "Cap Hit",
                    "ip_type": "patent",
                    "status": "filed",
                    "inventor_ids": "f1",
                },
                tenant_id=1,
            )

    def test_create_succeeds_below_cap_with_valid_inventor(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()

        created: list[tuple[str, dict]] = []

        def fake_list(entity_name: str, _tenant_id: int):
            if entity_name == "ip_assets":
                return []
            if entity_name == "faculty_contracts":
                return [{"faculty_id": "f1", "status": "active"}]
            if entity_name == "ip_licensing_records":
                return []
            return []

        def fake_create(entity_name: str, payload: dict, tenant_id: int):
            rec = {**payload, "id": len(created) + 1, "tenant_id": tenant_id}
            created.append((entity_name, rec))
            return rec

        monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
        monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

        result = svc.create_ip_asset(
            {
                "asset_code": "IP-004",
                "title": "Good Asset",
                "ip_type": "patent",
                "status": "filed",
                "inventor_ids": "f1",
            },
            tenant_id=2,
        )
        assert result["asset_code"] == "IP-004"
        assert created[0][0] == "ip_assets"


class TestW31LicensingSideEffect:
    def test_commercialized_asset_creates_licensing_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()
        created: list[tuple[str, dict]] = []

        def fake_list(entity_name: str, _tenant_id: int):
            if entity_name == "faculty_contracts":
                return [{"faculty_id": "f1", "status": "active"}]
            return []

        def fake_create(entity_name: str, payload: dict, tenant_id: int):
            rec = {**payload, "id": len(created) + 1, "tenant_id": tenant_id}
            created.append((entity_name, rec))
            return rec

        monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
        monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

        svc.create_ip_asset(
            {
                "asset_code": "IP-C1",
                "title": "Commercial Asset",
                "ip_type": "copyright",
                "status": "draft",
                "commercialization_status": "licensed",
                "inventor_ids": "f1",
            },
            tenant_id=11,
        )

        names = [name for name, _ in created]
        assert "ip_assets" in names
        assert "ip_licensing_records" in names

    def test_non_commercialized_asset_skips_licensing_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()
        created: list[tuple[str, dict]] = []

        def fake_list(entity_name: str, _tenant_id: int):
            if entity_name == "faculty_contracts":
                return []
            return []

        def fake_create(entity_name: str, payload: dict, tenant_id: int):
            rec = {**payload, "id": len(created) + 1, "tenant_id": tenant_id}
            created.append((entity_name, rec))
            return rec

        monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
        monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

        svc.create_ip_asset(
            {
                "asset_code": "IP-N1",
                "title": "Non Commercial",
                "ip_type": "patent",
                "status": "draft",
                "commercialization_status": "none",
            },
            tenant_id=11,
        )

        assert [name for name, _ in created] == ["ip_assets"]

    def test_ensure_licensing_record_is_idempotent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        svc = _load_service()

        existing = [{"source_entity_id": "77", "integration_source": "ip_commercialization"}]
        created: list[tuple[str, dict]] = []

        def fake_list(entity_name: str, _tenant_id: int):
            if entity_name == "ip_licensing_records":
                return existing
            return []

        def fake_create(entity_name: str, payload: dict, tenant_id: int):
            created.append((entity_name, {**payload, "tenant_id": tenant_id}))
            return {**payload, "id": 90, "tenant_id": tenant_id}

        monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
        monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

        svc._ensure_ip_licensing_record({"id": 77, "asset_code": "A-77"}, tenant_id=1)
        assert created == []


class TestW31BusinessInvariants:
    @pytest.mark.parametrize("ip_type", ["patent", "trademark", "copyright", "trade_secret"])
    def test_cap_map_contains_expected_types(self, ip_type: str) -> None:
        svc = _load_service()
        assert ip_type in svc._IP_TYPE_MAX_ACTIVE_ASSETS

    @pytest.mark.parametrize("status", ["filed", "granted", "active"])
    def test_active_statuses_are_guarded(self, status: str) -> None:
        svc = _load_service()
        assert status in svc._INVENTOR_REQUIRED_ASSET_STATUSES

    @pytest.mark.parametrize("status", ["licensed", "commercialized", "sold"])
    def test_commercial_statuses_trigger_contract_validation(self, status: str) -> None:
        svc = _load_service()
        assert status in svc._COMMERCIAL_STATUSES

    def test_active_contract_status_contains_active(self) -> None:
        svc = _load_service()
        assert "active" in svc._INVENTOR_ACTIVE_CONTRACT_STATUSES
