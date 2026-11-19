import json

import httpx
import pytest

from app.api.routes import get_recommendations, investigate_logs, load_sample_log, parse_dataset
from app.models.schemas import InvestigateRequest
from app.services import gemini
from app.services.ai_recommender import ai_recommender
from app.services.investigator import investigator_service


@pytest.mark.parametrize("failure", [None, "rate_limit", "empty_response"])
def test_gemini_through_recommendation_and_investigation_routes(monkeypatch, failure):
    requests = []

    def handle_gemini(request):
        assert request.url.host == "generativelanguage.googleapis.com"
        assert request.url.path == "/v1beta/models/gemini-test:generateContent"
        assert request.headers["x-goog-api-key"] == "test-key"
        assert not request.url.query
        body = json.loads(request.content)
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        assert body["generationConfig"]["responseJsonSchema"]["type"] == "object"
        prompt = json.loads(body["contents"][0]["parts"][0]["text"])
        requests.append(prompt)

        if failure == "rate_limit":
            return httpx.Response(429)
        if failure == "empty_response":
            return httpx.Response(200, json={"candidates": []})

        if "chart_options" in prompt:
            suggestion = {
                "id": prompt["chart_options"][0]["id"],
                "title": "Gemini chart title",
                "analytical_question": "Which log events are most frequent?",
                "reason": "Shows the most relevant events.",
                "expected_insight": "Recurring events become visible.",
                "limitations": "Limited to the sample.",
                "suitability_score": 0.97,
            }
            content = {
                "recommendations": [
                    {**suggestion, "id": "unsupported-chart"},
                    suggestion,
                    suggestion,
                ]
            }
        else:
            content = {
                "factual_findings": ["Fabricated finding"],
                "hypotheses": ["Investigate possible queuing delays."],
                "recommended_checks": ["Compare p95 across intervals."],
            }
        parts = [{"text": "Internal thought", "thought": True}, {"text": json.dumps(content)}]
        return httpx.Response(200, json={
            "candidates": [{"finishReason": "STOP", "content": {"parts": parts}}],
        })

    client_class = httpx.Client
    transport = httpx.MockTransport(handle_gemini)
    for service in (ai_recommender, investigator_service):
        monkeypatch.setattr(service, "api_key", "test-key")
        monkeypatch.setattr(service, "model", "gemini-test")
    monkeypatch.setattr(
        gemini.httpx, "Client", lambda **kwargs: client_class(transport=transport, **kwargs)
    )

    dataset_id = load_sample_log("web_access.log")["dataset_id"]
    parse_dataset(dataset_id, format_name=None)
    charts = get_recommendations(dataset_id)
    investigation = investigate_logs(dataset_id, InvestigateRequest(query="What is the response time?"))

    expected_source = "rules" if failure else "gemini"
    assert len(requests) == 2
    assert charts and all(chart.source == expected_source for chart in charts)
    assert investigation.source == expected_source
    assert investigation.evidence_found
    assert "p95_response_time_ms" in investigation.supporting_metrics
    assert "Fabricated finding" not in investigation.factual_findings
    if not failure:
        assert len(charts) == 1
        assert charts[0].title == "Gemini chart title"
        assert investigation.recommended_checks == ["Compare p95 across intervals."]
