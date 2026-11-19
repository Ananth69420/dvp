export interface LogEntry {
  id: number;
  timestamp: string | null;
  level: string | null;
  service: string | null;
  message: string | null;
  source_ip: string | null;
  http_method: string | null;
  request_path: string | null;
  status_code: number | null;
  response_time_ms: number | null;
  raw_line: string;
  line_number: number;
  parse_status: 'parsed' | 'malformed' | 'unparsed';
  error_details?: string | null;
}

export interface DataQualityReport {
  total_lines: number;
  parsed_lines: number;
  unparsed_lines: number;
  success_rate: number;
  field_presence: Record<string, number>;
  detected_format: string;
  sample_failures: LogEntry[];
}

export interface DatasetProfile {
  dataset_id: string;
  filename: string;
  file_size_bytes: number;
  created_at: string;
  format: string;
  data_quality: DataQualityReport;
  available_fields: string[];
}

export interface TopErrorItem {
  message: string;
  count: number;
  percentage: number;
  services: string[];
  first_seen?: string | null;
  last_seen?: string | null;
}

export interface ServiceStatItem {
  service: string;
  total_entries: number;
  error_count: number;
  warning_count: number;
  info_count: number;
  error_rate: number;
}

export interface ResponseTimeStats {
  count: number;
  avg_ms: number;
  median_ms: number;
  p90_ms: number;
  p95_ms: number;
  p99_ms: number;
  min_ms: number;
  max_ms: number;
}

export interface AnomalyItem {
  id: string;
  type: 'error_spike' | 'activity_burst' | 'service_failure_rate';
  title: string;
  description: string;
  timestamp_interval?: string | null;
  severity: 'low' | 'medium' | 'high';
  metric_value: number;
  baseline_value: number;
}

export interface TimeVolumePoint {
  interval: string;
  total: number;
  error: number;
  warning: number;
  info: number;
  debug: number;
}

export interface HeatmapPoint {
  day_of_week: number;
  day_name: string;
  hour: number;
  error_count: number;
  total_count: number;
}

export interface LogAnalytics {
  total_lines: number;
  parsed_lines: number;
  unparsed_lines: number;
  success_rate: number;
  error_count: number;
  warning_count: number;
  info_count: number;
  debug_count: number;
  critical_count: number;
  distinct_services_count: number;
  most_active_service: string | null;
  top_errors: TopErrorItem[];
  service_stats: ServiceStatItem[];
  status_code_distribution: Record<string, number>;
  response_time_stats: ResponseTimeStats | null;
  time_series: TimeVolumePoint[];
  anomalies: AnomalyItem[];
  heatmap: HeatmapPoint[];
  time_range?: { start: string | null; end: string | null } | null;
}

export interface ChartRecommendation {
  id: string;
  chart_type: 'line' | 'stacked_bar' | 'bar' | 'pie' | 'donut' | 'histogram' | 'heatmap';
  title: string;
  analytical_question: string;
  required_fields: string[];
  reason: string;
  expected_insight: string;
  limitations: string;
  suitability_score: number;
  aggregation_target: string;
  source?: 'gemini' | 'rules';
  time_interval?: string;
}

export interface RecommendationEvaluation {
  recommendation_id: string;
  chart_type: string;
  status: 'accepted' | 'rejected' | 'modified';
  user_reason?: string | null;
  modified_chart_type?: string | null;
  timestamp: string;
}

export interface EvaluationSummary {
  total_recommendations: number;
  accepted_count: number;
  rejected_count: number;
  modified_count: number;
  acceptance_rate: number;
  evaluations: RecommendationEvaluation[];
}

export interface InvestigateRequest {
  query: string;
  focus_service?: string | null;
  focus_severity?: string | null;
}

export interface InvestigateResponse {
  source?: 'gemini' | 'rules';
  query: string;
  evidence_found: boolean;
  factual_findings: string[];
  hypotheses: string[];
  recommended_checks: string[];
  supporting_metrics: Record<string, any>;
}

export interface PaginatedEntries {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  entries: LogEntry[];
}

export interface FormatCandidate {
  format_id: string;
  name: string;
  confidence: number;
}

export interface UploadResponse {
  dataset_id: string;
  filename: string;
  file_size_bytes: number;
  total_lines: number;
  detected_format: string;
  detection_confidence: number;
  candidates: FormatCandidate[];
  preview_lines: string[];
}

export interface SampleItem {
  name: string;
  size_bytes: number;
  description: string;
}

