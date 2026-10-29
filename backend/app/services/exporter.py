import csv
import io
import json
from typing import List, Dict, Any
from app.models.schemas import LogEntry, LogAnalytics, EvaluationSummary


class ExporterService:
    def export_csv(self, entries: List[LogEntry]) -> str:
        output = io.StringIO()
        fieldnames = [
            "id",
            "line_number",
            "timestamp",
            "level",
            "service",
            "message",
            "source_ip",
            "http_method",
            "request_path",
            "status_code",
            "response_time_ms",
            "parse_status",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for e in entries:
            writer.writerow({
                "id": e.id,
                "line_number": e.line_number,
                "timestamp": e.timestamp or "",
                "level": e.level or "",
                "service": e.service or "",
                "message": e.message or "",
                "source_ip": e.source_ip or "",
                "http_method": e.http_method or "",
                "request_path": e.request_path or "",
                "status_code": e.status_code if e.status_code is not None else "",
                "response_time_ms": e.response_time_ms if e.response_time_ms is not None else "",
                "parse_status": e.parse_status,
            })

        return output.getvalue()

    def export_json(self, entries: List[LogEntry]) -> str:
        return json.dumps([e.model_dump() for e in entries], indent=2)

    def export_unparsed_txt(self, malformed_entries: List[LogEntry]) -> str:
        output = io.StringIO()
        for e in malformed_entries:
            output.write(f"Line {e.line_number}: {e.raw_line}\n")
            if e.error_details:
                output.write(f"  Reason: {e.error_details}\n")
        return output.getvalue()

    def generate_html_report(
        self,
        filename: str,
        detected_format: str,
        analytics: LogAnalytics,
        eval_summary: EvaluationSummary,
    ) -> str:
        """Generates a clean, printable HTML report suitable for printing to PDF or offline archival."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Log Analysis Report - {filename}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #1e293b; background: #fff; line-height: 1.5; }}
    h1, h2, h3 {{ color: #0f172a; margin-top: 24px; }}
    .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
    .kpi-card {{ border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; background: #f8fafc; }}
    .kpi-title {{ font-size: 12px; font-weight: 600; text-transform: uppercase; color: #64748b; }}
    .kpi-value {{ font-size: 24px; font-weight: 700; color: #0f172a; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; margin-bottom: 24px; }}
    th, td {{ border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; font-size: 13px; }}
    th {{ background: #f1f5f9; font-weight: 600; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
    .badge-error {{ background: #fee2e2; color: #b91c1c; }}
    .badge-warn {{ background: #fef3c7; color: #b45309; }}
    .badge-info {{ background: #e0f2fe; color: #0369a1; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Log File Parser &amp; AI-Assisted Visualization Report</h1>
    <p><strong>File:</strong> {filename} | <strong>Format:</strong> {detected_format} | <strong>Generated:</strong> {analytics.time_range.get('start', 'N/A') if analytics.time_range else 'N/A'}</p>
  </div>

  <h2>1. Data Quality &amp; Parser Performance</h2>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-title">Total Lines</div><div class="kpi-value">{analytics.total_lines}</div></div>
    <div class="kpi-card"><div class="kpi-title">Successfully Parsed</div><div class="kpi-value">{analytics.parsed_lines}</div></div>
    <div class="kpi-card"><div class="kpi-title">Unparsed Lines</div><div class="kpi-value">{analytics.unparsed_lines}</div></div>
    <div class="kpi-card"><div class="kpi-title">Success Rate</div><div class="kpi-value">{analytics.success_rate}%</div></div>
  </div>

  <h2>2. Operational Health &amp; Severities</h2>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-title">Errors</div><div class="kpi-value" style="color: #b91c1c;">{analytics.error_count}</div></div>
    <div class="kpi-card"><div class="kpi-title">Warnings</div><div class="kpi-value" style="color: #b45309;">{analytics.warning_count}</div></div>
    <div class="kpi-card"><div class="kpi-title">Info Logs</div><div class="kpi-value">{analytics.info_count}</div></div>
    <div class="kpi-card"><div class="kpi-title">Active Services</div><div class="kpi-value">{analytics.distinct_services_count}</div></div>
  </div>

  <h2>3. Top Recurring Errors</h2>
  <table>
    <thead><tr><th>Error Signature</th><th>Occurrences</th><th>% of Errors</th><th>Affected Services</th></tr></thead>
    <tbody>
      {"".join(f"<tr><td><code>{err.message}</code></td><td>{err.count}</td><td>{err.percentage}%</td><td>{', '.join(err.services)}</td></tr>" for err in analytics.top_errors[:8]) or "<tr><td colspan='4'>No errors recorded</td></tr>"}
    </tbody>
  </table>

  <h2>4. Service Breakdown</h2>
  <table>
    <thead><tr><th>Service</th><th>Total Entries</th><th>Errors</th><th>Warnings</th><th>Failure Rate</th></tr></thead>
    <tbody>
      {"".join(f"<tr><td>{s.service}</td><td>{s.total_entries}</td><td>{s.error_count}</td><td>{s.warning_count}</td><td>{s.error_rate}%</td></tr>" for s in analytics.service_stats[:8]) or "<tr><td colspan='5'>No service data available</td></tr>"}
    </tbody>
  </table>

  <h2>5. AI Recommendation Evaluation Summary</h2>
  <div class="kpi-grid">
    <div class="kpi-card"><div class="kpi-title">Total Recommendations</div><div class="kpi-value">{eval_summary.total_recommendations}</div></div>
    <div class="kpi-card"><div class="kpi-title">Accepted</div><div class="kpi-value" style="color: #15803d;">{eval_summary.accepted_count}</div></div>
    <div class="kpi-card"><div class="kpi-title">Rejected</div><div class="kpi-value" style="color: #b91c1c;">{eval_summary.rejected_count}</div></div>
    <div class="kpi-card"><div class="kpi-title">Acceptance Rate</div><div class="kpi-value">{eval_summary.acceptance_rate}%</div></div>
  </div>
</body>
</html>
"""
        return html


exporter_service = ExporterService()

