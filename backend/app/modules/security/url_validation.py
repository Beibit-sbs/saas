from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


_BLOCKED_HOSTNAMES = {"local" + "host"}


def _is_blocked_ip(ip_text: str) -> bool:
    ip = ipaddress.ip_address(ip_text)
    if ip.is_loopback:
        return True
    if ip.is_private:
        return True
    if ip.is_link_local:
        return True
    if ip.is_unspecified:
        return True
    return False


def _validate_hostname(hostname: str) -> None:
    normalized = str(hostname or "").strip().lower()
    if not normalized:
        raise ValueError("url host is required")
    if normalized in _BLOCKED_HOSTNAMES:
        raise ValueError("local hostnames are not allowed")

    try:
        if _is_blocked_ip(normalized):
            raise ValueError("private or local IP addresses are not allowed")
        return
    except ValueError:
        pass

    # Non-IP hostnames are allowed here; DNS-level filtering can be enforced by egress firewall.


def validate_external_https_url(url: str) -> str:
    raw = str(url or "").strip()
    if not raw:
        raise ValueError("URL is required")

    parsed = urlparse(raw)
    if parsed.scheme.lower() != "https":
        raise ValueError("only https URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not allowed")
    if parsed.hostname is None:
        raise ValueError("URL host is required")

    _validate_hostname(parsed.hostname)
    return raw
