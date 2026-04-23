from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TenantPolicyProfile:
    tenant_id: int
    autonomy_level: int = 2
    require_approval_for_critical: bool = True
    default_approval_role: str = "dean_office"
    enable_ai_reasoning: bool = False


class TenantPolicyResolver:
    """In-memory tenant policy resolver for Brain Core v1."""

    def __init__(self) -> None:
        self._profiles: dict[int, TenantPolicyProfile] = {}

    def get_profile(self, tenant_id: int) -> TenantPolicyProfile:
        if tenant_id not in self._profiles:
            self._profiles[tenant_id] = TenantPolicyProfile(tenant_id=tenant_id)
        return self._profiles[tenant_id]

    def set_profile(self, profile: TenantPolicyProfile) -> None:
        self._profiles[profile.tenant_id] = profile

    def set_profile_values(
        self,
        *,
        tenant_id: int,
        autonomy_level: int,
        require_approval_for_critical: bool,
        default_approval_role: str,
        enable_ai_reasoning: bool,
    ) -> TenantPolicyProfile:
        normalized_autonomy_level = max(0, min(4, int(autonomy_level)))
        profile = TenantPolicyProfile(
            tenant_id=int(tenant_id),
            autonomy_level=normalized_autonomy_level,
            require_approval_for_critical=bool(require_approval_for_critical),
            default_approval_role=str(default_approval_role),
            enable_ai_reasoning=bool(enable_ai_reasoning),
        )
        self._profiles[profile.tenant_id] = profile
        return profile

    def profile_dict(self, tenant_id: int) -> dict:
        return asdict(self.get_profile(tenant_id))
