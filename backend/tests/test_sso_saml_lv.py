"""Phase LV — SSO SAML 2.0 tests (22 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

MODULE = "app.modules.sso_saml.service"


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_idp(id_=1, entity_id="https://idp.example.com", sso_url="https://idp.example.com/sso",
              status="active"):
    return {
        "id": id_,
        "entity_id": entity_id,
        "sso_url": sso_url,
        "slo_url": "",
        "certificate": "CERT",
        "binding": "redirect",
        "status": status,
    }


def _make_session(id_=10, idp_id=1, user_id=None, status="initiated",
                  relay_state="/dashboard", request_id="abc123", name_id=""):
    return {
        "id": id_,
        "idp_id": idp_id,
        "user_id": user_id,
        "status": status,
        "relay_state": relay_state,
        "request_id": request_id,
        "name_id": name_id,
    }


# ---------------------------------------------------------------------------
# 1. register_idp — happy path
# ---------------------------------------------------------------------------


def test_register_idp_creates_entity():
    with (
        patch(f"{MODULE}.create_entity_for_tenant") as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        mock_create.return_value = {"id": 1}
        from app.modules.sso_saml.service import register_idp

        result = register_idp(
            entity_id="https://idp.example.com",
            sso_url="https://idp.example.com/sso",
            slo_url="https://idp.example.com/slo",
            certificate="CERT_DATA",
            binding="redirect",
            tenant_id=42,
        )

        assert result.idp_id == 1
        assert result.status == "active"
        mock_create.assert_called_once()
        args = mock_create.call_args[0]
        assert args[0] == "saml_identity_providers"
        assert args[2] == 42
        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "sso.idp_registered"


# ---------------------------------------------------------------------------
# 2. register_idp — post binding
# ---------------------------------------------------------------------------


def test_register_idp_post_binding():
    with (
        patch(f"{MODULE}.create_entity_for_tenant") as mock_create,
        patch(f"{MODULE}.EventPublisher"),
    ):
        mock_create.return_value = {"id": 2}
        from app.modules.sso_saml.service import register_idp

        result = register_idp(
            entity_id="https://idp2.example.com",
            sso_url="https://idp2.example.com/sso",
            slo_url="",
            certificate="CERT2",
            binding="post",
            tenant_id=1,
        )
        assert result.idp_id == 2


# ---------------------------------------------------------------------------
# 3. register_idp — missing entity_id
# ---------------------------------------------------------------------------


def test_register_idp_missing_entity_id():
    from app.modules.sso_saml.service import SSOError, register_idp

    with pytest.raises(SSOError, match="entity_id"):
        register_idp(entity_id="", sso_url="https://x.com", slo_url="",
                     certificate="C", binding="redirect", tenant_id=1)


# ---------------------------------------------------------------------------
# 4. register_idp — invalid binding
# ---------------------------------------------------------------------------


def test_register_idp_invalid_binding():
    from app.modules.sso_saml.service import SSOError, register_idp

    with pytest.raises(SSOError, match="invalid binding"):
        register_idp(entity_id="https://x.com", sso_url="https://x.com", slo_url="",
                     certificate="C", binding="artifact", tenant_id=1)


# ---------------------------------------------------------------------------
# 5. register_idp — missing certificate
# ---------------------------------------------------------------------------


def test_register_idp_missing_certificate():
    from app.modules.sso_saml.service import SSOError, register_idp

    with pytest.raises(SSOError, match="certificate"):
        register_idp(entity_id="https://x.com", sso_url="https://x.com", slo_url="",
                     certificate="", binding="redirect", tenant_id=1)


# ---------------------------------------------------------------------------
# 6. deactivate_idp — happy path
# ---------------------------------------------------------------------------


def test_deactivate_idp():
    idp = _make_idp(status="active")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[idp]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.sso_saml.service import deactivate_idp

        result = deactivate_idp(idp_id=1, tenant_id=42)

        assert result.status == "inactive"
        update_payload = mock_update.call_args[0][2]
        assert update_payload["status"] == "inactive"


# ---------------------------------------------------------------------------
# 7. deactivate_idp — already inactive
# ---------------------------------------------------------------------------


def test_deactivate_already_inactive_raises():
    idp = _make_idp(status="inactive")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[idp]):
        from app.modules.sso_saml.service import SSOError, deactivate_idp

        with pytest.raises(SSOError, match="already inactive"):
            deactivate_idp(idp_id=1, tenant_id=42)


# ---------------------------------------------------------------------------
# 8. reactivate_idp — happy path
# ---------------------------------------------------------------------------


def test_reactivate_idp():
    idp = _make_idp(status="inactive")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[idp]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.sso_saml.service import reactivate_idp

        result = reactivate_idp(idp_id=1, tenant_id=42)

        assert result.status == "active"
        update_payload = mock_update.call_args[0][2]
        assert update_payload["status"] == "active"


# ---------------------------------------------------------------------------
# 9. reactivate_idp — already active
# ---------------------------------------------------------------------------


def test_reactivate_already_active_raises():
    idp = _make_idp(status="active")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[idp]):
        from app.modules.sso_saml.service import SSOError, reactivate_idp

        with pytest.raises(SSOError, match="already active"):
            reactivate_idp(idp_id=1, tenant_id=42)


# ---------------------------------------------------------------------------
# 10. list_idps
# ---------------------------------------------------------------------------


def test_list_idps_returns_all():
    idps = [_make_idp(id_=1), _make_idp(id_=2)]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=idps):
        from app.modules.sso_saml.service import list_idps

        result = list_idps(tenant_id=42)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# 11. initiate_sso — happy path
# ---------------------------------------------------------------------------


def test_initiate_sso_creates_session():
    idp = _make_idp(status="active")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[idp]),
        patch(f"{MODULE}.create_entity_for_tenant") as mock_create,
    ):
        mock_create.return_value = {"id": 10}
        from app.modules.sso_saml.service import initiate_sso

        result = initiate_sso(idp_id=1, relay_state="/dashboard", tenant_id=42)

        assert result.session_id == 10
        assert result.status == "initiated"
        assert result.user_id is None
        payload = mock_create.call_args[0][1]
        assert payload["status"] == "initiated"
        assert len(payload["request_id"]) > 0  # random ID generated


# ---------------------------------------------------------------------------
# 12. initiate_sso — inactive IdP
# ---------------------------------------------------------------------------


def test_initiate_sso_inactive_idp_raises():
    idp = _make_idp(status="inactive")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[idp]):
        from app.modules.sso_saml.service import SSOError, initiate_sso

        with pytest.raises(SSOError, match="not active"):
            initiate_sso(idp_id=1, relay_state="", tenant_id=42)


# ---------------------------------------------------------------------------
# 13. initiate_sso — IdP not found
# ---------------------------------------------------------------------------


def test_initiate_sso_idp_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.sso_saml.service import SSOError, initiate_sso

        with pytest.raises(SSOError, match="not found"):
            initiate_sso(idp_id=99, relay_state="", tenant_id=42)


# ---------------------------------------------------------------------------
# 14. process_saml_response — happy path
# ---------------------------------------------------------------------------


def test_process_saml_response_authenticates():
    session = _make_session(status="initiated")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.sso_saml.service import process_saml_response

        result = process_saml_response(
            session_id=10,
            user_id=55,
            name_id="user@university.edu",
            attributes={"email": "user@university.edu"},
            tenant_id=42,
        )

        assert result.status == "authenticated"
        assert result.user_id == 55
        update_payload = mock_update.call_args[0][2]
        assert update_payload["status"] == "authenticated"
        assert update_payload["user_id"] == 55
        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "sso.login_success"


# ---------------------------------------------------------------------------
# 15. process_saml_response — session not initiated
# ---------------------------------------------------------------------------


def test_process_saml_response_wrong_status():
    session = _make_session(status="authenticated")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]):
        from app.modules.sso_saml.service import SSOError, process_saml_response

        with pytest.raises(SSOError, match="expected 'initiated'"):
            process_saml_response(
                session_id=10, user_id=55, name_id="x@y.com",
                attributes={}, tenant_id=42
            )


# ---------------------------------------------------------------------------
# 16. process_saml_response — missing name_id
# ---------------------------------------------------------------------------


def test_process_saml_response_missing_name_id():
    from app.modules.sso_saml.service import SSOError, process_saml_response

    with pytest.raises(SSOError, match="name_id"):
        process_saml_response(session_id=1, user_id=1, name_id="",
                              attributes={}, tenant_id=1)


# ---------------------------------------------------------------------------
# 17. logout_sso — happy path
# ---------------------------------------------------------------------------


def test_logout_sso_revokes_session():
    session = _make_session(status="authenticated", user_id=55)
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.sso_saml.service import logout_sso

        result = logout_sso(session_id=10, tenant_id=42)

        assert result.status == "revoked"
        update_payload = mock_update.call_args[0][2]
        assert update_payload["status"] == "revoked"
        mock_pub.publish.assert_called_once()
        assert mock_pub.publish.call_args[1]["event_type"] == "sso.logout"


# ---------------------------------------------------------------------------
# 18. logout_sso — not authenticated
# ---------------------------------------------------------------------------


def test_logout_non_authenticated_raises():
    session = _make_session(status="initiated")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]):
        from app.modules.sso_saml.service import SSOError, logout_sso

        with pytest.raises(SSOError, match="only authenticated"):
            logout_sso(session_id=10, tenant_id=42)


# ---------------------------------------------------------------------------
# 19. expire_session — happy path
# ---------------------------------------------------------------------------


def test_expire_session_sets_status():
    session = _make_session(status="initiated")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.sso_saml.service import expire_session

        result = expire_session(session_id=10, tenant_id=42)

        assert result.status == "expired"
        assert mock_update.call_args[0][2]["status"] == "expired"


# ---------------------------------------------------------------------------
# 20. expire_session — already expired
# ---------------------------------------------------------------------------


def test_expire_session_already_expired_raises():
    session = _make_session(status="expired")
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[session]):
        from app.modules.sso_saml.service import SSOError, expire_session

        with pytest.raises(SSOError, match="cannot be expired"):
            expire_session(session_id=10, tenant_id=42)


# ---------------------------------------------------------------------------
# 21. add_attribute_mapping — happy path
# ---------------------------------------------------------------------------


def test_add_attribute_mapping():
    with patch(f"{MODULE}.create_entity_for_tenant") as mock_create:
        mock_create.return_value = {"id": 20}
        from app.modules.sso_saml.service import add_attribute_mapping

        result = add_attribute_mapping(
            idp_id=1,
            saml_attribute="urn:oid:1.3.6.1.4.1.5923.1.1.1.7",
            local_field="email",
            tenant_id=42,
        )

        assert result.mapping_id == 20
        assert result.local_field == "email"
        payload = mock_create.call_args[0][1]
        assert payload["saml_attribute"] == "urn:oid:1.3.6.1.4.1.5923.1.1.1.7"


# ---------------------------------------------------------------------------
# 22. list_attribute_mappings — filters by idp_id
# ---------------------------------------------------------------------------


def test_list_attribute_mappings_filters():
    mappings = [
        {"id": 1, "idp_id": 1, "saml_attribute": "email", "local_field": "email"},
        {"id": 2, "idp_id": 2, "saml_attribute": "uid", "local_field": "username"},
        {"id": 3, "idp_id": 1, "saml_attribute": "cn", "local_field": "full_name"},
    ]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=mappings):
        from app.modules.sso_saml.service import list_attribute_mappings

        result = list_attribute_mappings(idp_id=1, tenant_id=42)

        assert len(result) == 2
        assert all(r.idp_id == 1 for r in result)
