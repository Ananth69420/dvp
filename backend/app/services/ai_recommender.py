import json
from typing import List, Dict, Any, Optional
import httpx
from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.models.schemas import ChartRecommendation, LogAnalytics

ALLOWED_CHART_TYPES = {"line", "stacked_bar", "bar", "pie", "donut", "histogram", "heatmap"}
ALLOWED_FIELDS = {
    "timestamp",
    "level",
    "service",
    "message",
    "status_code",
    "response_time_ms",
    "source_ip",
    "http_method",
    "request_path",
}


class AiRecommenderService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL

    def generate_recommendations(
        self,
        available_fields: List[str],
        analytics: LogAnalytics,
        format_name: str,
    ) -> List[ChartRecommendation]:
        """
        Generates validated chart recommendations.
        Tries AI first if API key is present; otherwise (or on failure) uses intelligent rule-based engine.
        """
        if self.api_key and len(self.api_key.strip()) > 5:
            try:
                ai_recs = self._call_openai_recommendations(available_fields, analytics, format_name)
                if ai_recs:
                    return ai_recs
            except Exception:
                pass  # Fallback to rule-based

        return self._rule_based_recommendations(available_fields, analytics)

    def _rule_based_recommendations(
        self, available_fields: List[str], analytics: LogAnalytics
    ) -> List[ChartRecommendation]:
        recs: List[ChartRecommendation] = []
        fields_set = set(available_fields)

        # 1. Log Volume Timeline (Requires timestamp)
        if "timestamp" in fields_set and len(analytics.time_series) > 0:
            recs.append(
                ChartRecommendation(
                    id="rec-volume-timeline",
                    chart_type="line",
                    title="Log Volume & Error Trajectory Over Time",
                    analytical_question="When did traffic spikes, operational degradation, or error cascades occur?",
                    required_fields=["timestamp", "level"],
                    reason="Time-series line chart provides an intuitive view of volume fluctuation and error surges across temporal windows.",
                    expected_insight="Pinpoint exact timestamps of error bursts, system crashes, or recovery phases.",
                    limitations="Requires continuous timestamp coverage. Non-uniform intervals may display sparse buckets.",
                    suitability_score=0.96,
                    aggregation_target="time_series",
                    time_interval="auto",
                )
            )

        # 2. Severity Distribution Over Time (Stacked Bar)
        if "timestamp" in fields_set and "level" in fields_set and len(analytics.time_series) > 0:
            recs.append(
                ChartRecommendation(
                    id="rec-severity-stacked",
                    chart_type="stacked_bar",
                    title="Temporal Severity Composition",
                    analytical_question="How does the proportion of errors and warnings evolve compared to normal informational logs?",
                    required_fields=["timestamp", "level"],
                    reason="Stacked bars allow comparative inspection of severity ratios across intervals.",
                    expected_insight="Detect whether warnings precede hard error spikes, indicating progressive degradation.",
                    limitations="Overcrowded on very wide date ranges without aggregation rollup.",
                    suitability_score=0.91,
                    aggregation_target="time_series",
                    time_interval="auto",
                )
            )

        # 3. Overall Severity Distribution (Donut / Pie)
        if "level" in fields_set and (analytics.error_count > 0 or analytics.info_count > 0):
            recs.append(
                ChartRecommendation(
                    id="rec-severity-pie",
                    chart_type="donut",
                    title="Overall Severity Ratio",
                    analytical_question="What fraction of total events represent actionable failures versus background traffic?",
                    required_fields=["level"],
                    reason="Donut charts display high-level categorical ratios immediately for executive operational summaries.",
                    expected_insight="Determine fleet health baseline (e.g. error budget adherence, high warning ratio).",
                    limitations="Does not communicate temporal sequence or localized service context.",
                    suitability_score=0.88,
                    aggregation_target="severity_distribution",
                )
            )

        # 4. Errors by Service (Bar)
        if "service" in fields_set and analytics.distinct_services_count > 1 and analytics.error_count > 0:
            recs.append(
                ChartRecommendation(
                    id="rec-service-errors",
                    chart_type="bar",
                    title="Error Distribution Across Services",
                    analytical_question="Which specific microservices or components are driving the majority of system faults?",
                    required_fields=["service", "level"],
                    reason="Categorical bar chart highlights outlier services with disproportionate failure rates.",
                    expected_insight="Isolate fault domains (e.g., database timeout vs authentication service rejection).",
                    limitations="Requires service tagging in log entries; services with single failures may clutter axis.",
                    suitability_score=0.93,
                    aggregation_target="service_stats",
                )
            )

        # 5. Top Recurring Error Signatures (Bar)
        if len(analytics.top_errors) > 0:
            recs.append(
                ChartRecommendation(
                    id="rec-top-errors",
                    chart_type="bar",
                    title="Top Recurring Error Signatures",
                    analytical_question="What are the highest-frequency error messages requiring immediate triage or bug fixes?",
                    required_fields=["message", "level"],
                    reason="Horizontal or vertical ranked bars focus engineering attention on high-impact recurring bugs.",
                    expected_insight="Distinguish between one-off anomalies and systemic recurring bugs.",
                    limitations="Long error messages require truncation; dynamic stack traces might need grouping.",
                    suitability_score=0.95,
                    aggregation_target="top_errors",
                )
            )

        # 6. HTTP Status Code Distribution (Bar)
        if "status_code" in fields_set and len(analytics.status_code_distribution) > 0:
            recs.append(
                ChartRecommendation(
                    id="rec-status-codes",
                    chart_type="bar",
                    title="HTTP Status Code Breakdown",
                    analytical_question="What is the distribution of 2xx, 4xx, and 5xx HTTP response codes across requests?",
                    required_fields=["status_code"],
                    reason="Standard web infrastructure metric to diagnose client vs server errors.",
                    expected_insight="Identify high 404/403 scan attempts or 500/502 gateway outages.",
                    limitations="Only applicable when web server or gateway HTTP status codes are present.",
                    suitability_score=0.94,
                    aggregation_target="status_code_distribution",
                )
            )

        # 7. Response Time Latency Distribution (Histogram)
        if "response_time_ms" in fields_set and analytics.response_time_stats:
            recs.append(
                ChartRecommendation(
                    id="rec-latency-histogram",
                    chart_type="histogram",
                    title="Response Latency Distribution (ms)",
                    analytical_question="Are request latencies normally distributed, or is there a severe p95/p99 tail latency?",
                    required_fields=["response_time_ms"],
                    reason="Histogram distribution reveals multimodal latencies, timeouts, and cache miss penalties.",
                    expected_insight="Verify SLA compliance and detect backend blocking or thread pool starvation.",
                    limitations="Outlier requests (> 30s) can skew histogram buckets unless logarithmically bounded.",
                    suitability_score=0.92,
                    aggregation_target="response_time_stats",
                )
            )

        # 8. Activity Heatmap by Day & Hour (Heatmap)
        if "timestamp" in fields_set and len(analytics.heatmap) > 0:
            recs.append(
                ChartRecommendation(
                    id="rec-activity-heatmap",
                    chart_type="heatmap",
                    title="Error Activity Heatmap (Day of Week vs Hour)",
                    analytical_question="Do error patterns cluster around specific hours of the day or days of the week?",
                    required_fields=["timestamp", "level"],
                    reason="2D density matrix exposes cyclical operational stress, cron job failures, or peak user traffic patterns.",
                    expected_insight="Discover unattended nightly batch failure patterns or peak business hour strain.",
                    limitations="Needs sufficient temporal breadth (multi-day logs) to render meaningful heat distributions.",
                    suitability_score=0.87,
                    aggregation_target="heatmap",
                )
            )

        # Sort recommendations by suitability score descending
        recs.sort(key=lambda r: r.suitability_score, reverse=True)
        return recs

    def _call_openai_recommendations(
        self, available_fields: List[str], analytics: LogAnalytics, format_name: str
    ) -> List[ChartRecommendation]:
        # Compact summary sent to AI (no raw sensitive entries!)
        prompt_data = {
            "format": format_name,
            "available_fields": available_fields,
            "total_lines": analytics.total_lines,
            "error_count": analytics.error_count,
            "warning_count": analytics.warning_count,
            "info_count": analytics.info_count,
            "distinct_services": analytics.distinct_services_count,
            "has_status_codes": bool(analytics.status_code_distribution),
            "has_response_times": analytics.response_time_stats is not None,
            "has_timestamps": "timestamp" in available_fields,
        }

        system_prompt = (
            "You are an expert Data Visualization Engineer specializing in operational log analytics.\n"
            "Given available log metadata, recommend 4 to 8 distinct, actionable visualization charts.\n"
            "CRITICAL CONSTRAINTS:\n"
            "1. ONLY recommend chart_type from: ['line', 'stacked_bar', 'bar', 'pie', 'donut', 'histogram', 'heatmap'].\n"
            "2. required_fields MUST ONLY contain fields present in available_fields.\n"
            "3. DO NOT fabricate data or log counts; you only recommend metadata and analytical questions.\n"
            "4. Return strict JSON matching the schema: {'recommendations': [{"
            " 'id': str, 'chart_type': str, 'title': str, 'analytical_question': str, 'required_fields': [str],"
            " 'reason': str, 'expected_insight': str, 'limitations': str, 'suitability_score': float, 'aggregation_target': str}]}"
        )

        user_prompt = f"Analyze log dataset metadata and recommend appropriate visualizations:\n{json.dumps(prompt_data, indent=2)}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        with httpx.Client(timeout=12.0) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
            if resp.status_code != 200:
                return []
            content = resp.json()["choices"][0]["message"]["content"]
            parsed_json = json.loads(content)

        # Allowlist validation
        valid_recs: List[ChartRecommendation] = []
        raw_list = parsed_json.get("recommendations", [])
        avail_set = set(available_fields)

        for item in raw_list:
            c_type = item.get("chart_type")
            req_fields = item.get("required_fields", [])
            # Validate chart type
            if c_type not in ALLOWED_CHART_TYPES:
                continue
            # Validate required fields against available fields
            if not all(f in avail_set for f in req_fields):
                continue

            score = float(item.get("suitability_score", 0.8))
            score = max(0.1, min(1.0, score))

            valid_recs.append(
                ChartRecommendation(
                    id=str(item.get("id") or f"ai-rec-{len(valid_recs)}"),
                    chart_type=c_type,
                    title=str(item.get("title", "Log Analysis Chart")),
                    analytical_question=str(item.get("analytical_question", "How does this metric behave?")),
                    required_fields=req_fields,
                    reason=str(item.get("reason", "Provides insights into log distribution.")),
                    expected_insight=str(item.get("expected_insight", "Identify anomalies and trends.")),
                    limitations=str(item.get("limitations", "Bounded by available fields.")),
                    suitability_score=round(score, 2),
                    aggregation_target=str(item.get("aggregation_target", "time_series")),
                    time_interval="auto",
                )
            )

        valid_recs.sort(key=lambda r: r.suitability_score, reverse=True)
        return valid_recs if valid_recs else self._rule_based_recommendations(available_fields, analytics)


ai_recommender = AiRecommenderService()

