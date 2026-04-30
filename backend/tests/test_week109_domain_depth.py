"""W109 — Alumni: Engagement Type Cap Guard (cross-entity: alumni_records cap per student per type).

Business invariant: A student can only have a limited number of active alumni records
per engagement type, preventing phantom engagement inflation and engagement KPI gaming.

Cap limits:
  - mentoring: max 1
  - event: max 3
  - donation: max 5
  - referral: max 2

Bad outcomes if guard is missing:
  - Single student creates 50+ engagement records (phantom inflation)
  - Engagement analytics corrupted (inflated counts, false trends)
  - Brain Core decision-making on engagement metrics unreliable
  - Alumni program ROI metrics gamed/distorted
  - Cascade failures in alumni engagement analytics

Guard location: alumni/service.py :: create_alumni_record() → _check_engagement_cap()
                BEFORE create_entity_for_tenant("alumni_records", ...)
"""
from __future__ import annotations

import importlib
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Module under test
# ---------------------------------------------------------------------------
SERVICE_MODULE = "app.modules.alumni.service"


def _svc():
    """Return freshly imported service module."""
    return importlib.import_module(SERVICE_MODULE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_alumni_record(
    student_id: int,
    engagement_type: str,
    status: str,
    **extra,
) -> dict:
    return {
        "id": 1,
        "student_id": student_id,
        "engagement_type": engagement_type,
        "status": status,
        "graduation_year": 2024,
        "employer": "Acme",
        "contact_email": "alumni@example.com",
        "notes": "test",
        **extra,
    }


TENANT = 42
STUDENT_ID = 510


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

class TestW109Constants:
    def test_engagement_type_max_active_constants_exist(self):
        svc = _svc()
        assert hasattr(svc, "_ENGAGEMENT_TYPE_MAX_ACTIVE")

    def test_engagement_type_max_active_is_dict(self):
        svc = _svc()
        assert isinstance(svc._ENGAGEMENT_TYPE_MAX_ACTIVE, dict)

    def test_mentoring_max_is_one(self):
        svc = _svc()
        assert svc._ENGAGEMENT_TYPE_MAX_ACTIVE.get("mentoring") == 1

    def test_event_max_is_three(self):
        svc = _svc()
        assert svc._ENGAGEMENT_TYPE_MAX_ACTIVE.get("event") == 3

    def test_donation_max_is_five(self):
        svc = _svc()
        assert svc._ENGAGEMENT_TYPE_MAX_ACTIVE.get("donation") == 5

    def test_referral_max_is_two(self):
        svc = _svc()
        assert svc._ENGAGEMENT_TYPE_MAX_ACTIVE.get("referral") == 2

    def test_active_alumni_statuses_constants_exist(self):
        svc = _svc()
        assert hasattr(svc, "_ACTIVE_ALUMNI_STATUSES")

    def test_active_alumni_statuses_is_frozenset(self):
        svc = _svc()
        assert isinstance(svc._ACTIVE_ALUMNI_STATUSES, frozenset)

    def test_active_alumni_statuses_contains_active(self):
        svc = _svc()
        assert "active" in svc._ACTIVE_ALUMNI_STATUSES

    def test_active_alumni_statuses_contains_engaged(self):
        svc = _svc()
        assert "engaged" in svc._ACTIVE_ALUMNI_STATUSES

    def test_active_alumni_statuses_contains_donor(self):
        svc = _svc()
        assert "donor" in svc._ACTIVE_ALUMNI_STATUSES


# ---------------------------------------------------------------------------
# 2. Guard unit tests (_check_engagement_cap)
# ---------------------------------------------------------------------------

class TestCheckEngagementCap:
    def _call(self, records: list[dict], engagement_type: str = "event"):
        from app.modules.alumni.service import _check_engagement_cap
        from app.core.module_helpers.service_validation import DomainValidationError as DVE

        with patch(
            "app.modules.alumni.service.list_entities_for_tenant",
            return_value=records,
        ):
            try:
                _check_engagement_cap(
                    tenant_id=TENANT,
                    student_id=STUDENT_ID,
                    engagement_type=engagement_type,
                )
                return None  # success
            except DVE as exc:
                return str(exc)

    def test_no_existing_records_allowed(self):
        """Empty alumni registry → guard passes."""
        result = self._call(records=[])
        assert result is None

    def test_one_existing_active_event_allowed_when_max_3(self):
        """1 active event < 3 max → allowed."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
            )
        ]
        result = self._call(records, engagement_type="event")
        assert result is None

    def test_two_existing_active_events_allowed_when_max_3(self):
        """2 active events < 3 max → allowed."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=1,
            ),
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=2,
            ),
        ]
        result = self._call(records, engagement_type="event")
        assert result is None

    def test_three_existing_active_events_blocked_when_max_3(self):
        """3 active events = 3 max → block."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=1,
            ),
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=2,
            ),
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=3,
            ),
        ]
        result = self._call(records, engagement_type="event")
        assert result is not None
        assert "student_id=510" in result
        assert "already has 3 active 'event'" in result
        assert "max=3" in result

    def test_mentoring_max_1_blocked_at_2(self):
        """1 active mentoring = 1 max → block on second."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="mentoring",
                status="active",
            )
        ]
        result = self._call(records, engagement_type="mentoring")
        assert result is not None
        assert "already has 1 active 'mentoring'" in result
        assert "max=1" in result

    def test_donation_max_5_allowed_at_4(self):
        """4 active donations < 5 max → allowed (5th creation succeeds)."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="donation",
                status="active",
                id=i,
            )
            for i in range(1, 5)  # 4 existing < 5 max → allowed
        ]
        result = self._call(records, engagement_type="donation")
        assert result is None

    def test_donation_max_5_blocked_at_6(self):
        """6 active donations > 5 max → block."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="donation",
                status="active",
                id=i,
            )
            for i in range(1, 7)
        ]
        result = self._call(records, engagement_type="donation")
        assert result is not None
        assert "already has 6 active 'donation'" in result

    def test_referral_max_2_allowed_at_1(self):
        """1 active referral < 2 max → allowed (2nd creation succeeds)."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="referral",
                status="active",
                id=1,
            ),
        ]
        result = self._call(records, engagement_type="referral")
        assert result is None

    def test_referral_max_2_blocked_at_3(self):
        """3 active referrals > 2 max → block."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="referral",
                status="active",
                id=i,
            )
            for i in range(1, 4)
        ]
        result = self._call(records, engagement_type="referral")
        assert result is not None
        assert "already has 3 active 'referral'" in result

    def test_inactive_records_not_counted_toward_cap(self):
        """Inactive/donor records not counted → only active/engaged/donor count."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=1,
            ),
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="inactive",  # not counted
                id=2,
            ),
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=3,
            ),
        ]
        result = self._call(records, engagement_type="event")
        # 2 active < 3 max → allowed
        assert result is None

    def test_engaged_status_counts_toward_cap(self):
        """engaged status counts toward cap — 1 active + 1 engaged = 2 < 3 → allowed."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=1,
            ),
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="engaged",  # counts toward cap
                id=2,
            ),
        ]
        result = self._call(records, engagement_type="event")
        # 2 active/engaged < 3 max → allowed
        assert result is None

    def test_donor_status_counts_toward_cap(self):
        """donor status counts toward cap — 1 active + 1 donor = 2 < 3 → allowed."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=1,
            ),
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="donor",  # counts toward cap
                id=2,
            ),
        ]
        result = self._call(records, engagement_type="event")
        # 2 active/donor < 3 max → allowed
        assert result is None

    def test_different_student_records_not_counted(self):
        """Other student's records not counted toward this student's cap."""
        records = [
            _make_alumni_record(
                student_id=999,  # different student
                engagement_type="event",
                status="active",
                id=1,
            ),
            _make_alumni_record(
                student_id=999,
                engagement_type="event",
                status="active",
                id=2,
            ),
            _make_alumni_record(
                student_id=999,
                engagement_type="event",
                status="active",
                id=3,
            ),
        ]
        result = self._call(records, engagement_type="event")
        # STUDENT_ID has 0 active → allowed
        assert result is None

    def test_different_engagement_type_not_counted(self):
        """Other engagement types not counted toward this type's cap."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="mentoring",  # different type
                status="active",
                id=1,
            ),
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="mentoring",  # different type
                status="active",
                id=2,
            ),
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="mentoring",  # different type
                status="active",
                id=3,
            ),
        ]
        result = self._call(records, engagement_type="event")
        # STUDENT_ID has 0 'event' records → allowed
        assert result is None

    def test_engagement_type_case_insensitive(self):
        """engagement_type match is case-insensitive."""
        records = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="EVENT",  # uppercase
                status="active",
                id=1,
            ),
        ]
        result = self._call(records, engagement_type="event")  # lowercase
        assert result is None

    def test_lookup_failure_raises_domain_validation_error(self):
        """If alumni lookup fails, guard raises DomainValidationError (fail-closed)."""
        from app.core.module_helpers.service_validation import DomainValidationError as DVE

        with patch(
            "app.modules.alumni.service.list_entities_for_tenant",
            side_effect=Exception("DB connection lost"),
        ):
            with pytest.raises(DVE) as exc_info:
                from app.modules.alumni.service import _check_engagement_cap

                _check_engagement_cap(
                    tenant_id=TENANT,
                    student_id=STUDENT_ID,
                    engagement_type="event",
                )
        assert "alumni lookup failed" in str(exc_info.value)
        assert "Cannot verify engagement cap" in str(exc_info.value) or "cannot verify engagement cap" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# 3. Integration tests with create_alumni_record
# ---------------------------------------------------------------------------

class TestCreateAlumniRecordEngagementCap:
    def _create(self, existing_records: list[dict], engagement_type: str = "event"):
        from app.modules.alumni.service import create_alumni_record
        from app.modules.alumni.schemas import AlumniRecordCreateSchema
        from app.core.module_helpers.service_validation import DomainValidationError as DVE

        request = AlumniRecordCreateSchema(
            student_id=STUDENT_ID,
            graduation_year=2024,
            engagement_type=engagement_type,
            employer="Acme",
            contact_email="test@example.com",
            notes="test",
        )

        with patch(
            "app.modules.alumni.service.list_entities_for_tenant",
            side_effect=lambda entity, tenant_id: {
                "students": [
                    {
                        "id": STUDENT_ID,
                        "status": "graduated",
                    }
                ],
                "alumni_records": existing_records,
            }.get(entity, []),
        ), patch(
            "app.modules.alumni.service.create_entity_for_tenant",
            return_value={
                "id": 1,
                "student_id": STUDENT_ID,
                "engagement_type": engagement_type,
                "status": "active",
                "graduation_year": 2024,
                "employer": "Acme",
                "contact_email": "test@example.com",
                "notes": "test",
            },
        ):
            try:
                result = create_alumni_record(
                    tenant_id=TENANT,
                    request=request,
                    actor="test_user",
                )
                return None, result  # success
            except (ValueError, DVE) as exc:
                return str(exc), None  # error

    def test_create_first_event_succeeds(self):
        """Create first event engagement → success."""
        error, result = self._create(existing_records=[])
        assert error is None
        assert result is not None

    def test_create_when_at_cap_fails(self):
        """Create when already at cap → blocked."""
        existing = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=i,
            )
            for i in range(1, 4)  # 3 records = max for event
        ]
        error, result = self._create(existing_records=existing)
        assert error is not None
        assert "already has 3 active 'event'" in error
        assert result is None

    def test_create_below_cap_succeeds(self):
        """Create when below cap → success."""
        existing = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=1,
            )
        ]
        error, result = self._create(existing_records=existing)
        assert error is None
        assert result is not None

    def test_create_mentoring_one_then_second_fails(self):
        """Mentoring has max 1 → second fails."""
        existing = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="mentoring",
                status="active",
                id=1,
            )
        ]
        error, result = self._create(existing_records=existing, engagement_type="mentoring")
        assert error is not None
        assert "already has 1 active 'mentoring'" in error

    def test_create_with_inactive_previous_succeeds(self):
        """Previous inactive engagement doesn't block → success."""
        existing = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="inactive",
            )
        ]
        error, result = self._create(existing_records=existing)
        assert error is None
        assert result is not None

    def test_create_donation_at_cap_fails(self):
        """Donation cap is 5 → 6th fails."""
        existing = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="donation",
                status="active",
                id=i,
            )
            for i in range(1, 6)  # 5 = max
        ]
        error, result = self._create(existing_records=existing, engagement_type="donation")
        assert error is not None
        assert "already has 5 active 'donation'" in error

    def test_create_referral_below_cap_succeeds(self):
        """Referral has max 2 → 1 existing → success."""
        existing = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="referral",
                status="active",
            )
        ]
        error, result = self._create(existing_records=existing, engagement_type="referral")
        assert error is None
        assert result is not None

    def test_create_persists_before_audit(self):
        """Guard fires BEFORE persist."""
        from app.modules.alumni.service import create_alumni_record
        from app.modules.alumni.schemas import AlumniRecordCreateSchema

        request = AlumniRecordCreateSchema(
            student_id=STUDENT_ID,
            graduation_year=2024,
            engagement_type="event",
            employer="Acme",
            contact_email="test@example.com",
            notes="test",
        )

        # Create scenario: 3 existing active events (at cap)
        existing = [
            _make_alumni_record(
                student_id=STUDENT_ID,
                engagement_type="event",
                status="active",
                id=i,
            )
            for i in range(1, 4)
        ]

        persist_called = False

        def mock_persist(*args, **kwargs):
            nonlocal persist_called
            persist_called = True
            return {"id": 99}

        with patch(
            "app.modules.alumni.service.list_entities_for_tenant",
            side_effect=lambda entity, tenant_id: {
                "students": [{"id": STUDENT_ID, "status": "graduated"}],
                "alumni_records": existing,
            }.get(entity, []),
        ), patch(
            "app.modules.alumni.service.create_entity_for_tenant",
            side_effect=mock_persist,
        ):
            from app.core.module_helpers.service_validation import DomainValidationError as DVE

            with pytest.raises(DVE):
                create_alumni_record(
                    tenant_id=TENANT,
                    request=request,
                    actor="test_user",
                )
        # Persist was never called because guard blocked it
        assert not persist_called
