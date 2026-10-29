import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.storage import storage_service

client = TestClient(app)


def test_health_and_formats():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

    resp = client.get("/api/logs/formats")
    assert resp.status_code == 200
    formats = resp.json()["formats"]
    format_ids = [f["id"] for f in formats]
    assert "app_log" in format_ids
    assert "python_log" in format_ids
    assert "access_log" in format_ids
    assert "json_log" in format_ids
    assert "csv_log" in format_ids


def test_sample_loading_and_parse_flow():
    # 1. Load sample log
    resp = client.post("/api/logs/sample/application.log")
    assert resp.status_code == 200
    data = resp.json()
    dataset_id = data["dataset_id"]
    assert dataset_id is not None
    assert data["detected_format"] == "app_log"
    assert len(data["preview_lines"]) > 0

    # 2. Parse dataset
    parse_resp = client.post(f"/api/logs/{dataset_id}/parse")
    assert parse_resp.status_code == 200
    parse_data = parse_resp.json()
    assert parse_data["status"] == "success"
    assert parse_data["data_quality"]["parsed_lines"] > 50
    assert parse_data["data_quality"]["unparsed_lines"] >= 2  # synthetic malformed entries included!
    assert parse_data["data_quality"]["success_rate"] > 70.0

    # 3. Entries
    entries_resp = client.get(f"/api/logs/{dataset_id}/entries?page=1&page_size=10")
    assert entries_resp.status_code == 200
    entries_data = entries_resp.json()
    assert len(entries_data["entries"]) == 10
    assert entries_data["total"] > 50

    # 4. Analytics
    analytics_resp = client.get(f"/api/logs/{dataset_id}/analytics")
    assert analytics_resp.status_code == 200
    analytics_data = analytics_resp.json()
    assert analytics_data["error_count"] > 0
    assert len(analytics_data["service_stats"]) > 0

    # 5. Recommendations
    recs_resp = client.post(f"/api/logs/{dataset_id}/recommendations")
    assert recs_resp.status_code == 200
    recs = recs_resp.json()
    assert len(recs) >= 3
    rec_id = recs[0]["id"]

    # 6. Evaluations
    eval_resp = client.post(
        f"/api/logs/{dataset_id}/evaluations",
        json={
            "recommendation_id": rec_id,
            "chart_type": recs[0]["chart_type"],
            "status": "accepted",
            "timestamp": "2026-10-28T12:00:00",
        }
    )
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["accepted_count"] == 1
    assert eval_data["acceptance_rate"] > 0.0

    # 7. Investigate
    inv_resp = client.post(
        f"/api/logs/{dataset_id}/investigate",
        json={"query": "What are the most common errors?"}
    )
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()
    assert inv_data["evidence_found"] is True
    assert len(inv_data["factual_findings"]) > 0

    # 8. Export CSV
    export_resp = client.get(f"/api/logs/{dataset_id}/export?format=csv")
    assert export_resp.status_code == 200
    assert "timestamp" in export_resp.text

