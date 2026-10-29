import pytest
from app.models.schemas import LogEntry, RecommendationEvaluation, InvestigateRequest
from app.services.analytics import analytics_engine
from app.services.ai_recommender import ai_recommender, ALLOWED_CHART_TYPES
from app.services.investigator import investigator_service
from app.services.storage import storage_service
from app.services.exporter import exporter_service


def test_analytics_and_anomalies():
    entries = [
        LogEntry(id=1, timestamp="2026-10-28T10:00:00", level="INFO", service="auth", message="Login ok", line_number=1, raw_line=""),
        LogEntry(id=2, timestamp="2026-10-28T10:01:00", level="ERROR", service="db", message="Query timeout", status_code=504, response_time_ms=5000.0, line_number=2, raw_line=""),
        LogEntry(id=3, timestamp="2026-10-28T10:01:30", level="ERROR", service="db", message="Query timeout", status_code=504, response_time_ms=5200.0, line_number=3, raw_line=""),
        LogEntry(id=4, timestamp="2026-10-28T10:02:00", level="WARNING", service="auth", message="High load", line_number=4, raw_line=""),
        LogEntry(id=5, timestamp="2026-10-28T10:02:30", level="INFO", service="api", message="Health check", status_code=200, response_time_ms=15.0, line_number=5, raw_line=""),
    ]

    analytics = analytics_engine.compute_analytics(entries, total_lines=6, malformed_count=1)

    assert analytics.total_lines == 6
    assert analytics.parsed_lines == 5
    assert analytics.unparsed_lines == 1
    assert analytics.success_rate == 83.33
    assert analytics.error_count == 2
    assert analytics.warning_count == 1
    assert analytics.info_count == 2
    assert analytics.distinct_services_count == 3

    # Top errors
    assert len(analytics.top_errors) == 1
    assert analytics.top_errors[0].message == "Query timeout"
    assert analytics.top_errors[0].count == 2

    # Response time stats
    assert analytics.response_time_stats is not None
    assert analytics.response_time_stats.count == 3
    assert analytics.response_time_stats.min_ms == 15.0
    assert analytics.response_time_stats.max_ms == 5200.0


def test_ai_recommender_fallback_and_allowlist():
    # Test without API key (rule-based fallback)
    entries = [
        LogEntry(id=1, timestamp="2026-10-28T10:00:00", level="INFO", service="auth", message="ok", line_number=1, raw_line=""),
        LogEntry(id=2, timestamp="2026-10-28T10:01:00", level="ERROR", service="db", message="fail", status_code=500, response_time_ms=100.0, line_number=2, raw_line=""),
    ]
    analytics = analytics_engine.compute_analytics(entries, total_lines=2, malformed_count=0)
    avail_fields = ["timestamp", "level", "service", "message", "status_code", "response_time_ms"]

    recs = ai_recommender.generate_recommendations(avail_fields, analytics, "app_log")

    assert len(recs) >= 4
    for r in recs:
        # Chart type must be in allowlist
        assert r.chart_type in ALLOWED_CHART_TYPES
        # Required fields must only use available fields
        assert all(f in avail_fields for f in r.required_fields)
        # Suitability score between 0.0 and 1.0
        assert 0.0 <= r.suitability_score <= 1.0
        assert len(r.analytical_question) > 5


def test_investigator_factual_calculation():
    entries = [
        LogEntry(id=1, timestamp="2026-10-28T10:00:00", level="INFO", service="auth", message="ok", line_number=1, raw_line=""),
        LogEntry(id=2, timestamp="2026-10-28T10:01:00", level="ERROR", service="db", message="Database connection refused", line_number=2, raw_line=""),
    ]
    analytics = analytics_engine.compute_analytics(entries, total_lines=2, malformed_count=0)

    req = InvestigateRequest(query="Which service generates the most errors?")
    resp = investigator_service.investigate(req, entries, analytics)

    assert resp.evidence_found is True
    assert any("db" in f for f in resp.factual_findings)
    assert len(resp.hypotheses) > 0
    assert len(resp.recommended_checks) > 0


def test_evaluations_and_acceptance_rate():
    session = storage_service.create_dataset("test.log", "/tmp/test.log", 100, "app_log")
    
    # 3 recommendations
    avail_fields = ["timestamp", "level"]
    entries = [LogEntry(id=1, timestamp="2026-10-28T10:00:00", level="INFO", message="ok", line_number=1, raw_line="")]
    analytics = analytics_engine.compute_analytics(entries, total_lines=1, malformed_count=0)
    recs = ai_recommender.generate_recommendations(avail_fields, analytics, "app_log")
    session.recommendations = recs

    # User evaluates
    session.evaluations[recs[0].id] = RecommendationEvaluation(
        recommendation_id=recs[0].id,
        chart_type=recs[0].chart_type,
        status="accepted",
        timestamp="2026-10-28T10:05:00",
    )
    if len(recs) > 1:
        session.evaluations[recs[1].id] = RecommendationEvaluation(
            recommendation_id=recs[1].id,
            chart_type=recs[1].chart_type,
            status="rejected",
            user_reason="Not needed for this project",
            timestamp="2026-10-28T10:06:00",
        )

    summary = session.get_evaluation_summary()
    assert summary.total_recommendations == len(recs)
    assert summary.accepted_count == 1
    assert summary.rejected_count == (1 if len(recs) > 1 else 0)
    assert summary.acceptance_rate == round(1 / len(recs) * 100.0, 1)


def test_exporter():
    entries = [
        LogEntry(id=1, timestamp="2026-10-28T10:00:00", level="INFO", service="auth", message="User login", line_number=1, raw_line="raw1"),
    ]
    csv_str = exporter_service.export_csv(entries)
    assert "User login" in csv_str
    assert "timestamp" in csv_str

    json_str = exporter_service.export_json(entries)
    assert '"service": "auth"' in json_str

    malformed = [
        LogEntry(id=2, raw_line="corrupt line", line_number=2, parse_status="malformed", error_details="Invalid header")
    ]
    unparsed_str = exporter_service.export_unparsed_txt(malformed)
    assert "Line 2: corrupt line" in unparsed_str
    assert "Invalid header" in unparsed_str

