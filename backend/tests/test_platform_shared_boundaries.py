from app.modules.platform_shared.boundaries import SHARED_SERVICE_BOUNDARIES


def test_platform_shared_boundaries_cover_core_services() -> None:
    keys = {item.key for item in SHARED_SERVICE_BOUNDARIES}
    assert keys == {
        "events",
        "notifications",
        "files",
        "search",
        "workflow",
        "webhooks",
        "entitlements",
    }
