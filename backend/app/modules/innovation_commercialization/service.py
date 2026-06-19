"""Read-only service responses for innovation / commercialization extension shell."""

from __future__ import annotations

from app.modules.innovation_commercialization.schemas import (
    InnovationCommercializationShellResponse,
    InnovationOpportunity,
    InnovationOpportunityListResponse,
)


def get_extension_shell_service(tenant_id: int) -> InnovationCommercializationShellResponse:
    return InnovationCommercializationShellResponse(
        tenant_id=tenant_id,
        owner_module="innovation_commercialization_extension",
        extension_boundary="A-047 research core is closed and remains authoritative",
        runtime_mode="read_only_extension_shell",
        canonical_base_vertical="research_brain_a047_closed_baselined",
        integration_policy="no_live_provider_execution",
        bridge_modules=[
            "research_science",
            "research",
            "research_grants",
            "research_ethics",
            "ip_management",
        ],
    )


def list_opportunities_service(tenant_id: int) -> InnovationOpportunityListResponse:
    # Seeded extension-only placeholders until dedicated projections are introduced.
    items = [
        InnovationOpportunity(
            opportunity_id="ICX-001",
            title="Patent Licensing Candidate",
            stage="screening",
            readiness="advisory",
            source_module="ip_management",
            notes="Metadata-only opportunity signal; no external outreach triggered.",
        ),
        InnovationOpportunity(
            opportunity_id="ICX-002",
            title="Industry Partnership Candidate",
            stage="review",
            readiness="advisory",
            source_module="research_science",
            notes="Derived from existing research context; no contracting workflow executed.",
        ),
    ]
    return InnovationOpportunityListResponse(tenant_id=tenant_id, items=items)
