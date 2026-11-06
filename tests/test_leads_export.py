import csv
import io
import base64
import pytest
from fastapi.testclient import TestClient
from hub.main import app


@pytest.fixture(scope="module")
def client():
    auth_str = "admin:password"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    with TestClient(app, headers={"Authorization": f"Basic {b64_auth}"}) as c:
        yield c


def test_export_leads_csv_endpoint(client):
    """Verifies that /api/leads/export returns valid CSV content with correct header columns."""
    # First log a customer interaction
    client.post(
        "/api/log_interaction",
        json={
            "attributes": "grey trench coat, leather briefcase",
            "response": "Premium executive collection is in aisle 4.",
            "sales_framework": "Consultative Problem-Solver",
            "tts_latency_ms": 110
        }
    )

    # Export all interactions
    all_res = client.get("/api/leads/export?all=true")
    assert all_res.status_code == 200
    assert "text/csv" in all_res.headers["content-type"]
    assert 'attachment; filename="crm_all_interactions.csv"' in all_res.headers["content-disposition"]

    # Parse CSV content
    reader = csv.reader(io.StringIO(all_res.text))
    rows = list(reader)
    assert len(rows) >= 2  # header + at least 1 record
    header = rows[0]
    expected_headers = [
        "id", "timestamp", "attributes", "response", "sales_framework",
        "is_lead", "follow_up_notes", "tts_latency_ms", "feedback_score"
    ]
    assert header == expected_headers

    # Check that our logged interaction is present
    attributes_column_idx = header.index("attributes")
    assert any("grey trench coat" in r[attributes_column_idx] for r in rows[1:])


def test_analytics_summary_endpoint(client):
    """Verifies that /api/analytics/summary returns aggregated conversion and performance statistics."""
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "total_interactions" in data
    assert "total_leads" in data
    assert "conversion_rate_percent" in data
    assert "avg_tts_latency_ms" in data
    assert "avg_feedback_score" in data
    assert isinstance(data["total_interactions"], int)
    assert isinstance(data["conversion_rate_percent"], (int, float))
