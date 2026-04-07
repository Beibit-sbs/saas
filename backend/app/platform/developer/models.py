from __future__ import annotations

from enum import StrEnum


class DeveloperAppStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class DeveloperInstallationStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"