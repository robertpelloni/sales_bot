import sys
import os
import pytest
from fastapi.testclient import TestClient
import pytest_asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from hub.main import app

import base64
from unittest.mock import patch

@pytest.fixture(scope="module")
def client():
    auth_str = "admin:password"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    with TestClient(app, headers={"Authorization": f"Basic {b64_auth}"}) as c:
        yield c

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Project Sirens" in response.text
    assert "Autonomous Retail Engine" in response.text

def test_update_system_config(client):
    # Make sure we don't accidentally leak real API keys into git
    response = client.post(
        "/update_system_config",
        data={"openai_api_key": "test_mock_key_123", "use_mock_vision": "True"}
    )
    assert response.status_code == 200
    assert "test_mock_key_123" in response.text

def test_simulate_detection(client):
    # Make sure to mock the API key so we don't hit OpenAI in unit tests
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["USE_MOCK_VISION"] = "True"

    response = client.post(
        "/simulate_detection",
        data={
            "attributes": "navy blue windbreaker, baseball cap",
            "system_prompt_override": "Be super nice.",
            "temperature": "1.0"
        }
    )
    assert response.status_code == 200
    # Our fallback logic triggers on "windbreaker" and returns the "winter coat" line
    assert "winter coat" in response.text
    assert "Generated Autonomous Pitch:" in response.text

def test_add_item_and_settings(client, monkeypatch, tmp_path):
    # Testing that the UI configuration routing handles POST requests gracefully
    # We patch get_config_path so it writes to a temporary directory instead of polluting the real files.
    import hub.main

    def mock_get_config_path(filename):
        return str(tmp_path / filename)

    monkeypatch.setattr(hub.main, "get_config_path", mock_get_config_path)

    response = client.post(
        "/update_settings",
        data={"store_name": "Integration Test Store", "sales_framework": "Aggressive Testing"}
    )
    assert response.status_code == 200

    response = client.post(
        "/add_item",
        data={"product_name": "Test Item", "price_usd": "99.99", "usps": "Point 1, Point 2"}
    )
    assert response.status_code == 200
    assert "Test Item" in response.text
    assert "99.99" in response.text

def test_log_interaction(client):
    response = client.post(
        "/api/log_interaction",
        json={"attributes": "pytest_attribute", "response": "pytest_response"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "id" in response.json()

    response = client.get("/")
    assert response.status_code == 200
    assert "pytest_attribute" in response.text
    assert "pytest_response" in response.text

def test_lead_tracking(client):
    # Insert a dummy interaction to track
    response = client.post(
        "/api/log_interaction",
        json={"attributes": "lead_test", "response": "lead_response"}
    )
    interaction_id = response.json()["id"]

    # Mark as lead
    response = client.post(f"/mark_lead/{interaction_id}", data={"is_lead": "True"})
    assert response.status_code == 200
    assert "Qualified Lead" in response.text

    # Update Follow-up notes
    response = client.post(f"/update_follow_up/{interaction_id}", data={"follow_up_notes": "Call them back tomorrow."})
    assert response.status_code == 200
    assert "Call them back tomorrow." in response.text


def test_server_status_and_shutdown(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Project Sirens Hub"
    assert data["version"] == "0.6.0"
    assert "mock_vision" in data
    assert "inventory_item_count" in data

    # Test shutdown endpoint with mock kill to prevent terminating pytest process
    with patch("os.kill") as mock_kill:
        response = client.post("/api/server/shutdown")
        assert response.status_code == 200
        assert response.json()["status"] == "shutting_down"


def test_add_and_delete_promotion(client, monkeypatch, tmp_path):
    """Verifies adding and deleting dynamic promotions through the Hub API."""
    import json
    dummy_inv = {
        "store_name": "Test Promo Store",
        "items": [],
        "promotions": [
            {
                "rule_name": "Initial Rule",
                "discount_percent": 10,
                "trigger_type": "dwell_time",
                "threshold": 15,
                "description": "Initial test rule"
            }
        ]
    }
    inv_file = tmp_path / "inventory.json"
    inv_file.write_text(json.dumps(dummy_inv))

    monkeypatch.setattr("hub.main.get_config_path", lambda f: str(inv_file) if "inventory" in f else None)

    # 1. Add new promotion rule
    resp = client.post("/add_promotion", data={
        "rule_name": "VIP Dwell Discount",
        "discount_percent": 25,
        "trigger_type": "dwell_time",
        "threshold": 60,
        "description": "25% discount after 60s dwell"
    }, follow_redirects=False)
    assert resp.status_code == 303

    with open(inv_file, "r") as f:
        data = json.load(f)
    assert len(data["promotions"]) == 2
    assert data["promotions"][1]["rule_name"] == "VIP Dwell Discount"
    assert data["promotions"][1]["discount_percent"] == 25

    # 2. Delete the first promotion rule (index 0)
    del_resp = client.post("/delete_promotion/0", follow_redirects=False)
    assert del_resp.status_code == 303

    with open(inv_file, "r") as f:
        data = json.load(f)
    assert len(data["promotions"]) == 1
    assert data["promotions"][0]["rule_name"] == "VIP Dwell Discount"


def test_websocket_event_streaming(client):
    # Connect websocket client to /ws/events and verify broadcast reception
    with client.websocket_connect("/ws/events") as websocket:
        # Trigger an interaction via the REST webhook
        post_resp = client.post(
            "/api/log_interaction",
            json={
                "attributes": "red sneakers, baseball cap",
                "response": "Real-time stream test pitch.",
                "sales_framework": "Challenger",
                "tts_latency_ms": 120
            }
        )
        assert post_resp.status_code == 200

        # Receive the event over WebSocket
        data = websocket.receive_json()
        assert data["event"] == "NEW_INTERACTION"
        assert data["data"]["attributes"] == "red sneakers, baseball cap"
        assert data["data"]["response"] == "Real-time stream test pitch."
        assert data["data"]["sales_framework"] == "Challenger"
        assert data["data"]["tts_latency_ms"] == 120
