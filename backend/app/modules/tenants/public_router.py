from fastapi import APIRouter

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
