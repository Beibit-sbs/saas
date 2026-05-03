"""Phase LIX — Alumni Donation Portal tests (23 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

MODULE = "app.modules.alumni_donation_portal.service"


def _campaign(
    id: int = 1,
    title: str = "Library Endowment",
    target_amount: float = 10000.0,
    description: str = "Fundraising",
    status: str = "draft",
):
    return {
        "id": id,
        "title": title,
        "target_amount": target_amount,
        "description": description,
        "status": status,
    }


def _donation(
    id: int = 10,
    campaign_id: int = 1,
    donor_id: str = "AL-001",
    amount: float = 1000.0,
    payment_method: str = "card",
    status: str = "pledged",
):
    return {
        "id": id,
        "campaign_id": campaign_id,
        "donor_id": donor_id,
        "amount": amount,
        "payment_method": payment_method,
        "status": status,
    }


def test_create_campaign_success():
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_campaign()) as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.alumni_donation_portal import service

        result = service.create_campaign("Library Endowment", 10000, "Fund", 1)

    assert result.campaign_id == 1
    assert result.status == "draft"
    mock_create.assert_called_once()
    mock_pub.publish.assert_called_once()


def test_create_campaign_invalid_title():
    from app.modules.alumni_donation_portal.service import AlumniDonationError, create_campaign

    with pytest.raises(AlumniDonationError, match="title"):
        create_campaign("", 1000, "x", 1)


def test_create_campaign_invalid_target_amount():
    from app.modules.alumni_donation_portal.service import AlumniDonationError, create_campaign

    with pytest.raises(AlumniDonationError, match="target_amount"):
        create_campaign("Campaign", 0, "x", 1)


def test_create_campaign_event_error_suppressed():
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_campaign()),
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        mock_pub.publish.side_effect = RuntimeError("down")
        from app.modules.alumni_donation_portal import service

        result = service.create_campaign("Library Endowment", 10000, "Fund", 1)

    assert result.campaign_id == 1


def test_activate_campaign_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_campaign(status="draft")]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.alumni_donation_portal import service

        result = service.activate_campaign(1, 1)

    assert result.status == "active"
    mock_update.assert_called_once_with("alumni_donation_campaigns", 1, {"status": "active"}, 1)


def test_activate_campaign_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.alumni_donation_portal.service import AlumniDonationError, activate_campaign

        with pytest.raises(AlumniDonationError, match="not found"):
            activate_campaign(999, 1)


def test_activate_campaign_already_active():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_campaign(status="active")]):
        from app.modules.alumni_donation_portal.service import AlumniDonationError, activate_campaign

        with pytest.raises(AlumniDonationError, match="already active"):
            activate_campaign(1, 1)


def test_activate_campaign_closed_not_allowed():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_campaign(status="closed")]):
        from app.modules.alumni_donation_portal.service import AlumniDonationError, activate_campaign

        with pytest.raises(AlumniDonationError, match="closed"):
            activate_campaign(1, 1)


def test_close_campaign_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_campaign(status="active")]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.alumni_donation_portal import service

        result = service.close_campaign(1, 1)

    assert result.status == "closed"
    mock_update.assert_called_once_with("alumni_donation_campaigns", 1, {"status": "closed"}, 1)
    mock_pub.publish.assert_called_once()


def test_close_campaign_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.alumni_donation_portal.service import AlumniDonationError, close_campaign

        with pytest.raises(AlumniDonationError, match="not found"):
            close_campaign(999, 1)


def test_record_donation_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_campaign(status="active")]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_donation()) as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.alumni_donation_portal import service

        result = service.record_donation(1, "AL-001", 1000.0, "card", 1)

    assert result.donation_id == 10
    assert result.status == "pledged"
    mock_create.assert_called_once()
    mock_pub.publish.assert_called_once()


def test_record_donation_campaign_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.alumni_donation_portal.service import AlumniDonationError, record_donation

        with pytest.raises(AlumniDonationError, match="not found"):
            record_donation(1, "AL-001", 1000.0, "card", 1)


def test_record_donation_campaign_not_active():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_campaign(status="draft")]):
        from app.modules.alumni_donation_portal.service import AlumniDonationError, record_donation

        with pytest.raises(AlumniDonationError, match="active"):
            record_donation(1, "AL-001", 1000.0, "card", 1)


def test_record_donation_invalid_donor_id():
    from app.modules.alumni_donation_portal.service import AlumniDonationError, record_donation

    with pytest.raises(AlumniDonationError, match="donor_id"):
        record_donation(1, "", 1000.0, "card", 1)


def test_record_donation_invalid_amount():
    from app.modules.alumni_donation_portal.service import AlumniDonationError, record_donation

    with pytest.raises(AlumniDonationError, match="amount"):
        record_donation(1, "AL-001", 0.0, "card", 1)


def test_record_donation_invalid_method():
    from app.modules.alumni_donation_portal.service import AlumniDonationError, record_donation

    with pytest.raises(AlumniDonationError, match="payment_method"):
        record_donation(1, "AL-001", 10.0, "crypto", 1)


def test_confirm_donation_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_donation(status="pledged")]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.alumni_donation_portal import service

        result = service.confirm_donation(10, 1)

    assert result.status == "paid"
    mock_update.assert_called_once_with("alumni_donations", 10, {"status": "paid"}, 1)
    mock_pub.publish.assert_called_once()


def test_confirm_donation_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.alumni_donation_portal.service import AlumniDonationError, confirm_donation

        with pytest.raises(AlumniDonationError, match="not found"):
            confirm_donation(10, 1)


def test_confirm_donation_wrong_status():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_donation(status="paid")]):
        from app.modules.alumni_donation_portal.service import AlumniDonationError, confirm_donation

        with pytest.raises(AlumniDonationError, match="pledged"):
            confirm_donation(10, 1)


def test_list_campaigns_filtered_by_status():
    rows = [_campaign(id=1, status="draft"), _campaign(id=2, status="active"), _campaign(id=3, status="active")]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.alumni_donation_portal import service

        result = service.list_campaigns(1, status="active")

    assert len(result) == 2
    assert all(item.status == "active" for item in result)


def test_list_campaigns_invalid_status():
    from app.modules.alumni_donation_portal.service import AlumniDonationError, list_campaigns

    with pytest.raises(AlumniDonationError, match="status"):
        list_campaigns(1, status="planned")


def test_list_donations_filters_by_campaign():
    rows = [_donation(id=1, campaign_id=10), _donation(id=2, campaign_id=11), _donation(id=3, campaign_id=10)]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.alumni_donation_portal import service

        result = service.list_donations(10, 1)

    assert len(result) == 2
    assert all(item.campaign_id == 10 for item in result)


def test_get_campaign_summary_calculates_totals():
    rows = [
        _donation(id=1, campaign_id=1, donor_id="A", amount=100.0, status="pledged"),
        _donation(id=2, campaign_id=1, donor_id="B", amount=300.0, status="paid"),
        _donation(id=3, campaign_id=1, donor_id="A", amount=50.0, status="paid"),
        _donation(id=4, campaign_id=2, donor_id="C", amount=999.0, status="paid"),
    ]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.alumni_donation_portal import service

        summary = service.get_campaign_summary(1, 1)

    assert summary.pledged_amount == 450.0
    assert summary.paid_amount == 350.0
    assert summary.donor_count == 2
