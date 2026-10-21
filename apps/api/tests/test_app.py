from fastapi.testclient import TestClient

import main
from routers.webhooks import verify_signature


class TestWebhookSignature:
    def test_valid_signature(self):
        import hashlib
        import hmac

        from config import settings

        payload = b'{"action": "opened"}'
        sig = "sha256=" + hmac.new(
            settings.github_webhook_secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        assert verify_signature(payload, sig) is True

    def test_invalid_signature(self):
        assert verify_signature(b"{}", "sha256=deadbeef") is False

    def test_missing_signature(self):
        assert verify_signature(b"{}", None) is False

    def test_wrong_prefix(self):
        assert verify_signature(b"{}", "sha1=abc") is False

    def test_tampered_payload(self):
        import hashlib
        import hmac

        from config import settings

        sig = "sha256=" + hmac.new(
            settings.github_webhook_secret.encode(), b"original", hashlib.sha256
        ).hexdigest()
        assert verify_signature(b"tampered", sig) is False


class TestAppHealth:
    def setup_method(self):
        self.client = TestClient(main.app)

    def test_ready_reports_database(self):
        resp = self.client.get("/ready")
        assert resp.status_code in (200, 503)
        body = resp.json()
        assert "status" in body
        assert "checks" in body

    def test_health_shape(self):
        resp = self.client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert set(body) >= {"status", "version", "checks", "timestamp"}

    def test_openapi_has_expected_paths(self):
        spec = main.app.openapi()
        assert "/api/v1/repos" in spec["paths"]
        assert "/api/v1/webhooks/github" in spec["paths"]
        assert "/api/v1/repos/{repo_id}/chat" in spec["paths"]
        assert "/api/v1/repos/{repo_id}/summary" in spec["paths"]

    def test_request_id_header_present(self):
        resp = self.client.get("/health")
        assert "X-Request-ID" in resp.headers

    def test_rate_limit_headers_present(self):
        resp = self.client.get("/health")
        assert "X-RateLimit-Limit" in resp.headers

    def test_rate_limiter_blocks_after_burst(self):
        for _ in range(130):
            r = self.client.post(
                "/api/v1/webhooks/github",
                json={},
                headers={"X-GitHub-Event": "ping", "X-Hub-Signature-256": "sha256=bad"},
            )
            if r.status_code == 429:
                assert r.headers.get("Retry-After")
                assert r.json()["error"]["code"] == "RATE_LIMITED"
                return
        raise AssertionError("rate limiter never triggered within expected burst")
