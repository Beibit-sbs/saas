"""W69 — thesis: Rejection Risk Alert depth tests."""
from __future__ import annotations


from app.modules.thesis.service import (
    _HIGH_RISK_THESIS_STATUSES,
    _REJECTION_RISK_STATUSES,
    _THESIS_STATUS_MAX_ACTIVE,
    _ensure_rejection_risk_alert,
)
from app.modules.thesis.schemas import ThesisCreateSchema


# ---------------------------------------------------------------------------
# 1. Cap dict structure
# ---------------------------------------------------------------------------

def test_w69_thesis_cap_dict_structure():
    """_THESIS_STATUS_MAX_ACTIVE must be a dict[str, int] with at least 'under_review'."""
    assert isinstance(_THESIS_STATUS_MAX_ACTIVE, dict)
    assert len(_THESIS_STATUS_MAX_ACTIVE) >= 1
    for k, v in _THESIS_STATUS_MAX_ACTIVE.items():
        assert isinstance(k, str)
        assert isinstance(v, int) and v > 0
    assert "under_review" in _THESIS_STATUS_MAX_ACTIVE


# ---------------------------------------------------------------------------
# 2. Rejection risk statuses frozenset
# ---------------------------------------------------------------------------

def test_w69_rejection_risk_statuses_frozenset():
    """_REJECTION_RISK_STATUSES must be a frozenset containing 'rejected'."""
    assert isinstance(_REJECTION_RISK_STATUSES, frozenset)
    assert "rejected" in _REJECTION_RISK_STATUSES
    assert _REJECTION_RISK_STATUSES.isdisjoint(_HIGH_RISK_THESIS_STATUSES), (
        "rejection risk statuses must not overlap with high risk statuses"
    )


# ---------------------------------------------------------------------------
# 3. reviewer_notes in ThesisCreateSchema
# ---------------------------------------------------------------------------

def test_w69_reviewer_notes_field_on_create_schema():
    """ThesisCreateSchema must expose reviewer_notes (str | None, max_length=500)."""
    fields = ThesisCreateSchema.model_fields
    assert "reviewer_notes" in fields, "reviewer_notes field missing from ThesisCreateSchema"
    field = fields["reviewer_notes"]
    assert field.is_required() is False, "reviewer_notes must be optional"


# ---------------------------------------------------------------------------
# 4. Idempotent rejection risk alert — creates once
# ---------------------------------------------------------------------------

def test_w69_rejection_risk_alert_idempotent_creates_once(monkeypatch):
    """_ensure_rejection_risk_alert creates a record the first time."""
    created_records: list[dict] = []
    existing_store: list[dict] = []

    def mock_list(entity_name, tenant_id):
        return list(existing_store)

    def mock_create(entity_name, payload, tenant_id):
        record = {**payload, "id": len(created_records) + 1}
        created_records.append(record)
        existing_store.append(record)
        return record

    monkeypatch.setattr(
        "app.modules.thesis.service.list_entities_for_tenant", mock_list
    )
    monkeypatch.setattr(
        "app.modules.thesis.service.create_entity_for_tenant", mock_create
    )

    thesis_data = {"thesis_code": "TH-2026-001", "student_id": 42, "current_status": "rejected"}
    _ensure_rejection_risk_alert(tenant_id=1, thesis_id=101, thesis_data=thesis_data)

    assert len(created_records) == 1
    record = created_records[0]
    assert record["integration_source"] == "thesis_rejection_queue"
    assert record["source_entity_id"] == "101"
    assert record["alert_status"] == "open"


# ---------------------------------------------------------------------------
# 5. Idempotent rejection risk alert — skips if exists
# ---------------------------------------------------------------------------

def test_w69_rejection_risk_alert_skips_if_exists(monkeypatch):
    """_ensure_rejection_risk_alert is a no-op when a record already exists."""
    created_records: list[dict] = []
    existing_store: list[dict] = [
        {
            "id": 1,
            "integration_source": "thesis_rejection_queue",
            "source_entity_id": "101",
        }
    ]

    def mock_list(entity_name, tenant_id):
        return list(existing_store)

    def mock_create(entity_name, payload, tenant_id):
        created_records.append(payload)
        return payload

    monkeypatch.setattr(
        "app.modules.thesis.service.list_entities_for_tenant", mock_list
    )
    monkeypatch.setattr(
        "app.modules.thesis.service.create_entity_for_tenant", mock_create
    )

    thesis_data = {"thesis_code": "TH-2026-001", "student_id": 42, "current_status": "rejected"}
    _ensure_rejection_risk_alert(tenant_id=1, thesis_id=101, thesis_data=thesis_data)

    assert len(created_records) == 0, "should not create a duplicate record"
