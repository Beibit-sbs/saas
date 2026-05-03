"""Phase XLIX: Student Portal (Self-Service) Tests (15 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.modules.student_portal.service as svc

TENANT = "uni-xlix"
BAD_TENANT = "bad-tenant"


def _make_request(rid="r-1", student_id="stu-1", request_type="CERTIFICATE", status="SUBMITTED"):
    return {
        "id": rid,
        "student_id": student_id,
        "request_type": request_type,
        "details": "",
        "status": status,
        "tenant_id": TENANT,
    }


# ─── 1. Constants ─────────────────────────────────────────────────────────────

class TestConstants:
    def test_request_types_complete(self):
        assert {"CERTIFICATE", "TRANSCRIPT", "ID_CARD_REPLACEMENT", "GRADE_INQUIRY", "ENROLLMENT_CONFIRMATION"} == svc.REQUEST_TYPES

    def test_request_states_complete(self):
        assert {"SUBMITTED", "PROCESSING", "READY", "DELIVERED"} == svc.REQUEST_STATES


# ─── 2. submit_request ────────────────────────────────────────────────────────

class TestSubmitRequest:
    def test_submit_request_fires_event(self):
        publisher = MagicMock()
        with patch("app.modules.student_portal.service.create_entity_for_tenant", return_value=_make_request()):
            with patch("app.modules.student_portal.service.EventPublisher", publisher):
                req = svc.submit_request(TENANT, student_id="stu-1", request_type="CERTIFICATE")
        assert req["status"] == "SUBMITTED"
        publisher.publish.assert_called_once()
        assert publisher.publish.call_args[0][0] == "request.submitted"

    def test_submit_request_invalid_type(self):
        with pytest.raises(ValueError, match="request_type"):
            svc.submit_request(TENANT, student_id="stu-1", request_type="UNKNOWN")

    def test_submit_request_missing_student(self):
        with pytest.raises(ValueError, match="student_id"):
            svc.submit_request(TENANT, student_id="", request_type="TRANSCRIPT")

    def test_submit_request_bad_tenant(self):
        with pytest.raises(ValueError, match="tenant"):
            svc.submit_request(BAD_TENANT, student_id="stu-1", request_type="CERTIFICATE")


# ─── 3. FSM transitions ───────────────────────────────────────────────────────

class TestRequestFSM:
    def test_start_processing_success(self):
        req = _make_request()
        with patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=[req]):
            result = svc.start_processing(TENANT, request_id="r-1")
        assert result["status"] == "PROCESSING"

    def test_start_processing_wrong_status(self):
        req = _make_request(status="READY")
        with patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=[req]):
            with pytest.raises(ValueError, match="transition"):
                svc.start_processing(TENANT, request_id="r-1")

    def test_mark_ready_fires_event(self):
        req = _make_request(status="PROCESSING")
        publisher = MagicMock()
        with patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=[req]):
            with patch("app.modules.student_portal.service.EventPublisher", publisher):
                result = svc.mark_ready(TENANT, request_id="r-1")
        assert result["status"] == "READY"
        publisher.publish.assert_called_once()
        assert publisher.publish.call_args[0][0] == "request.ready"

    def test_mark_ready_wrong_status(self):
        req = _make_request(status="SUBMITTED")
        with patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=[req]):
            with pytest.raises(ValueError, match="transition"):
                svc.mark_ready(TENANT, request_id="r-1")

    def test_deliver_request_success(self):
        req = _make_request(status="READY")
        with patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=[req]):
            result = svc.deliver_request(TENANT, request_id="r-1")
        assert result["status"] == "DELIVERED"

    def test_deliver_request_wrong_status(self):
        req = _make_request(status="SUBMITTED")
        with patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=[req]):
            with pytest.raises(ValueError, match="transition"):
                svc.deliver_request(TENANT, request_id="r-1")

    def test_deliver_request_not_found(self):
        with patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=[]):
            with pytest.raises(ValueError, match="not found"):
                svc.deliver_request(TENANT, request_id="r-999")


# ─── 4. list_requests ─────────────────────────────────────────────────────────

class TestListRequests:
    def test_list_requests_filter_by_student(self):
        reqs = [
            _make_request("r-1", "stu-1"),
            _make_request("r-2", "stu-2"),
            _make_request("r-3", "stu-1"),
        ]
        with patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=reqs):
            result = svc.list_requests(TENANT, student_id="stu-1")
        assert len(result) == 2
        assert all(r["student_id"] == "stu-1" for r in result)

    def test_list_requests_filter_by_type(self):
        reqs = [
            _make_request("r-1", request_type="CERTIFICATE"),
            _make_request("r-2", request_type="TRANSCRIPT"),
        ]
        with patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=reqs):
            result = svc.list_requests(TENANT, request_type="CERTIFICATE")
        assert len(result) == 1
        assert result[0]["request_type"] == "CERTIFICATE"


# ─── 5. Dashboard ─────────────────────────────────────────────────────────────

class TestDashboard:
    def test_get_dashboard_counts_active_requests(self):
        reqs = [
            _make_request("r-1", "stu-1", status="SUBMITTED"),
            _make_request("r-2", "stu-1", status="PROCESSING"),
            _make_request("r-3", "stu-1", status="DELIVERED"),
        ]
        with patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=reqs):
            dash = svc.get_student_dashboard(TENANT, student_id="stu-1")
        assert dash["active_requests"] == 2  # DELIVERED excluded

    def test_get_dashboard_missing_student(self):
        with pytest.raises(ValueError, match="student_id"):
            svc.get_student_dashboard(TENANT, student_id="")
