"""Phase LIX — Alumni Donation Portal service."""
from __future__ import annotations

from dataclasses import dataclass

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

CAMPAIGN_STATUSES = {"draft", "active", "closed"}
DONATION_STATUSES = {"pledged", "paid", "refunded", "cancelled"}
PAYMENT_METHODS = {"card", "bank_transfer", "cash", "kaspi"}


class AlumniDonationError(Exception):
    """Raised on invalid Alumni Donation operations."""


@dataclass
class DonationCampaign:
    campaign_id: int
    tenant_id: int
    title: str
    target_amount: float
    status: str


@dataclass
class DonationRecord:
    donation_id: int
    tenant_id: int
    campaign_id: int
    donor_id: str
    amount: float
    payment_method: str
    status: str


@dataclass
class DonationSummary:
    campaign_id: int
    tenant_id: int
    pledged_amount: float
    paid_amount: float
    donor_count: int


def create_campaign(
    title: str,
    target_amount: float,
    description: str,
    tenant_id: int,
) -> DonationCampaign:
    if not title or not title.strip():
        raise AlumniDonationError("title is required")
    if target_amount <= 0:
        raise AlumniDonationError("target_amount must be > 0")

    row = create_entity_for_tenant(
        "alumni_donation_campaigns",
        {
            "title": title.strip(),
            "target_amount": float(target_amount),
            "description": (description or "").strip(),
            "status": "draft",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="alumni_donation.campaign_created",
            payload={"campaign_id": row["id"], "title": row["title"]},
        )
    except Exception:
        pass

    return DonationCampaign(
        campaign_id=row["id"],
        tenant_id=tenant_id,
        title=row["title"],
        target_amount=float(row["target_amount"]),
        status=row["status"],
    )


def activate_campaign(campaign_id: int, tenant_id: int) -> DonationCampaign:
    campaigns = list_entities_for_tenant("alumni_donation_campaigns", tenant_id)
    matched = [c for c in campaigns if c.get("id") == campaign_id]
    if not matched:
        raise AlumniDonationError(f"campaign {campaign_id} not found")

    campaign = matched[0]
    if campaign.get("status") == "active":
        raise AlumniDonationError("campaign is already active")
    if campaign.get("status") == "closed":
        raise AlumniDonationError("closed campaign cannot be activated")

    update_entity_for_tenant(
        "alumni_donation_campaigns",
        campaign_id,
        {"status": "active"},
        tenant_id,
    )

    return DonationCampaign(
        campaign_id=campaign_id,
        tenant_id=tenant_id,
        title=campaign["title"],
        target_amount=float(campaign["target_amount"]),
        status="active",
    )


def close_campaign(campaign_id: int, tenant_id: int) -> DonationCampaign:
    campaigns = list_entities_for_tenant("alumni_donation_campaigns", tenant_id)
    matched = [c for c in campaigns if c.get("id") == campaign_id]
    if not matched:
        raise AlumniDonationError(f"campaign {campaign_id} not found")

    campaign = matched[0]
    if campaign.get("status") == "closed":
        raise AlumniDonationError("campaign is already closed")

    update_entity_for_tenant(
        "alumni_donation_campaigns",
        campaign_id,
        {"status": "closed"},
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="alumni_donation.campaign_closed",
            payload={"campaign_id": campaign_id},
        )
    except Exception:
        pass

    return DonationCampaign(
        campaign_id=campaign_id,
        tenant_id=tenant_id,
        title=campaign["title"],
        target_amount=float(campaign["target_amount"]),
        status="closed",
    )


def record_donation(
    campaign_id: int,
    donor_id: str,
    amount: float,
    payment_method: str,
    tenant_id: int,
) -> DonationRecord:
    if not donor_id or not donor_id.strip():
        raise AlumniDonationError("donor_id is required")
    if amount <= 0:
        raise AlumniDonationError("amount must be > 0")
    if payment_method not in PAYMENT_METHODS:
        raise AlumniDonationError(f"payment_method must be one of {sorted(PAYMENT_METHODS)}")

    campaigns = list_entities_for_tenant("alumni_donation_campaigns", tenant_id)
    matched = [c for c in campaigns if c.get("id") == campaign_id]
    if not matched:
        raise AlumniDonationError(f"campaign {campaign_id} not found")

    campaign = matched[0]
    if campaign.get("status") != "active":
        raise AlumniDonationError("donations are accepted only for active campaigns")

    row = create_entity_for_tenant(
        "alumni_donations",
        {
            "campaign_id": campaign_id,
            "donor_id": donor_id.strip(),
            "amount": float(amount),
            "payment_method": payment_method,
            "status": "pledged",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="alumni_donation.donation_recorded",
            payload={
                "donation_id": row["id"],
                "campaign_id": campaign_id,
                "amount": float(amount),
            },
        )
    except Exception:
        pass

    return DonationRecord(
        donation_id=row["id"],
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        donor_id=row["donor_id"],
        amount=float(row["amount"]),
        payment_method=row["payment_method"],
        status=row["status"],
    )


def confirm_donation(donation_id: int, tenant_id: int) -> DonationRecord:
    donations = list_entities_for_tenant("alumni_donations", tenant_id)
    matched = [d for d in donations if d.get("id") == donation_id]
    if not matched:
        raise AlumniDonationError(f"donation {donation_id} not found")

    donation = matched[0]
    if donation.get("status") != "pledged":
        raise AlumniDonationError("only pledged donations can be confirmed")

    update_entity_for_tenant(
        "alumni_donations",
        donation_id,
        {"status": "paid"},
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="alumni_donation.donation_paid",
            payload={"donation_id": donation_id, "campaign_id": donation["campaign_id"]},
        )
    except Exception:
        pass

    return DonationRecord(
        donation_id=donation_id,
        tenant_id=tenant_id,
        campaign_id=donation["campaign_id"],
        donor_id=donation["donor_id"],
        amount=float(donation["amount"]),
        payment_method=donation["payment_method"],
        status="paid",
    )


def list_campaigns(tenant_id: int, status: str | None = None) -> list[DonationCampaign]:
    if status is not None and status not in CAMPAIGN_STATUSES:
        raise AlumniDonationError(f"status must be one of {sorted(CAMPAIGN_STATUSES)}")

    campaigns = list_entities_for_tenant("alumni_donation_campaigns", tenant_id)
    filtered = [c for c in campaigns if status is None or c.get("status") == status]

    return [
        DonationCampaign(
            campaign_id=row["id"],
            tenant_id=tenant_id,
            title=row["title"],
            target_amount=float(row["target_amount"]),
            status=row["status"],
        )
        for row in filtered
    ]


def list_donations(campaign_id: int, tenant_id: int) -> list[DonationRecord]:
    donations = list_entities_for_tenant("alumni_donations", tenant_id)
    filtered = [d for d in donations if d.get("campaign_id") == campaign_id]

    return [
        DonationRecord(
            donation_id=row["id"],
            tenant_id=tenant_id,
            campaign_id=row["campaign_id"],
            donor_id=row["donor_id"],
            amount=float(row["amount"]),
            payment_method=row["payment_method"],
            status=row["status"],
        )
        for row in filtered
    ]


def get_campaign_summary(campaign_id: int, tenant_id: int) -> DonationSummary:
    donations = list_entities_for_tenant("alumni_donations", tenant_id)
    rows = [d for d in donations if d.get("campaign_id") == campaign_id]

    pledged_amount = sum(float(d.get("amount") or 0.0) for d in rows)
    paid_amount = sum(float(d.get("amount") or 0.0) for d in rows if d.get("status") == "paid")
    donor_count = len({str(d.get("donor_id")) for d in rows})

    return DonationSummary(
        campaign_id=campaign_id,
        tenant_id=tenant_id,
        pledged_amount=pledged_amount,
        paid_amount=paid_amount,
        donor_count=donor_count,
    )
