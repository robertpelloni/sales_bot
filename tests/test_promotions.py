import os
import json
import base64
import pytest
from fastapi.testclient import TestClient
from hub.main import app
from src.llm_client import construct_system_prompt


@pytest.fixture(scope="module")
def client():
    auth_str = "admin:password"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    with TestClient(app, headers={"Authorization": f"Basic {b64_auth}"}) as c:
        yield c


def test_inventory_promotions_in_system_prompt():
    inventory = {
        "store_name": "Test Boutique",
        "items": [
            {
                "product_name": "Performance Fleece",
                "price_usd": 85.0,
                "unique_selling_points": ["Thermal", "Breathable"]
            }
        ],
        "promotions": [
            {
                "rule_name": "Morning Rush Discount",
                "discount_percent": 10.0,
                "trigger_type": "dwell_time",
                "threshold": "15s",
                "description": "10% off for customers exploring items for over 15 seconds."
            }
        ]
    }

    prompt_modifiers = {
        "sales_framework": "Consultative Problem-Solver",
        "tactics_enforced": ["Highlight insulation value"],
        "constraints": ["No pushy behavior"]
    }

    prompt = construct_system_prompt(inventory, prompt_modifiers)
    assert "Active Promotional Rules & Discounts:" in prompt
    assert "Morning Rush Discount" in prompt
    assert "10.0" in prompt


def test_add_and_delete_promotion(client, monkeypatch, tmp_path):
    test_inventory_file = tmp_path / "inventory.json"
    initial_data = {
        "store_name": "Promo Test Store",
        "items": [],
        "promotions": [
            {
                "rule_name": "Initial Promo",
                "discount_percent": 5.0,
                "trigger_type": "all_items",
                "threshold": "",
                "description": "5% off storewide"
            }
        ]
    }
    test_inventory_file.write_text(json.dumps(initial_data, indent=2))

    # Intercept get_config_path
    from hub import main as hub_main
    monkeypatch.setattr(hub_main, "get_config_path", lambda fname: str(test_inventory_file) if fname == "inventory.json" else "")

    # Add promotion
    response = client.post(
        "/add_promotion",
        data={
            "rule_name": "Flash 20",
            "discount_percent": "20.0",
            "trigger_type": "weather_or_apparel",
            "threshold": "outerwear",
            "description": "20% off all outerwear"
        },
        follow_redirects=True
    )
    assert response.status_code == 200

    saved_data = json.loads(test_inventory_file.read_text())
    assert len(saved_data["promotions"]) == 2
    assert saved_data["promotions"][1]["rule_name"] == "Flash 20"
    assert saved_data["promotions"][1]["discount_percent"] == 20.0

    # Delete first promotion
    del_response = client.post("/delete_promotion/0", follow_redirects=True)
    assert del_response.status_code == 200

    saved_after_delete = json.loads(test_inventory_file.read_text())
    assert len(saved_after_delete["promotions"]) == 1
    assert saved_after_delete["promotions"][0]["rule_name"] == "Flash 20"
