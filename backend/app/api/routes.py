import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse, HTMLResponse

from app.config import UPLOAD_DIR, SAMPLES_DIR, MAX_FILE_SIZE_BYTES
from app.models.schemas import (
    DataQualityReport,
    DatasetProfile,
    LogAnalytics,
    ChartRecommendation,
    RecommendationEvaluation,
    EvaluationSummary,
    InvestigateRequest,
    InvestigateResponse,
    PaginatedEntries,
    LogEntry,
)
from app.parsers.registry import parser_registry
from app.services.storage import storage_service
from app.services.analytics import analytics_engine
from app.services.ai_recommender import ai_recommender
from app.services.investigator import investigator_service
from app.services.exporter import exporter_service

router = APIRouter(prefix="/api")


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "registered_parsers": [p["id"] for p in parser_registry.list_all()],
    }


@router.get("/logs/formats")
def get_supported_formats():
    return {"formats": parser_registry.list_all()}


@router.get("/logs/samples")
def list_samples():
    sample_files = []
    if SAMPLES_DIR.exists():
        for f in SAMPLES_DIR.iterdir():
            if f.is_file():
                sample_files.append({
                    "name": f.name,
                    "size_bytes": f.stat().st_size,
                    "description": {
                        "application.log": "Timestamped Microservices App Log (with error bursts & malformed lines)",
                        "python_app.log": "Python App Log with Multiline Exception Tracebacks",
                        "web_access.log": "Nginx / Apache HTTP Access Log (latency, status codes, IPs)",
                        "service_events.jsonl": "JSON Lines Structured Event Stream",
                        "system_audit.csv": "CSV System Audit Log (with custom column mappings)",
                    }.get(f.name, "Synthetic sample log file"),
                })
    return {"samples": sample_files}


@router.post("/logs/upload")
async def upload_log_file(file: UploadFile = File(...)):
    # Validate extension
    filename = file.filename or "unknown.log"
    valid_exts = [".log", ".txt", ".csv", ".json", ".jsonl"]
    if not any(filename.lower().endswith(ext) for ext in valid_exts):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension. Allowed extensions: {', '.join(valid_exts)}"
        )

    # Save to uploads dir
    dest_path = UPLOAD_DIR / f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    file_bytes = await file.read()
    
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB")

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    # Read preview lines
    try:
        content_text = file_bytes.decode("utf-8", errors="replace")
    except Exception:
        content_text = file_bytes.decode("latin-1", errors="replace")

    raw_lines = content_text.splitlines()
    preview_lines = raw_lines[:25]

    # Detect format
    best_format, confidence, candidates = parser_registry.detect_format(preview_lines)

    # Create dataset session
    session = storage_service.create_dataset(
        filename=filename,
        file_path=str(dest_path),
        file_size=len(file_bytes),
        detected_format=best_format,
    )
    session.raw_lines = raw_lines

    return {
        "dataset_id": session.dataset_id,
        "filename": filename,
        "file_size_bytes": len(file_bytes),
        "total_lines": len(raw_lines),
        "detected_format": best_format,
        "detection_confidence": confidence,
        "candidates": candidates,
        "preview_lines": preview_lines,
    }


@router.post("/logs/sample/{sample_name}")
def load_sample_log(sample_name: str):
    sample_path = SAMPLES_DIR / sample_name
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample '{sample_name}' not found.")

    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    content_text = file_bytes.decode("utf-8", errors="replace")
    raw_lines = content_text.splitlines()
    preview_lines = raw_lines[:25]

    best_format, confidence, candidates = parser_registry.detect_format(preview_lines)

    session = storage_service.create_dataset(
        filename=f"[Synthetic] {sample_name}",
        file_path=str(sample_path),
        file_size=len(file_bytes),
        detected_format=best_format,
    )
    session.raw_lines = raw_lines

    return {
        "dataset_id": session.dataset_id,
        "filename": session.filename,
        "file_size_bytes": len(file_bytes),
        "total_lines": len(raw_lines),
        "detected_format": best_format,
        "detection_confidence": confidence,
        "candidates": candidates,
        "preview_lines": preview_lines,
    }


@router.post("/logs/{dataset_id}/parse")
def parse_dataset(
    dataset_id: str,
    format_name: Optional[str] = Query(None),
    options: Optional[Dict[str, Any]] = None,
):
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found or session expired.")

    chosen_format = format_name or session.detected_format
    parser = parser_registry.get(chosen_format)
    if not parser:
        raise HTTPException(status_code=400, detail=f"Parser format '{chosen_format}' is not registered.")

    session.detected_format = chosen_format

    # Parse lines
    parsed, malformed = parser.parse_lines(session.raw_lines, options=options)
    session.parsed_entries = parsed
    session.malformed_entries = malformed

    total_lines = len(session.raw_lines)
    success_rate = round(len(parsed) / total_lines * 100.0, 2) if total_lines > 0 else 0.0

    # Field presence stats
    field_counts: Dict[str, int] = {}
    for entry in parsed:
        if entry.timestamp:
            field_counts["timestamp"] = field_counts.get("timestamp", 0) + 1
        if entry.level:
            field_counts["level"] = field_counts.get("level", 0) + 1
        if entry.service:
            field_counts["service"] = field_counts.get("service", 0) + 1
        if entry.message:
            field_counts["message"] = field_counts.get("message", 0) + 1
        if entry.source_ip:
            field_counts["source_ip"] = field_counts.get("source_ip", 0) + 1
        if entry.http_method:
            field_counts["http_method"] = field_counts.get("http_method", 0) + 1
        if entry.request_path:
            field_counts["request_path"] = field_counts.get("request_path", 0) + 1
        if entry.status_code is not None:
            field_counts["status_code"] = field_counts.get("status_code", 0) + 1
        if entry.response_time_ms is not None:
            field_counts["response_time_ms"] = field_counts.get("response_time_ms", 0) + 1

    dq = DataQualityReport(
        total_lines=total_lines,
        parsed_lines=len(parsed),
        unparsed_lines=len(malformed),
        success_rate=success_rate,
        field_presence=field_counts,
        detected_format=chosen_format,
        sample_failures=malformed[:10],
    )
    session.data_quality = dq

    return {
        "status": "success",
        "dataset_id": dataset_id,
        "format": chosen_format,
        "data_quality": dq,
        "available_fields": session.get_available_fields(),
    }


@router.get("/logs/{dataset_id}/profile", response_model=DatasetProfile)
def get_dataset_profile(dataset_id: str):
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return session.get_profile()


@router.get("/logs/{dataset_id}/entries", response_model=PaginatedEntries)
def get_entries(
    dataset_id: str,
    search: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    parse_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: str = Query("line_number"),
    sort_dir: str = Query("asc"),
):
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    entries = session.parsed_entries if parse_status != "malformed" else session.malformed_entries
    if parse_status == "all":
        entries = session.parsed_entries + session.malformed_entries

    filtered = entries

    # Filter by search
    if search:
        s_lower = search.lower()
        filtered = [
            e for e in filtered
            if (e.message and s_lower in e.message.lower()) or (s_lower in e.raw_line.lower())
        ]

    # Filter by level
    if level and level.upper() != "ALL":
        lvl_u = level.upper()
        filtered = [e for e in filtered if e.level and e.level.upper() == lvl_u]

    # Filter by service
    if service and service != "ALL":
        filtered = [e for e in filtered if e.service == service]

    # Filter by status code
    if status_code is not None:
        filtered = [e for e in filtered if e.status_code == status_code]

    # Sort
    reverse = (sort_dir.lower() == "desc")
    if sort_by == "timestamp":
        filtered.sort(key=lambda x: x.timestamp or "", reverse=reverse)
    elif sort_by == "response_time_ms":
        filtered.sort(key=lambda x: x.response_time_ms or -1.0, reverse=reverse)
    elif sort_by == "level":
        filtered.sort(key=lambda x: x.level or "", reverse=reverse)
    else:
        filtered.sort(key=lambda x: x.line_number, reverse=reverse)

    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start_idx = (page - 1) * page_size
    paged = filtered[start_idx : start_idx + page_size]

    return PaginatedEntries(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        entries=paged,
    )


@router.get("/logs/{dataset_id}/malformed")
def get_malformed_entries(dataset_id: str):
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return {
        "dataset_id": dataset_id,
        "total_malformed": len(session.malformed_entries),
        "malformed_entries": session.malformed_entries,
    }


@router.get("/logs/{dataset_id}/analytics", response_model=LogAnalytics)
def get_analytics(dataset_id: str):
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    analytics = analytics_engine.compute_analytics(
        session.parsed_entries,
        total_lines=len(session.raw_lines),
        malformed_count=len(session.malformed_entries),
    )
    return analytics


@router.post("/logs/{dataset_id}/recommendations", response_model=List[ChartRecommendation])
def get_recommendations(dataset_id: str):
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    analytics = analytics_engine.compute_analytics(
        session.parsed_entries,
        total_lines=len(session.raw_lines),
        malformed_count=len(session.malformed_entries),
    )
    available_fields = session.get_available_fields()

    recs = ai_recommender.generate_recommendations(
        available_fields=available_fields,
        analytics=analytics,
        format_name=session.detected_format,
    )
    session.recommendations = recs
    return recs


@router.post("/logs/{dataset_id}/visualizations")
def get_visualization_data(
    dataset_id: str,
    chart_id: Optional[str] = None,
    chart_type: Optional[str] = None,
    time_interval: Optional[str] = None,
    filter_service: Optional[str] = None,
    filter_level: Optional[str] = None,
):
    """
    Returns actual chart data aggregated deterministically from the parsed logs.
    Never lets AI invent chart counts!
    """
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    # Filter entries if filters requested
    entries = session.parsed_entries
    if filter_service and filter_service != "ALL":
        entries = [e for e in entries if e.service == filter_service]
    if filter_level and filter_level != "ALL":
        entries = [e for e in entries if e.level and e.level.upper() == filter_level.upper()]

    analytics = analytics_engine.compute_analytics(
        entries,
        total_lines=len(session.raw_lines),
        malformed_count=len(session.malformed_entries),
    )

    return {
        "dataset_id": dataset_id,
        "time_series": analytics.time_series,
        "service_stats": analytics.service_stats,
        "top_errors": analytics.top_errors,
        "status_code_distribution": analytics.status_code_distribution,
        "response_time_stats": analytics.response_time_stats,
        "heatmap": analytics.heatmap,
        "severity_distribution": {
            "ERROR": analytics.error_count,
            "CRITICAL": analytics.critical_count,
            "WARNING": analytics.warning_count,
            "INFO": analytics.info_count,
            "DEBUG": analytics.debug_count,
        },
    }


@router.post("/logs/{dataset_id}/investigate", response_model=InvestigateResponse)
def investigate_logs(dataset_id: str, request: InvestigateRequest):
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    analytics = analytics_engine.compute_analytics(
        session.parsed_entries,
        total_lines=len(session.raw_lines),
        malformed_count=len(session.malformed_entries),
    )

    return investigator_service.investigate(request, session.parsed_entries, analytics)


@router.post("/logs/{dataset_id}/evaluations")
def record_evaluation(
    dataset_id: str,
    evaluation: RecommendationEvaluation,
):
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    session.evaluations[evaluation.recommendation_id] = evaluation
    return session.get_evaluation_summary()


@router.get("/logs/{dataset_id}/evaluations", response_model=EvaluationSummary)
def get_evaluations(dataset_id: str):
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return session.get_evaluation_summary()


@router.get("/logs/{dataset_id}/export")
def export_dataset(
    dataset_id: str,
    format: str = Query("csv", pattern="^(csv|json|unparsed|html)$"),
):
    session = storage_service.get(dataset_id)
    if not session:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    if format == "csv":
        csv_data = exporter_service.export_csv(session.parsed_entries)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={session.filename}_parsed.csv"}
        )
    elif format == "json":
        json_data = exporter_service.export_json(session.parsed_entries)
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={session.filename}_parsed.json"}
        )
    elif format == "unparsed":
        txt_data = exporter_service.export_unparsed_txt(session.malformed_entries)
        return Response(
            content=txt_data,
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={session.filename}_unparsed.txt"}
        )
    elif format == "html":
        analytics = analytics_engine.compute_analytics(
            session.parsed_entries,
            total_lines=len(session.raw_lines),
            malformed_count=len(session.malformed_entries),
        )
        html_report = exporter_service.generate_html_report(
            session.filename,
            session.detected_format,
            analytics,
            session.get_evaluation_summary(),
        )
        return HTMLResponse(content=html_report)
