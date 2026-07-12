from fastapi import APIRouter

from app.demo_accounts import demo_accounts_enabled, get_public_demo_accounts
from app.modules.tenants.schemas import LoginDirectoryResponse, LoginDirectoryTenant
from app.modules.tenants.service import list_login_directory_tenants

# Public router for login directory endpoint
# Prefix is /api, routes are under /public/...
router = APIRouter(prefix="/api", tags=["tenants-public"])


@router.get("/public/tenants/login-directory", response_model=LoginDirectoryResponse)
def get_login_directory() -> LoginDirectoryResponse:
    """
    Public login directory endpoint.

    Returns a list of active tenants available for selection during login.
    No authentication required.

    This endpoint is safe for unauthenticated, public access:
    - Only includes active tenants
    - Returns minimal fields (tenant_id, slug, name)
    - No sensitive tenant metadata exposed

    Response:
        tenants: List of LoginDirectoryTenant objects
            - tenant_id: Numeric ID for login form
            - slug: URL-friendly identifier
            - name: Display name for UI dropdown
    """
    tenant_list = list_login_directory_tenants()
    return LoginDirectoryResponse(
        tenants=[
            LoginDirectoryTenant(
                tenant_id=item["tenant_id"],
                slug=item["slug"],
                name=item["name"],
            )
            for item in tenant_list
        ]
    )


@router.get("/public/demo-accounts")
def get_demo_accounts() -> dict[str, object]:
    """Public demo accounts for one-click login.

    Returns ready-made accounts for every platform role, but only when demo
    accounts are explicitly enabled via ``DEMO_ROLE_ACCOUNTS_ENABLED``. When
    disabled (the production default) this returns an empty, disabled payload so
    no credentials are ever exposed.
    """
    if not demo_accounts_enabled():
        return {"enabled": False, "accounts": []}
    return {"enabled": True, "accounts": get_public_demo_accounts()}

