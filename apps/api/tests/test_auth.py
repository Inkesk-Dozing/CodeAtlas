import pytest
from fastapi import HTTPException

from services.auth import create_access_token, create_refresh_token, decode_token


class TestAccessToken:
    def test_round_trip(self):
        token = create_access_token("user-123", role="admin", org_id="org-1")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["role"] == "admin"
        assert payload["org_id"] == "org-1"
        assert payload["type"] == "access"

    def test_default_role(self):
        payload = decode_token(create_access_token("u1"))
        assert payload["role"] == "member"

    def test_tampered_token_rejected(self):
        token = create_access_token("user-123")
        with pytest.raises(HTTPException):
            decode_token(token[:-4] + "AAAA")

    def test_garbage_token_rejected(self):
        with pytest.raises(HTTPException):
            decode_token("not.a.token")


class TestRefreshToken:
    def test_round_trip(self):
        token = create_refresh_token("user-456", jti="jti-1")
        payload = decode_token(token)
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"
        assert payload["jti"] == "jti-1"

    def test_access_token_is_not_refresh(self):
        payload = decode_token(create_access_token("user-456"))
        assert payload.get("type") != "refresh"
