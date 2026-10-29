import pytest
from app.parsers.app_log import AppLogParser
from app.parsers.python_log import PythonLogParser
from app.parsers.access_log import AccessLogParser
from app.parsers.json_log import JsonLogParser
from app.parsers.csv_log import CsvLogParser
from app.parsers.base import normalize_level, parse_timestamp_iso
from app.parsers.registry import parser_registry


def test_level_normalization():
    assert normalize_level("WARN") == "WARNING"
    assert normalize_level("warning") == "WARNING"
    assert normalize_level("ERR") == "ERROR"
    assert normalize_level("[ERROR]") == "ERROR"
    assert normalize_level("CRIT") == "CRITICAL"
    assert normalize_level("FATAL") == "CRITICAL"
    assert normalize_level("INFO") == "INFO"
    assert normalize_level("DBG") == "DEBUG"
    assert normalize_level(None) is None


def test_timestamp_parsing():
    assert parse_timestamp_iso("2026-10-28 10:15:22") == "2026-10-28T10:15:22"
    assert parse_timestamp_iso("2026-10-28 10:15:22,100").startswith("2026-10-28T10:15:22")
    # Apache format
    clf_ts = parse_timestamp_iso("28/Oct/2026:10:15:22 +0000")
    assert clf_ts is not None and "2026-10-28" in clf_ts
    assert parse_timestamp_iso("invalid-timestamp-string") is None


def test_app_log_parser():
    parser = AppLogParser()
    lines = [
        "2026-10-28 10:15:22 INFO [auth-service] User login successful status: 200 latency: 45ms",
        "2026-10-28 10:15:24 WARNING [payment-service] Payment processing delayed took 320ms",
        "2026-10-28 10:15:27 ERROR [database-service] Connection timeout 504",
        "INVALID GARBAGE ENTRY WITHOUT TIMESTAMP",
    ]
    parsed, malformed = parser.parse_lines(lines)

    assert len(parsed) == 3
    assert len(malformed) == 1

    assert parsed[0].level == "INFO"
    assert parsed[0].service == "auth-service"
    assert parsed[0].status_code == 200
    assert parsed[0].response_time_ms == 45.0

    assert parsed[1].level == "WARNING"
    assert parsed[1].service == "payment-service"
    assert parsed[1].response_time_ms == 320.0

    assert parsed[2].level == "ERROR"
    assert parsed[2].service == "database-service"
    assert parsed[2].status_code == 504

    assert malformed[0].parse_status == "malformed"
    assert "INVALID GARBAGE" in malformed[0].raw_line


def test_python_log_parser_multiline_stack_traces():
    parser = PythonLogParser()
    lines = [
        "2026-10-28 10:15:22,100 - auth - INFO - User authenticated",
        "2026-10-28 10:15:24,300 - api - ERROR - Request processing failed",
        "Traceback (most recent call last):",
        '  File "server.py", line 42, in handle_request',
        "    raise ValueError('Corrupt token')",
        "ValueError: Corrupt token",
        "2026-10-28 10:15:26,500 - worker - INFO - Completed background job",
    ]
    parsed, malformed = parser.parse_lines(lines)

    assert len(parsed) == 3
    assert len(malformed) == 0

    # Verify multiline traceback grouping on entry 2
    err_entry = parsed[1]
    assert err_entry.level == "ERROR"
    assert err_entry.service == "api"
    assert "Traceback" in err_entry.message
    assert "ValueError: Corrupt token" in err_entry.message
    assert "server.py" in err_entry.raw_line


def test_access_log_parser():
    parser = AccessLogParser()
    lines = [
        '192.168.1.50 - - [28/Oct/2026:10:15:22 +0000] "GET /api/v1/orders HTTP/1.1" 200 1450 "-" "Mozilla/5.0" 0.045',
        '192.168.1.51 - - [28/Oct/2026:10:15:23 +0000] "POST /checkout HTTP/1.1" 500 512 "-" "Mozilla/5.0" 1.250',
        '192.168.1.52 - - [28/Oct/2026:10:15:24 +0000] "GET /not-found HTTP/1.1" 404 120 "-" "Mozilla/5.0"',
        "CORRUPT ACCESS LINE",
    ]
    parsed, malformed = parser.parse_lines(lines)

    assert len(parsed) == 3
    assert len(malformed) == 1

    assert parsed[0].source_ip == "192.168.1.50"
    assert parsed[0].http_method == "GET"
    assert parsed[0].request_path == "/api/v1/orders"
    assert parsed[0].status_code == 200
    assert parsed[0].response_time_ms == 45.0  # converted 0.045s -> 45ms
    assert parsed[0].level == "INFO"

    assert parsed[1].status_code == 500
    assert parsed[1].level == "ERROR"

    assert parsed[2].status_code == 404
    assert parsed[2].level == "WARNING"


def test_json_log_parser():
    parser = JsonLogParser()
    lines = [
        '{"timestamp": "2026-10-28T10:15:22Z", "level": "INFO", "service": "indexer", "message": "Indexed 50 items", "status_code": 200, "duration_ms": 78}',
        '{"time": "2026-10-28T10:15:25Z", "severity": "WARN", "app": "gateway", "msg": "Slow upstream call", "status": 429, "latency": 1500}',
        '{"corrupted_json_string',
    ]
    parsed, malformed = parser.parse_lines(lines)

    assert len(parsed) == 2
    assert len(malformed) == 1

    assert parsed[0].level == "INFO"
    assert parsed[0].service == "indexer"
    assert parsed[0].response_time_ms == 78.0

    assert parsed[1].level == "WARNING"
    assert parsed[1].service == "gateway"
    assert parsed[1].status_code == 429


def test_csv_log_parser():
    parser = CsvLogParser()
    lines = [
        "timestamp,severity,service,message,status_code,latency_ms",
        "2026-10-28 10:15:22,INFO,billing,Invoice generated,200,42.5",
        "2026-10-28 10:15:25,ERROR,billing,Payment card declined,402,120.0",
        "SHORT,ROW",
    ]
    parsed, malformed = parser.parse_lines(lines)

    assert len(parsed) == 2
    assert len(malformed) == 1
    assert parsed[0].level == "INFO"
    assert parsed[0].service == "billing"
    assert parsed[0].response_time_ms == 42.5
    assert parsed[1].level == "ERROR"
    assert parsed[1].status_code == 402


def test_registry_detection():
    sample_app = [
        "2026-10-28 10:15:22 INFO [auth-service] User login successful",
        "2026-10-28 10:15:24 WARNING [payment-service] Payment processing delayed",
    ]
    fmt, conf, candidates = parser_registry.detect_format(sample_app)
    assert fmt == "app_log"
    assert conf > 0.8

