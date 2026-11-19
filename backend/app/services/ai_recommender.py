from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError

from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.models.schemas import ChartRecommendation, LogAnalytics
from app.services.gemini import generate_json, logger

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


class GeminiChartSuggestion(BaseModel):
    id: str
    title: str = Field(min_length=1)
    analytical_question: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    expected_insight: str = Field(min_length=1)
    limitations: str = Field(min_length=1)
    suitability_score: float = Field(ge=0.0, le=1.0)


class GeminiChartSuggestions(BaseModel):
    recommendations: List[GeminiChartSuggestion] = Field(max_length=8)


class AiRecommenderService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = GEMINI_API_KEY if api_key is None else api_key.strip()
        self.model = model or GEMINI_MODEL

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
        local_recs = self._rule_based_recommendations(available_fields, analytics)
        if self.api_key and local_recs:
            ai_recs = self._call_gemini_recommendations(available_fields, analytics, format_name, local_recs)
            if ai_recs:
                return ai_recs
        return local_recs

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
                    required_fields=["timestamp", "level"] if "level" in fields_set else ["timestamp"],
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
        if "level" in fields_set and analytics.parsed_lines > 0:
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
        if {"message", "level"} <= fields_set and analytics.top_errors:
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
        if {"timestamp", "level"} <= fields_set and analytics.heatmap:
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

    def _call_gemini_recommendations(
        self,
        available_fields: List[str],
        analytics: LogAnalytics,
        format_name: str,
        local_recs: List[ChartRecommendation],
    ) -> List[ChartRecommendation]:
        templates = {rec.id: rec for rec in local_recs}
        result = generate_json(
            self.api_key,
            self.model,
            feature="chart recommendations",
            system_prompt=(
                "Recommend the most relevant charts from the provided chart options. "
                "Select existing ids once each and write a title, question, rationale, expected insight, "
                "limitation and relevance score for each selected option. "
                "Ground each suggestion in the supplied dataset profile and never invent log counts."
            ),
            prompt_data={
                "format": format_name,
                "available_fields": sorted(ALLOWED_FIELDS.intersection(available_fields)),
                "total_lines": analytics.total_lines,
                "error_count": analytics.error_count,
                "warning_count": analytics.warning_count,
                "info_count": analytics.info_count,
                "distinct_services": analytics.distinct_services_count,
                "chart_options": [
                    rec.model_dump(include={"id", "title", "chart_type", "required_fields", "aggregation_target"})
                    for rec in local_recs
                ],
            },
            response_schema=GeminiChartSuggestions.model_json_schema(),
        )
        if result is None:
            return []
        try:
            suggestions = GeminiChartSuggestions.model_validate(result, strict=True).recommendations
        except ValidationError:
            logger.warning("Gemini chart recommendations returned invalid suggestions. Using local rules.")
            return []

        valid_recs = {}
        for suggestion in suggestions:
            if suggestion.id in templates and suggestion.id not in valid_recs:
                valid_recs[suggestion.id] = templates[suggestion.id].model_copy(
                    update={
                        **suggestion.model_dump(exclude={"id"}),
                        "suitability_score": round(suggestion.suitability_score, 2),
                        "source": "gemini",
                    },
                )

        if not valid_recs:
            logger.warning("Gemini returned no supported chart recommendations. Using local rules.")
        return sorted(valid_recs.values(), key=lambda rec: rec.suitability_score, reverse=True)


ai_recommender = AiRecommenderService()

