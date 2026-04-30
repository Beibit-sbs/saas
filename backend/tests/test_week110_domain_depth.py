"""W110 — Research Publication × Research Grant cross-entity guard.

Business invariant: A research publication may only be created when the lead
author has at least one active research grant (status: active, planned,
submitted). Creating publications without grant backing produces phantom
research output, corrupts Brain Core KPIs, and misrepresents institutional
research productivity.

Guard: _check_author_has_active_grant() — BEFORE create_entity_for_tenant()
Fail-closed: if grant lookup raises any exception → DomainValidationError.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError

# ---------------------------------------------------------------------------
# Constants / module introspection
# ---------------------------------------------------------------------------

MODULE_PATH = "app.modules.research.service"


@pytest.fixture()
def svc():
    """Return a fresh import of the research service module."""
    import app.modules.research.service as m
    return m


# ===========================================================================
# GROUP 1 — Guard constant correctness
# ===========================================================================

class TestGrantActiveForPublicationConstant:
    def test_constant_exists(self, svc):
        assert hasattr(svc, "_GRANT_ACTIVE_FOR_PUBLICATION"), (
            "_GRANT_ACTIVE_FOR_PUBLICATION constant must exist"
        )

    def test_constant_is_frozenset(self, svc):
        assert isinstance(svc._GRANT_ACTIVE_FOR_PUBLICATION, frozenset)

    def test_active_in_constant(self, svc):
        assert "active" in svc._GRANT_ACTIVE_FOR_PUBLICATION

    def test_planned_in_constant(self, svc):
        assert "planned" in svc._GRANT_ACTIVE_FOR_PUBLICATION

    def test_submitted_in_constant(self, svc):
        assert "submitted" in svc._GRANT_ACTIVE_FOR_PUBLICATION

    def test_closed_not_in_constant(self, svc):
        assert "closed" not in svc._GRANT_ACTIVE_FOR_PUBLICATION

    def test_delayed_not_in_constant(self, svc):
        """Delayed grants do NOT satisfy authorship requirement."""
        assert "delayed" not in svc._GRANT_ACTIVE_FOR_PUBLICATION

    def test_constant_has_exactly_three_statuses(self, svc):
        assert len(svc._GRANT_ACTIVE_FOR_PUBLICATION) == 3


# ===========================================================================
# GROUP 2 — Guard function exists and is wired correctly
# ===========================================================================

class TestGuardFunctionExists:
    def test_check_function_exists(self, svc):
        assert hasattr(svc, "_check_author_has_active_grant"), (
            "_check_author_has_active_grant must be defined in research service"
        )

    def test_check_function_is_callable(self, svc):
        assert callable(svc._check_author_has_active_grant)

    def test_create_publication_calls_guard_before_persist(self):
        """Guard must fire before create_entity_for_tenant."""
        call_order: list[str] = []

        def fake_guard(*, tenant_id, lead_author_id):
            call_order.append("guard")

        def fake_create(entity_type, data, tenant_id):
            call_order.append("persist")
            return {
                "id": 1,
                "publication_code": data.get("publication_code", "PUB-001"),
                "title": data.get("title", "T"),
                "lead_author_id": data.get("lead_author_id", "A"),
                "target_venue": data.get("target_venue", "V"),
                "last_activity_days": 0,
                "status": data.get("status", "draft"),
            }

        def fake_list(entity_type, tenant_id):
            return []

        from app.modules.research.schemas import ResearchPublicationCreateSchema

        payload = ResearchPublicationCreateSchema(
            publication_code="PUB-TEST",
            title="Test Publication",
            lead_author_id="faculty-1",
            target_venue="Nature",
            status="draft",
        )

        import app.modules.research.service as svc_mod
        with (
            patch.object(svc_mod, "_check_author_has_active_grant", fake_guard),
            patch(
                "app.modules.research.service.create_entity_for_tenant",
                side_effect=fake_create,
            ),
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                side_effect=fake_list,
            ),
            patch(
                "app.modules.research.service.log_admin_action",
            ),
        ):
            svc_mod.create_research_publication(1, payload, "actor")

        assert call_order[0] == "guard", (
            "Guard must fire BEFORE persist; got order: " + str(call_order)
        )
        assert "persist" in call_order


# ===========================================================================
# GROUP 3 — Guard blocks: no grants at all
# ===========================================================================

AUTHOR_ID = "faculty-001"


def _make_grant(pi: str, status: str, gid: int = 1) -> dict:
    return {
        "id": gid,
        "grant_code": f"GR-{gid:03d}",
        "title": f"Grant {gid}",
        "pi_faculty_id": pi,
        "status": status,
        "deadline": "2028-12-31",
        "funding_amount": 100000.0,
        "sponsor_notes": None,
    }


class TestGuardBlocksNoGrant:
    def _run_guard(self, grants: list[dict], author: str = AUTHOR_ID):
        import app.modules.research.service as svc_mod
        with patch(
            "app.modules.research.service.list_entities_for_tenant",
            return_value=grants,
        ):
            svc_mod._check_author_has_active_grant(
                tenant_id=1,
                lead_author_id=author,
            )

    def test_empty_grants_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard([])

    def test_no_grants_for_author_blocked(self):
        """Grants exist but none belong to this author."""
        grants = [_make_grant("other-faculty", "active")]
        with pytest.raises(DomainValidationError):
            self._run_guard(grants)

    def test_closed_grant_blocked(self):
        grants = [_make_grant(AUTHOR_ID, "closed")]
        with pytest.raises(DomainValidationError):
            self._run_guard(grants)

    def test_delayed_grant_blocked(self):
        """Delayed grants do NOT count for publication authorship."""
        grants = [_make_grant(AUTHOR_ID, "delayed")]
        with pytest.raises(DomainValidationError):
            self._run_guard(grants)

    def test_unknown_status_blocked(self):
        grants = [_make_grant(AUTHOR_ID, "archived")]
        with pytest.raises(DomainValidationError):
            self._run_guard(grants)

    def test_error_message_contains_author_id(self):
        try:
            self._run_guard([])
        except DomainValidationError as exc:
            assert AUTHOR_ID in str(exc)
        else:
            pytest.fail("DomainValidationError not raised")

    def test_error_message_contains_active_statuses(self):
        try:
            self._run_guard([])
        except DomainValidationError as exc:
            msg = str(exc).lower()
            assert "active" in msg
        else:
            pytest.fail("DomainValidationError not raised")


# ===========================================================================
# GROUP 4 — Guard allows: author has qualifying grant
# ===========================================================================

class TestGuardAllows:
    def _run_guard(self, grants: list[dict], author: str = AUTHOR_ID):
        import app.modules.research.service as svc_mod
        with patch(
            "app.modules.research.service.list_entities_for_tenant",
            return_value=grants,
        ):
            svc_mod._check_author_has_active_grant(
                tenant_id=1,
                lead_author_id=author,
            )

    def test_active_grant_allowed(self):
        grants = [_make_grant(AUTHOR_ID, "active")]
        self._run_guard(grants)  # must not raise

    def test_planned_grant_allowed(self):
        grants = [_make_grant(AUTHOR_ID, "planned")]
        self._run_guard(grants)

    def test_submitted_grant_allowed(self):
        grants = [_make_grant(AUTHOR_ID, "submitted")]
        self._run_guard(grants)

    def test_active_grant_among_many_allowed(self):
        """One active grant is enough even if others are closed/delayed."""
        grants = [
            _make_grant(AUTHOR_ID, "closed", gid=1),
            _make_grant(AUTHOR_ID, "active", gid=2),
            _make_grant(AUTHOR_ID, "delayed", gid=3),
        ]
        self._run_guard(grants)

    def test_different_author_does_not_help(self):
        """Active grant for another author must NOT unblock this author."""
        grants = [_make_grant("other-pi", "active")]
        with pytest.raises(DomainValidationError):
            self._run_guard(grants, author=AUTHOR_ID)


# ===========================================================================
# GROUP 5 — Case-insensitive matching
# ===========================================================================

class TestCaseInsensitiveMatching:
    def _run_guard(self, grants: list[dict], author: str = AUTHOR_ID):
        import app.modules.research.service as svc_mod
        with patch(
            "app.modules.research.service.list_entities_for_tenant",
            return_value=grants,
        ):
            svc_mod._check_author_has_active_grant(
                tenant_id=1,
                lead_author_id=author,
            )

    def test_pi_uppercase_matched(self):
        grants = [_make_grant(AUTHOR_ID.upper(), "active")]
        self._run_guard(grants)

    def test_author_uppercase_matched(self):
        grants = [_make_grant(AUTHOR_ID, "active")]
        self._run_guard(grants, author=AUTHOR_ID.upper())

    def test_grant_status_uppercase_allowed(self):
        grant = _make_grant(AUTHOR_ID, "active")
        grant["status"] = "ACTIVE"
        self._run_guard([grant])

    def test_grant_status_mixed_case_allowed(self):
        grant = _make_grant(AUTHOR_ID, "active")
        grant["status"] = "Active"
        self._run_guard([grant])


# ===========================================================================
# GROUP 6 — Fail-closed: lookup exception → DomainValidationError
# ===========================================================================

class TestFailClosed:
    def test_lookup_exception_raises_domain_error(self):
        import app.modules.research.service as svc_mod
        with patch(
            "app.modules.research.service.list_entities_for_tenant",
            side_effect=RuntimeError("DB connection refused"),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                svc_mod._check_author_has_active_grant(
                    tenant_id=1,
                    lead_author_id=AUTHOR_ID,
                )
        assert "Cannot verify" in str(exc_info.value) or "lookup failed" in str(exc_info.value)

    def test_lookup_exception_does_not_allow_creation(self):
        """On lookup failure, creation must NOT proceed (fail-closed)."""
        import app.modules.research.service as svc_mod
        from app.modules.research.schemas import ResearchPublicationCreateSchema

        payload = ResearchPublicationCreateSchema(
            publication_code="PUB-FAIL",
            title="Fail Closed Test",
            lead_author_id=AUTHOR_ID,
            target_venue="ICLR",
            status="draft",
        )

        persisted = []

        def fake_list(entity_type, tenant_id):
            if entity_type == "research_grants":
                raise RuntimeError("connection lost")
            return []

        def fake_create(entity_type, data, tenant_id):
            persisted.append(data)
            return {"id": 1, **data}

        with (
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                side_effect=fake_list,
            ),
            patch(
                "app.modules.research.service.create_entity_for_tenant",
                side_effect=fake_create,
            ),
            patch("app.modules.research.service.log_admin_action"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_research_publication(1, payload, "actor")

        assert persisted == [], "create_entity_for_tenant must NOT be called when guard raises"

    def test_timeout_exception_fail_closed(self):
        import app.modules.research.service as svc_mod
        with patch(
            "app.modules.research.service.list_entities_for_tenant",
            side_effect=TimeoutError("grant lookup timed out"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod._check_author_has_active_grant(
                    tenant_id=1,
                    lead_author_id=AUTHOR_ID,
                )


# ===========================================================================
# GROUP 7 — Integration: create_research_publication end-to-end
# ===========================================================================

def _make_publication_payload(author: str = AUTHOR_ID, status: str = "draft"):
    from app.modules.research.schemas import ResearchPublicationCreateSchema
    return ResearchPublicationCreateSchema(
        publication_code="PUB-INT-001",
        title="Integration Test Publication",
        lead_author_id=author,
        target_venue="CVPR",
        status=status,
    )


def _fake_create_entity(entity_type, data, tenant_id):
    return {"id": 42, **data}


class TestCreatePublicationIntegration:
    def test_creation_allowed_with_active_grant(self):
        import app.modules.research.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "research_grants":
                return [_make_grant(AUTHOR_ID, "active")]
            return []  # no existing publications

        with (
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                side_effect=fake_list,
            ),
            patch(
                "app.modules.research.service.create_entity_for_tenant",
                side_effect=_fake_create_entity,
            ),
            patch("app.modules.research.service.log_admin_action"),
        ):
            result = svc_mod.create_research_publication(
                1, _make_publication_payload(), "actor"
            )
        assert result.lead_author_id == AUTHOR_ID

    def test_creation_blocked_without_grant(self):
        import app.modules.research.service as svc_mod

        with (
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                return_value=[],
            ),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_research_publication(
                    1, _make_publication_payload(), "actor"
                )

    def test_creation_blocked_with_only_closed_grant(self):
        import app.modules.research.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "research_grants":
                return [_make_grant(AUTHOR_ID, "closed")]
            return []

        with (
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                side_effect=fake_list,
            ),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_research_publication(
                    1, _make_publication_payload(), "actor"
                )

    def test_creation_blocked_with_only_delayed_grant(self):
        import app.modules.research.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "research_grants":
                return [_make_grant(AUTHOR_ID, "delayed")]
            return []

        with (
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                side_effect=fake_list,
            ),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_research_publication(
                    1, _make_publication_payload(), "actor"
                )

    def test_cap_still_enforced_after_guard_passes(self):
        """After guard passes, existing pub cap must still block over-limit."""
        import app.modules.research.service as svc_mod

        # 3 existing draft publications for the same author = at cap
        existing_pubs = [
            {
                "id": i,
                "publication_code": f"PUB-{i}",
                "lead_author_id": AUTHOR_ID,
                "status": "draft",
                "title": f"Pub {i}",
                "target_venue": "Venue",
                "last_activity_days": 0,
            }
            for i in range(1, 4)  # 3 drafts = cap reached (max=3)
        ]

        def fake_list(entity_type, tenant_id):
            if entity_type == "research_grants":
                return [_make_grant(AUTHOR_ID, "active")]
            return existing_pubs

        with (
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                side_effect=fake_list,
            ),
        ):
            with pytest.raises(ValueError, match="max="):
                svc_mod.create_research_publication(
                    1, _make_publication_payload(status="draft"), "actor"
                )

    def test_planned_grant_satisfies_guard(self):
        import app.modules.research.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "research_grants":
                return [_make_grant(AUTHOR_ID, "planned")]
            return []

        with (
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                side_effect=fake_list,
            ),
            patch(
                "app.modules.research.service.create_entity_for_tenant",
                side_effect=_fake_create_entity,
            ),
            patch("app.modules.research.service.log_admin_action"),
        ):
            result = svc_mod.create_research_publication(
                1, _make_publication_payload(), "actor"
            )
        assert result.id == 42

    def test_submitted_grant_satisfies_guard(self):
        import app.modules.research.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "research_grants":
                return [_make_grant(AUTHOR_ID, "submitted")]
            return []

        with (
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                side_effect=fake_list,
            ),
            patch(
                "app.modules.research.service.create_entity_for_tenant",
                side_effect=_fake_create_entity,
            ),
            patch("app.modules.research.service.log_admin_action"),
        ):
            result = svc_mod.create_research_publication(
                1, _make_publication_payload(), "actor"
            )
        assert result.id == 42

    def test_error_is_domain_validation_error_not_value_error(self):
        """Guard must raise DomainValidationError, not ValueError."""
        import app.modules.research.service as svc_mod

        with (
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                return_value=[],
            ),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_research_publication(
                    1, _make_publication_payload(), "actor"
                )

    def test_tenant_isolation(self):
        """Guard checks grants only for the same tenant_id."""
        import app.modules.research.service as svc_mod

        # tenant 2 has active grant; tenant 1 has none
        def fake_list(entity_type, tenant_id):
            if entity_type == "research_grants" and tenant_id == 2:
                return [_make_grant(AUTHOR_ID, "active")]
            return []

        with (
            patch(
                "app.modules.research.service.list_entities_for_tenant",
                side_effect=fake_list,
            ),
        ):
            # Tenant 1 — no grants → blocked
            with pytest.raises(DomainValidationError):
                svc_mod.create_research_publication(
                    1, _make_publication_payload(), "actor"
                )
