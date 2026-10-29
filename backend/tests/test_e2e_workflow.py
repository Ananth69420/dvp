import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_complete_end_to_end_dvp_workflow():
    # Step 1: Health Check
    health = client.get("/api/health")
    assert health.status_code == 200

    # Step 2: Load Synthetic Python Log Sample
    upload_res = client.post("/api/logs/sample/python_app.log")
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    ds_id = upload_data["dataset_id"]
    assert upload_data["detected_format"] == "python_log"
    assert len(upload_data["preview_lines"]) > 0

    # Step 3: Execute Parser Engine
    parse_res = client.post(f"/api/logs/{ds_id}/parse")
    assert parse_res.status_code == 200
    p_data = parse_res.json()
    assert p_data["status"] == "success"
    dq = p_data["data_quality"]
    assert dq["parsed_lines"] > 50
    assert dq["unparsed_lines"] >= 1  # synthetic malformed line included
    assert dq["success_rate"] > 75.0

    # Step 4: Verify Dataset Profile
    profile_res = client.get(f"/api/logs/{ds_id}/profile")
    assert profile_res.status_code == 200
    prof = profile_res.json()
    assert "timestamp" in prof["available_fields"]
    assert "level" in prof["available_fields"]
    assert "message" in prof["available_fields"]

    # Step 5: Filter Entries in Explorer Table
    err_entries_res = client.get(f"/api/logs/{ds_id}/entries?level=ERROR&page=1&page_size=10")
    assert err_entries_res.status_code == 200
    err_data = err_entries_res.json()
    assert err_data["total"] > 0
    # Check that traceback is preserved in message
    sample_err = err_data["entries"][0]
    assert sample_err["level"] == "ERROR"

    # Step 6: Verify Analytics & Anomalies
    analytics_res = client.get(f"/api/logs/{ds_id}/analytics")
    assert analytics_res.status_code == 200
    analytics = analytics_res.json()
    assert analytics["error_count"] > 0
    assert len(analytics["service_stats"]) > 0
    assert len(analytics["top_errors"]) > 0

    # Step 7: Request AI Recommendations
    recs_res = client.post(f"/api/logs/{ds_id}/recommendations")
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert len(recs) >= 3

    # Step 8: Evaluate Recommendations (Accept, Reject, Modify)
    rec1 = recs[0]
    rec2 = recs[1]
    rec3 = recs[2]

    # Accept rec1
    client.post(
        f"/api/logs/{ds_id}/evaluations",
        json={
            "recommendation_id": rec1["id"],
            "chart_type": rec1["chart_type"],
            "status": "accepted",
            "timestamp": "2026-10-28T12:00:00",
        }
    )

    # Reject rec2
    client.post(
        f"/api/logs/{ds_id}/evaluations",
        json={
            "recommendation_id": rec2["id"],
            "chart_type": rec2["chart_type"],
            "status": "rejected",
            "user_reason": "Not prioritizing this chart",
            "timestamp": "2026-10-28T12:01:00",
        }
    )

    # Modify rec3
    eval_summary_res = client.post(
        f"/api/logs/{ds_id}/evaluations",
        json={
            "recommendation_id": rec3["id"],
            "chart_type": rec3["chart_type"],
            "status": "modified",
            "modified_chart_type": "bar",
            "user_reason": "Better discrete visual breakdown",
            "timestamp": "2026-10-28T12:02:00",
        }
    )
    assert eval_summary_res.status_code == 200
    eval_summary = eval_summary_res.json()
    assert eval_summary["total_recommendations"] == len(recs)
    assert eval_summary["accepted_count"] == 1
    assert eval_summary["rejected_count"] == 1
    assert eval_summary["modified_count"] == 1
    # Acceptance rate = accepted / total * 100
    expected_rate = round(1 / len(recs) * 100.0, 1)
    assert eval_summary["acceptance_rate"] == expected_rate

    # Step 9: SRE AI-Assisted Investigation Query
    inv_res = client.post(
        f"/api/logs/{ds_id}/investigate",
        json={"query": "What should I inspect first?"}
    )
    assert inv_res.status_code == 200
    inv = inv_res.json()
    assert inv["evidence_found"] is True
    assert len(inv["factual_findings"]) > 0
    assert len(inv["hypotheses"]) > 0
    assert len(inv["recommended_checks"]) > 0

    # Step 10: Export CSV & HTML Report
    csv_res = client.get(f"/api/logs/{ds_id}/export?format=csv")
    assert csv_res.status_code == 200
    assert "timestamp" in csv_res.text
    assert "level" in csv_res.text

    html_res = client.get(f"/api/logs/{ds_id}/export?format=html")
    assert html_res.status_code == 200
    assert "<!DOCTYPE html>" in html_res.text
    assert "Log Analysis Report" in html_res.text
    assert "Data Quality &amp; Parser Performance" in html_res.text

