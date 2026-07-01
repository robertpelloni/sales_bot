import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from hub.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Project Sirens - Dashboard" in response.text

def test_update_system_config():
    # Make sure we don't accidentally leak real API keys into git
    response = client.post(
        "/update_system_config",
        data={"openai_api_key": "test_mock_key_123", "use_mock_vision": "True"}
    )
    assert response.status_code == 200
    assert "test_mock_key_123" in response.text

def test_simulate_detection():
    # Make sure to mock the API key so we don't hit OpenAI in unit tests
    os.environ["OPENAI_API_KEY"] = ""
    os.environ["USE_MOCK_VISION"] = "True"

    response = client.post(
        "/simulate_detection",
        data={"attributes": "navy blue windbreaker, baseball cap"}
    )
    assert response.status_code == 200
    # Our fallback logic triggers on "windbreaker" and returns the "winter coat" line
    assert "winter coat" in response.text
    assert "Bot Response:" in response.text

def test_add_item_and_settings():
    # Testing that the UI configuration routing handles POST requests gracefully
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
