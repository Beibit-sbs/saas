from __future__ import annotations

from enum import StrEnum


class InstitutionType(StrEnum):
    UNIVERSITY = "university"
    COLLEGE = "college"
    INSTITUTE = "institute"


class InstitutionStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class FederationMemberRole(StrEnum):
    INSTITUTION_ADMIN = "institution_admin"
    FEDERATION_ADMIN = "federation_admin"
    PLATFORM_ADMIN = "platform_admin"
