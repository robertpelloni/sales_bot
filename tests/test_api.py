import sys
import os
import pytest
from fastapi.testclient import TestClient
import pytest_asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from hub.main import app

import base64

@pytest.fixture(scope="module")
def client():
    auth_str = "admin:password"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    with TestClient(app, headers={"Authorization": f"Basic {b64_auth}"}) as c:
        yield c

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Project Sirens - Dashboard" in response.text

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
    assert "Agent Response Generated:" in response.text

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
