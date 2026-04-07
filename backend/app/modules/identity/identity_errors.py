from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IdentityErrorCode(StrEnum):
    IDENTITY_PROVIDER_NOT_FOUND = "IDENTITY_PROVIDER_NOT_FOUND"
    IDENTITY_PROVIDER_DISABLED = "IDENTITY_PROVIDER_DISABLED"
    IDENTITY_LDAP_CONNECT_FAILED = "IDENTITY_LDAP_CONNECT_FAILED"
    IDENTITY_LDAP_BIND_FAILED = "IDENTITY_LDAP_BIND_FAILED"
    IDENTITY_LDAP_USER_NOT_FOUND = "IDENTITY_LDAP_USER_NOT_FOUND"
    IDENTITY_INVALID_CREDENTIALS = "IDENTITY_INVALID_CREDENTIALS"
    IDENTITY_GROUP_FETCH_FAILED = "IDENTITY_GROUP_FETCH_FAILED"
    IDENTITY_MAPPING_EMPTY = "IDENTITY_MAPPING_EMPTY"
    IDENTITY_MAPPING_INVALID = "IDENTITY_MAPPING_INVALID"
    IDENTITY_PROVIDER_UNAVAILABLE = "IDENTITY_PROVIDER_UNAVAILABLE"
    IDENTITY_RATE_LIMITED = "IDENTITY_RATE_LIMITED"
    IDENTITY_ACCOUNT_LOCKED = "IDENTITY_ACCOUNT_LOCKED"


@dataclass
class IdentityError(Exception):
    code: IdentityErrorCode
    message: str
    details: str = ""
    http_status: int = 400

    def to_response(self) -> dict[str, str]:
        return {"code": self.code.value, "message": self.message}


class IdentityProviderNotFound(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_PROVIDER_NOT_FOUND,
            message="identity provider not found",
            details=details,
            http_status=404,
        )


class IdentityProviderDisabled(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_PROVIDER_DISABLED,
            message="identity provider is disabled",
            details=details,
            http_status=403,
        )


class IdentityLdapConnectFailed(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_LDAP_CONNECT_FAILED,
            message="directory connection failed",
            details=details,
            http_status=503,
        )


class IdentityLdapBindFailed(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_LDAP_BIND_FAILED,
            message="directory bind failed",
            details=details,
            http_status=401,
        )


class IdentityLdapUserNotFound(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_LDAP_USER_NOT_FOUND,
            message="directory user not found",
            details=details,
            http_status=401,
        )


class IdentityInvalidCredentials(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_INVALID_CREDENTIALS,
            message="invalid credentials",
            details=details,
            http_status=401,
        )


class IdentityGroupFetchFailed(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_GROUP_FETCH_FAILED,
            message="failed to fetch external groups",
            details=details,
            http_status=503,
        )


class IdentityMappingEmpty(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_MAPPING_EMPTY,
            message="external groups are not mapped to platform roles",
            details=details,
            http_status=403,
        )


class IdentityMappingInvalid(IdentityError):
    def __init__(self, message: str = "identity mapping is invalid", *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_MAPPING_INVALID,
            message=message,
            details=details,
            http_status=400,
        )


class IdentityProviderUnavailable(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_PROVIDER_UNAVAILABLE,
            message="identity provider is unavailable",
            details=details,
            http_status=503,
        )


class IdentityRateLimited(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_RATE_LIMITED,
            message="too many login attempts",
            details=details,
            http_status=429,
        )


class IdentityAccountLocked(IdentityError):
    def __init__(self, *, details: str = "") -> None:
        super().__init__(
            code=IdentityErrorCode.IDENTITY_ACCOUNT_LOCKED,
            message="account is temporarily locked",
            details=details,
            http_status=423,
        )
