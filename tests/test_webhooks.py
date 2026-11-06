import pytest
import os
import json
import hmac
import hashlib
from fastapi.testclient import TestClient
from hub.main import app
from hub.webhooks import WebhookManager, webhook_manager


def test_webhook_manager_signature():
    mgr = WebhookManager()
    payload = b'{"event": "TEST", "data": {"key": "val"}}'
    secret = "super_secret_crm_key"
    sig = mgr.sign_payload(payload, secret)
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    assert sig == expected
    assert mgr.sign_payload(payload, "") == ""


@pytest.mark.asyncio
async def test_webhook_dispatch_disabled(tmp_path):
    cfg_file = tmp_path / "webhooks.json"
    mgr = WebhookManager(config_path=str(cfg_file))
    mgr.save_config({"enabled": False, "url": "https://example.com/webhook"})

    dispatched = await mgr.dispatch_event("NEW_INTERACTION", {"msg": "hello"})
    assert dispatched is False


@pytest.mark.asyncio
async def test_webhook_dispatch_enabled_event_filtering(tmp_path, monkeypatch):
    cfg_file = tmp_path / "webhooks.json"
    mgr = WebhookManager(config_path=str(cfg_file))
    mgr.save_config({
        "enabled": True,
        "url": "https://example.com/webhook",
        "secret": "testsecret",
        "events": ["LEAD_QUALIFIED"]
    })

    # NEW_INTERACTION is not in configured events -> should return False
    assert await mgr.dispatch_event("NEW_INTERACTION", {"foo": "bar"}) is False

    # Mock _send_http_request
    sent_payloads = []
    async def mock_send(payload):
        sent_payloads.append(payload)
        return True

    monkeypatch.setattr(mgr, "_send_http_request", mock_send)
    assert await mgr.dispatch_event("LEAD_QUALIFIED", {"lead_id": 42}) is True


def test_api_webhook_config_endpoints(monkeypatch, tmp_path):
    cfg_file = tmp_path / "webhooks.json"
    monkeypatch.setattr(webhook_manager, "config_path", str(cfg_file))
    webhook_manager.config = webhook_manager.load_config()

    client = TestClient(app)
    auth = ("admin", "password")

    # GET config
    res = client.get("/api/webhooks/config", auth=auth)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "enabled" in data["config"]

    # POST config
    update_data = {
        "enabled": True,
        "url": "https://crm.example.com/api/v1",
        "secret": "webhook-secret-123",
        "events": ["NEW_INTERACTION", "LEAD_QUALIFIED"],
        "timeout_seconds": 3.0
    }
    res = client.post("/api/webhooks/config", json=update_data, auth=auth)
    assert res.status_code == 200
    cfg = res.json()["config"]
    assert cfg["enabled"] is True
    assert cfg["url"] == "https://crm.example.com/api/v1"
    assert cfg["secret"] == "webhook-secret-123"

    # POST /api/webhooks/test with mocked HTTP call
    async def mock_post(payload):
        return True

    monkeypatch.setattr(webhook_manager, "_send_http_request", mock_post)
    test_res = client.post("/api/webhooks/test", auth=auth)
    assert test_res.status_code == 200
    assert test_res.json()["status"] == "success"


def test_update_webhooks_form_submission(monkeypatch, tmp_path):
    cfg_file = tmp_path / "webhooks.json"
    monkeypatch.setattr(webhook_manager, "config_path", str(cfg_file))
    client = TestClient(app)
    auth = ("admin", "password")

    form_data = {
        "enabled": "True",
        "url": "https://zapier.com/hooks/catch/123",
        "secret": "zapier_secret",
        "event_lead_qualified": "LEAD_QUALIFIED",
        "timeout_seconds": "4.5"
    }
    res = client.post("/update_webhooks", data=form_data, auth=auth, follow_redirects=False)
    assert res.status_code == 303

    assert webhook_manager.config["enabled"] is True
    assert webhook_manager.config["url"] == "https://zapier.com/hooks/catch/123"
    assert webhook_manager.config["events"] == ["LEAD_QUALIFIED"]
    assert webhook_manager.config["timeout_seconds"] == 4.5
