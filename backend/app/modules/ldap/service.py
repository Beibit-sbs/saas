import json
import os
from typing import Any

from ldap3 import ALL, Connection, Server
from ldap3.core.exceptions import LDAPException
from ldap3.utils.conv import escape_filter_chars

from app.modules.integrations.service import get_ldap_runtime_config


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _cfg(name: str, default: str = "") -> str:
    runtime = get_ldap_runtime_config()
    return str(runtime.get(name, default)).strip()


def _is_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _timeout() -> int:
    raw = _cfg("timeout_seconds", "5")
    try:
        return max(1, int(raw))
    except ValueError:
        return 5


def _server() -> Server:
    server_uri = _cfg("server_uri")
    if not server_uri:
        raise ValueError("LDAP_SERVER_URI is not configured")
    return Server(server_uri, get_info=ALL, connect_timeout=_timeout())


def _service_bind_credentials() -> tuple[str, str]:
    bind_dn = _cfg("bind_dn")
    bind_password = _cfg("bind_password")
    if not bind_dn or not bind_password:
        raise ValueError("LDAP bind account is not fully configured")
    return bind_dn, bind_password


def _base_dn() -> str:
    value = _cfg("base_dn")
    if not value:
        raise ValueError("LDAP_BASE_DN is not configured")
    return value


def _user_filter(username: str) -> str:
    template = _cfg("user_filter", "(sAMAccountName={username})")
    return template.format(username=escape_filter_chars(username))


def _display_name_attribute() -> str:
    return _cfg("display_name_attribute", "displayName")


def _login_attribute() -> str:
    return _cfg("login_attribute", "sAMAccountName")


def _group_attribute() -> str:
    return _cfg("group_attribute", "memberOf")


def _default_role() -> str:
    return _cfg("default_role", "student")


def _group_role_map() -> dict[str, str]:
    raw = _cfg("group_role_map_json", "{}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("LDAP_GROUP_ROLE_MAP_JSON must be valid JSON") from exc

    if not isinstance(value, dict):
        raise ValueError("LDAP_GROUP_ROLE_MAP_JSON must be an object")

    return {str(k).strip().lower(): str(v).strip() for k, v in value.items() if str(k).strip() and str(v).strip()}


def ldap_status() -> dict[str, Any]:
    enabled = _is_enabled(_cfg("enabled", "false"))
    bind_dn = _cfg("bind_dn")
    base_dn = _cfg("base_dn")
    server_uri = _cfg("server_uri")
    role_map = _group_role_map()
    configured = bool(server_uri and bind_dn and _cfg("bind_password") and base_dn)
    return {
        "enabled": enabled,
        "configured": configured,
        "server_uri": server_uri,
        "bind_dn": bind_dn,
        "base_dn": base_dn,
        "user_filter": _cfg("user_filter", "(sAMAccountName={username})"),
        "display_name_attribute": _display_name_attribute(),
        "login_attribute": _login_attribute(),
        "group_attribute": _group_attribute(),
        "group_role_map_count": len(role_map),
        "default_role": _default_role(),
        "timeout_seconds": _timeout(),
    }


def test_ldap_connection(username: str | None = None, password: str | None = None) -> dict[str, Any]:
    status = ldap_status()
    if not status["enabled"]:
        raise ValueError("LDAP/AD auth is disabled")
    if not status["configured"]:
        raise ValueError("LDAP/AD config is incomplete")

    bind_dn, bind_password = _service_bind_credentials()
    server = _server()

    try:
        with Connection(server, user=bind_dn, password=bind_password, auto_bind=True) as conn:
            result: dict[str, Any] = {
                "status": "service_bind_ok",
                "server_uri": status["server_uri"],
                "base_dn": status["base_dn"],
            }

            if username and password:
                user_info = _search_and_authenticate_user(conn, username, password)
                result["user_check"] = {
                    "status": "user_bind_ok",
                    "user_id": user_info["user_id"],
                    "display_name": user_info["display_name"],
                    "roles": user_info["roles"],
                }

            return result
    except LDAPException as exc:
        raise ValueError(f"LDAP/AD connection failed: {exc}") from exc


def _extract_groups(entry: Any) -> list[str]:
    attribute_name = _group_attribute()
    if attribute_name not in entry:
        return []

    values = entry[attribute_name].value
    if values is None:
        return []
    if isinstance(values, str):
        return [values]
    return [str(item) for item in values]


def _map_groups_to_roles(groups: list[str]) -> list[str]:
    role_map = _group_role_map()
    roles = []
    for group in groups:
      normalized = group.strip().lower()
      if normalized in role_map:
          roles.append(role_map[normalized])

    if not roles:
        roles.append(_default_role())

    return sorted(set(roles))


def _search_and_authenticate_user(service_connection: Connection, username: str, password: str) -> dict[str, Any]:
    base_dn = _base_dn()
    requested_attributes = [_display_name_attribute(), _login_attribute(), _group_attribute()]
    search_ok = service_connection.search(
        search_base=base_dn,
        search_filter=_user_filter(username),
        attributes=requested_attributes,
    )
    if not search_ok or not service_connection.entries:
        raise ValueError("LDAP/AD user not found")

    entry = service_connection.entries[0]
    user_dn = entry.entry_dn
    try:
        with Connection(_server(), user=user_dn, password=password, auto_bind=True):
            pass
    except LDAPException as exc:
        raise ValueError("LDAP/AD credentials rejected") from exc

    display_name_attr = _display_name_attribute()
    login_attr = _login_attribute()

    display_name = str(entry[display_name_attr].value) if display_name_attr in entry and entry[display_name_attr].value else username
    login_value = str(entry[login_attr].value) if login_attr in entry and entry[login_attr].value else username
    groups = _extract_groups(entry)

    return {
        "user_id": f"ad.{login_value}",
        "login": login_value,
        "display_name": display_name,
        "roles": _map_groups_to_roles(groups),
        "groups": groups,
        "auth_source": "ldap",
        "sync_with_ad": True,
        "language": "ru",
    }


def authenticate_ldap_user(username: str, password: str) -> dict[str, Any]:
    status = ldap_status()
    if not status["enabled"]:
        raise ValueError("LDAP/AD auth is disabled")
    if not status["configured"]:
        raise ValueError("LDAP/AD config is incomplete")

    bind_dn, bind_password = _service_bind_credentials()
    try:
        with Connection(_server(), user=bind_dn, password=bind_password, auto_bind=True) as conn:
            return _search_and_authenticate_user(conn, username, password)
    except LDAPException as exc:
        raise ValueError(f"LDAP/AD bind failed: {exc}") from exc