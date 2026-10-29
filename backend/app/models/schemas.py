from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    id: int
    timestamp: Optional[str] = None
    level: Optional[str] = None  # Normalized: DEBUG, INFO, WARNING, ERROR, CRITICAL
    service: Optional[str] = None
    message: Optional[str] = None
    source_ip: Optional[str] = None
    http_method: Optional[str] = None
    request_path: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    raw_line: str
    line_number: int
    parse_status: Literal["parsed", "malformed", "unparsed"] = "parsed"
    error_details: Optional[str] = None


class DataQualityReport(BaseModel):
    total_lines: int
    parsed_lines: int
    unparsed_lines: int
    success_rate: float
    field_presence: Dict[str, int]
    detected_format: str
    sample_failures: List[LogEntry] = []


class DatasetProfile(BaseModel):
    dataset_id: str
    filename: str
    file_size_bytes: int
    created_at: str
    format: str
    data_quality: DataQualityReport
    available_fields: List[str]


class TopErrorItem(BaseModel):
    message: str
    count: int
    percentage: float
    services: List[str]
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


class ServiceStatItem(BaseModel):
    service: str
    total_entries: int
    error_count: int
    warning_count: int
    info_count: int
    error_rate: float


class ResponseTimeStats(BaseModel):
    count: int
    avg_ms: float
    median_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float


class AnomalyItem(BaseModel):
    id: str
    type: Literal["error_spike", "activity_burst", "service_failure_rate"]
    title: str
    description: str
    timestamp_interval: Optional[str] = None
    severity: Literal["low", "medium", "high"] = "medium"
    metric_value: float
    baseline_value: float


class TimeVolumePoint(BaseModel):
    interval: str
    total: int
    error: int
    warning: int
    info: int
    debug: int


class HeatmapPoint(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    day_name: str
    hour: int         # 0-23
    error_count: int
    total_count: int


class LogAnalytics(BaseModel):
    total_lines: int
    parsed_lines: int
    unparsed_lines: int
    success_rate: float
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int
    critical_count: int
    distinct_services_count: int
    most_active_service: Optional[str] = None
    top_errors: List[TopErrorItem] = []
    service_stats: List[ServiceStatItem] = []
    status_code_distribution: Dict[str, int] = {}
    response_time_stats: Optional[ResponseTimeStats] = None
    time_series: List[TimeVolumePoint] = []
    anomalies: List[AnomalyItem] = []
    heatmap: List[HeatmapPoint] = []
    time_range: Optional[Dict[str, Optional[str]]] = None


class ChartRecommendation(BaseModel):
    id: str
    chart_type: Literal[
        "line", "stacked_bar", "bar", "pie", "donut", "histogram", "heatmap"
    ]
    title: str
    analytical_question: str
    required_fields: List[str]
    reason: str
    expected_insight: str
    limitations: str
    suitability_score: float  # 0.0 - 1.0
    aggregation_target: str
    time_interval: Optional[str] = "1h"  # 1m, 5m, 1h, 1d


class RecommendationEvaluation(BaseModel):
    recommendation_id: str
    chart_type: str
    status: Literal["accepted", "rejected", "modified"]
    user_reason: Optional[str] = None
    modified_chart_type: Optional[str] = None
    timestamp: str


class EvaluationSummary(BaseModel):
    total_recommendations: int
    accepted_count: int
    rejected_count: int
    modified_count: int
    acceptance_rate: float
    evaluations: List[RecommendationEvaluation] = []


class InvestigateRequest(BaseModel):
    query: str
    focus_service: Optional[str] = None
    focus_severity: Optional[str] = None


class InvestigateResponse(BaseModel):
    query: str
    evidence_found: bool
    factual_findings: List[str]
    hypotheses: List[str]
    recommended_checks: List[str]
    supporting_metrics: Dict[str, Any]


class LogFilterQuery(BaseModel):
    search: Optional[str] = None
    level: Optional[str] = None
    service: Optional[str] = None
    status_code: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    parse_status: Optional[str] = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "line_number"
    sort_dir: Literal["asc", "desc"] = "asc"


class PaginatedEntries(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    entries: List[LogEntry]

